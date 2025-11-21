from functools import wraps
from fastapi import APIRouter, Request, HTTPException
import os, httpx, re, logging, gc, psutil
import ujson as json
from datetime import datetime, time, timezone, timedelta
from pydantic import BaseModel
from typing import List, Optional
from states.global_state import influx_state, redis_state, os_spec
from concurrent.futures import ThreadPoolExecutor
import asyncio, math

EN_FILES = 'en50160_info.json'

# Path 객체 절대경로
from pathlib import Path

base_dir = Path(__file__).resolve().parent
SETTING_FOLDER = base_dir.parent.parent / "config"  # ⬅️ 두 단계 상위로

cpu_count = os.cpu_count() or 4
MAX_WORKERS = min(max(2, cpu_count), 8)  # 2~8 사이
executor: Optional[ThreadPoolExecutor] = None


def gc_after_large_data(threshold_mb=50):
    """대용량 데이터 처리 후 GC 실행하는 데코레이터"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            process = psutil.Process()

            # 실행 전 메모리
            before_memory = process.memory_info().rss / 1024 / 1024

            # 함수 실행
            result = await func(*args, **kwargs)

            # 실행 후 메모리
            after_memory = process.memory_info().rss / 1024 / 1024

            # 메모리 증가량이 임계값 초과시 GC
            if after_memory - before_memory > threshold_mb:
                gc.collect()
                logging.info(f"GC triggered after {func.__name__}: {after_memory - before_memory:.1f}MB freed")

            return result

        return wrapper

    return decorator


def get_or_create_executor() -> ThreadPoolExecutor:
    """Executor를 가져오거나 생성 (thread-safe)"""
    global executor
    if executor is None:
        executor = ThreadPoolExecutor(
            max_workers=MAX_WORKERS,
            thread_name_prefix="influx-"
        )
        logging.info(f"Created ThreadPoolExecutor with {MAX_WORKERS} workers")
    return executor


router = APIRouter()

ptInfo = ["3P4W", "3P3W(3)", "1P2W", "1P3W", "3P3W(2)"]

eventType = ["All", "SAG", "SWELL", "SHORT INTERRUPT", "LONG INTERRUPT", "OVER CURRENT", "UNDER CURRENT",
             "VOLTAGE TRANSIENT", "CURRENT TRANSIENT"]

api_timeout = httpx.Timeout(
    connect=2.0,  # 연결에는 5초
    read=20.0,  # 응답 읽기는 2초
    write=2.0,  # 요청 전송은 5초
    pool=5.0  # 연결 풀은 5초
)


def findNode(supers, name, path):  # check node level
    result = ''
    for i in range(0, len(supers)):
        if supers[i]["Name"] == name:
            if supers[i]["Path"] == path:
                break
            else:
                parts = [part.strip() for part in path.split("|")]
                result = "_".join(parts[1:])
                break
    return result


def checkNode(supers, name, path):  # check node level
    for i in range(0, len(supers)):
        if supers[i]["Name"] == name:
            if supers[i]["Path"] == path:
                return True
            else:
                return path
    return ''

@router.get("/getDiagnosisDetail/{asset}")
@gc_after_large_data(threshold_mb=30)  # Diagnosis Vue : get diagnosis
async def get_diagnosis(asset, request: Request):

   async with httpx.AsyncClient(timeout=api_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getDiagnostic?name={asset}")
        datas = response.json()
        # if response.status_code in [400, 401, 500]:
        #     flag = await checkLoginAPI(request)
        #     if not flag:
        #         return {"success": False, "error": "Restful API Login Failed"}
        #     else:
        #         response = await client.get(f"http://{os_spec.restip}:5000/api/getDiagnostic?name={asset}")
        #         datas = response.json()
   superNodes = []
   if len(datas) > 0:
       statuslist = datas["BarGraph"]
       for a in range(0, len(datas["BarGraph"])):
           superNodes.append(datas["BarGraph"][a]["NodeType"])
       superlist = []
       for a in range(0, len(datas["TreeList"])):
           if datas["TreeList"][a]["NodeType"] in superNodes:
               superdict = dict()
               superdict["ID"] = datas["TreeList"][a]["ID"]
               superdict["Name"] = datas["TreeList"][a]["Name"]
               superdict["Title"] = datas["TreeList"][a]["Title"]
               superdict["Titles"] = datas["TreeList"][a]["Titles"]
               superdict["AssemblyID"] = datas["TreeList"][a]["AssemblyID"]  # AssemblyID
               superdict["Description"] = datas["TreeList"][a]["Description"]
               superdict["Descriptions"] = datas["TreeList"][a]["Descriptions"]
               superdict["Path"] = datas["TreeList"][a]["Path"]
               superdict["Status"] = datas["TreeList"][a]["Status"]
               superdict["Value"] = datas["TreeList"][a]["Value"]
               superdict["isParent"] = True
               Titles = findNode(superlist, datas["TreeList"][a]["Name"], datas["TreeList"][a]["AssemblyID"])
               if Titles != "":
                   superdict["Title"] = superdict["Title"] + "_" + Titles
                   superlist.append(superdict)
               else:
                   superlist.append(superdict)
           else:
               continue
       for i in range(0, len(superlist)):
           for j in range(0, len(datas["TreeList"])):
               if superlist[i]["ID"] == datas["TreeList"][j]["ParentID"]:
                   subdict = dict()
                   subdict["ID"] = datas["TreeList"][j]["ID"]
                   subdict["Name"] = datas["TreeList"][j]["Name"]
                   subdict["Title"] = datas["TreeList"][j]["Title"]
                   subdict["Titles"] = datas["TreeList"][j]["Titles"]
                   subdict["AssemblyID"] = datas["TreeList"][j]["AssemblyID"]  # AssemblyID
                   subdict["Description"] = datas["TreeList"][j]["Description"]
                   subdict["Descriptions"] = datas["TreeList"][j]["Descriptions"]
                   subdict["Status"] = datas["TreeList"][j]["Status"]
                   subdict["Value"] = datas["TreeList"][j]["Value"]
                   subdict["NodeType"] = datas["TreeList"][j]["NodeType"]
                   if datas["TreeList"][j]["NodeType"] == 10:
                       subdict["isSub"] = True
                   else:
                       subdict["isSub"] = False
                   if "children" in superlist[i]:
                       superlist[i]["children"].append(subdict)
                   else:
                       superlist[i]["children"] = []
                       superlist[i]["children"].append(subdict)
                   if "children" in superlist[i]:
                       superlist[i]["children"].append(subdict)
                   else:
                       superlist[i]["children"] = []
                       superlist[i]["children"].append(subdict)
               else:
                   continue
       for i in range(0, len(superlist)):
           if "children" in superlist[i]:
               for k in range(0, len(superlist[i]["children"])):
                   if superlist[i]["children"][k]["isSub"]:
                       for j in range(0, len(datas["TreeList"])):
                           if datas["TreeList"][j]["NodeType"] == 11 and superlist[i]["children"][k]["ID"] == \
                                   datas["TreeList"][j]["ParentID"]:
                               subdict = dict()
                               subdict["ID"] = datas["TreeList"][j]["ID"]
                               subdict["Name"] = datas["TreeList"][j]["Name"]
                               subdict["Title"] = datas["TreeList"][j]["Title"]
                               subdict["Titles"] = datas["TreeList"][j]["Titles"]
                               subdict["AssemblyID"] = datas["TreeList"][j]["AssemblyID"]  # AssemblyID
                               subdict["Description"] = datas["TreeList"][j]["Description"]
                               subdict["Descriptions"] = datas["TreeList"][j]["Descriptions"]
                               subdict["Status"] = datas["TreeList"][j]["Status"]
                               subdict["Value"] = datas["TreeList"][j]["Value"]
                               if "children" in superlist[i]["children"][k]:
                                   superlist[i]["children"][k]["children"].append(subdict)
                               else:
                                   superlist[i]["children"][k]["children"] = []
                                   superlist[i]["children"][k]["children"].append(subdict)
                           else:
                               continue
                   else:
                       continue
           else:
               continue
   if len(superlist) > 0:
       return {"success": True, "data_status": statuslist, "data_tree": superlist}
   else:
       return {"success": False, "error": "No Data"}


@router.get("/getDiagPQ/{asset}")  # Diagnosis Vue : get diagnosis PQ
@gc_after_large_data(threshold_mb=30)
async def get_diagPQ(asset, request: Request):
    async with httpx.AsyncClient(timeout=api_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getPQ?name={asset}")
        datas = response.json()
    #     if response.status_code in [400, 401, 500]:
    #         flag = await checkLoginAPI(request)
    #         if not flag:
    #             return {"success": False, "error": "Restful API Login Failed"}
    #         else:
    #             response = await client.get(f"http://{os_spec.restip}:5000/api/getPQ?name={asset}")
    #             datas = response.json()
    superNodes = []
    if len(datas) > 0:
        statuslist = datas["BarGraph"]
        for a in range(0, len(datas["BarGraph"])):
            superNodes.append(datas["BarGraph"][a]["NodeType"])
        superlist = []
        for a in range(0, len(datas["TreeList"])):
            if datas["TreeList"][a]["NodeType"] in superNodes:
                superdict = dict()
                superdict["ID"] = datas["TreeList"][a]["ID"]
                superdict["Name"] = datas["TreeList"][a]["Name"]
                superdict["Title"] = datas["TreeList"][a]["Title"]
                superdict["Titles"] = datas["TreeList"][a]["Titles"]
                superdict["AssemblyID"] = datas["TreeList"][a]["AssemblyID"]  # AssemblyID
                superdict["Description"] = datas["TreeList"][a]["Description"]
                superdict["Descriptions"] = datas["TreeList"][a]["Descriptions"]
                superdict["Path"] = datas["TreeList"][a]["Path"]
                superdict["Status"] = datas["TreeList"][a]["Status"]
                superdict["Value"] = datas["TreeList"][a]["Value"]
                superdict["isParent"] = True
                superlist.append(superdict)
                Titles = checkNode(superlist, datas["TreeList"][a]["Name"], datas["TreeList"][a]["AssemblyID"])
                if Titles != "":
                    superdict["Title"] = superdict["Title"] + "_" + Titles
                    superlist.append(superdict)
                else:
                    superlist.append(superdict)
            else:
                continue
        for i in range(0, len(superlist)):
            for j in range(0, len(datas["TreeList"])):
                if superlist[i]["ID"] == datas["TreeList"][j]["ParentID"]:
                    subdict = dict()
                    subdict["ID"] = datas["TreeList"][j]["ID"]
                    subdict["Name"] = datas["TreeList"][j]["Name"]
                    subdict["Title"] = datas["TreeList"][j]["Title"]
                    subdict["Titles"] = datas["TreeList"][j]["Titles"]
                    subdict["AssemblyID"] = datas["TreeList"][j]["AssemblyID"]  # AssemblyID
                    subdict["Description"] = datas["TreeList"][j]["Description"]
                    subdict["Descriptions"] = datas["TreeList"][j]["Descriptions"]
                    subdict["Status"] = datas["TreeList"][j]["Status"]
                    subdict["Value"] = datas["TreeList"][j]["Value"]
                    subdict["NodeType"] = datas["TreeList"][j]["NodeType"]
                    if datas["TreeList"][j]["NodeType"] == 10:
                        subdict["isSub"] = True
                    else:
                        subdict["isSub"] = False
                    if "children" in superlist[i]:
                        superlist[i]["children"].append(subdict)
                    else:
                        superlist[i]["children"] = []
                        superlist[i]["children"].append(subdict)
                else:
                    continue
        for i in range(0, len(superlist)):
            if "children" in superlist[i]:
                for k in range(0, len(superlist[i]["children"])):
                    if superlist[i]["children"][k]["isSub"]:
                        for j in range(0, len(datas["TreeList"])):
                            if datas["TreeList"][j]["NodeType"] == 11 and superlist[i]["children"][k]["ID"] == \
                                    datas["TreeList"][j]["ParentID"]:
                                subdict = dict()
                                subdict["ID"] = datas["TreeList"][j]["ID"]
                                subdict["Name"] = datas["TreeList"][j]["Name"]
                                subdict["Title"] = datas["TreeList"][j]["Title"]
                                subdict["Titles"] = datas["TreeList"][j]["Titles"]
                                subdict["AssemblyID"] = datas["TreeList"][j]["AssemblyID"]  # AssemblyID
                                subdict["Description"] = datas["TreeList"][j]["Description"]
                                subdict["Descriptions"] = datas["TreeList"][j]["Descriptions"]
                                subdict["Status"] = datas["TreeList"][j]["Status"]
                                subdict["Value"] = datas["TreeList"][j]["Value"]
                                if "children" in superlist[i]["children"][k]:
                                    superlist[i]["children"][k]["children"].append(subdict)
                                else:
                                    superlist[i]["children"][k]["children"] = []
                                    superlist[i]["children"][k]["children"].append(subdict)
                            else:
                                continue
                    else:
                        continue
            else:
                continue

    if len(superlist) > 0:
        return {"success": True, "data_status": statuslist, "data_tree": superlist}
    else:
        return {"success": False, "error": "No Data"}


@router.get("/getFaults/{asset}")  # Diagnosis Vue : get diagnosis
async def get_faults(asset, request: Request):
    async with httpx.AsyncClient(timeout=api_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getFaults?name={asset}")
        datas = response.json()
    #     if response.status_code in [400, 401, 500]:
    #         flag = await checkLoginAPI(request)
    #         if not flag:
    #             return {"success": False, "error": "Restful API Login Failed"}
    #         else:
    #             response = await client.get(f"http://{os_spec.restip}:5000/api/getFaults?name={asset}")
    #             datas = response.json()
    superNodes = []
    if len(datas) > 0:
        statuslist = datas["BarGraph"]
        for a in range(0, len(datas["BarGraph"])):
            superNodes.append(datas["BarGraph"][a]["NodeType"])
        superlist = []
        for a in range(0, len(datas["TreeList"])):
            if datas["TreeList"][a]["NodeType"] in superNodes:
                superdict = dict()
                superdict["ID"] = datas["TreeList"][a]["ID"]
                superdict["Name"] = datas["TreeList"][a]["Name"]
                superdict["Title"] = datas["TreeList"][a]["Title"]
                superdict["Titles"] = datas["TreeList"][a]["Titles"]
                superdict["Description"] = datas["TreeList"][a]["Description"]
                superdict["Descriptions"] = datas["TreeList"][a]["Descriptions"]
                superdict["Path"] = datas["TreeList"][a]["Path"]
                superdict["Status"] = datas["TreeList"][a]["Status"]
                superdict["Value"] = datas["TreeList"][a]["Value"]
                superdict["isParent"] = True
                Titles = findNode(superlist, datas["TreeList"][a]["Name"], datas["TreeList"][a]["Path"])
                if Titles != "":
                    superdict["Title"] = superdict["Title"] + "_" + Titles
                    superlist.append(superdict)
                else:
                    superlist.append(superdict)
            else:
                continue
        for i in range(0, len(superlist)):
            for j in range(0, len(datas["TreeList"])):
                if superlist[i]["ID"] == datas["TreeList"][j]["ParentID"]:
                    subdict = dict()
                    subdict["ID"] = datas["TreeList"][j]["ID"]
                    subdict["Name"] = datas["TreeList"][j]["Name"]
                    subdict["Title"] = datas["TreeList"][j]["Title"]
                    subdict["Titles"] = datas["TreeList"][j]["Titles"]
                    subdict["Description"] = datas["TreeList"][j]["Description"]
                    subdict["Descriptions"] = datas["TreeList"][j]["Descriptions"]
                    subdict["Status"] = datas["TreeList"][j]["Status"]
                    subdict["Value"] = datas["TreeList"][j]["Value"]
                    if "children" in superlist[i]:
                        superlist[i]["children"].append(subdict)
                    else:
                        superlist[i]["children"] = []
                        superlist[i]["children"].append(subdict)
                else:
                    continue
    if len(superlist) > 0:
        return {"success": True, "data_status": statuslist, "data_tree": superlist}
    else:
        return {"success": False, "error": "No Data"}


@router.get("/getEvents/{asset}")  # Diagnosis Vue : get diagnosis
async def get_events(asset, request: Request):
    async with httpx.AsyncClient(timeout=api_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getEvents?name={asset}")
        datas = response.json()
        # if response.status_code in [400, 401, 500]:
        #     flag = await checkLoginAPI(request)
        #     if not flag:
        #         return {"success": False, "error": "Restful API Login Failed"}
        #     else:
        #         response = await client.get(f"http://{os_spec.restip}:5000/api/getEvents?name={asset}")
        #         datas = response.json()
    superNodes = []
    if len(datas) > 0:
        statuslist = datas["BarGraph"]
        for a in range(0, len(datas["BarGraph"])):
            superNodes.append(datas["BarGraph"][a]["NodeType"])
        superlist = []
        for a in range(0, len(datas["TreeList"])):
            if datas["TreeList"][a]["NodeType"] in superNodes:
                superdict = dict()
                superdict["ID"] = datas["TreeList"][a]["ID"]
                superdict["Name"] = datas["TreeList"][a]["Name"]
                superdict["Title"] = datas["TreeList"][a]["Title"]
                superdict["Titles"] = datas["TreeList"][a]["Titles"]
                superdict["Description"] = datas["TreeList"][a]["Description"]
                superdict["Path"] = datas["TreeList"][a]["Path"]
                superdict["Status"] = datas["TreeList"][a]["Status"]
                superdict["Value"] = datas["TreeList"][a]["Value"]
                superdict["isParent"] = True
                Titles = findNode(superlist, datas["TreeList"][a]["Name"], datas["TreeList"][a]["Path"])
                if Titles != "":
                    superdict["Title"] = superdict["Title"] + "_" + Titles
                    superlist.append(superdict)
                else:
                    superlist.append(superdict)
            else:
                continue
        for i in range(0, len(superlist)):
            for j in range(0, len(datas["TreeList"])):
                if superlist[i]["ID"] == datas["TreeList"][j]["ParentID"]:
                    subdict = dict()
                    subdict["ID"] = datas["TreeList"][j]["ID"]
                    subdict["Name"] = datas["TreeList"][j]["Name"]
                    subdict["Title"] = datas["TreeList"][j]["Title"]
                    subdict["Titles"] = datas["TreeList"][j]["Titles"]
                    subdict["Description"] = datas["TreeList"][j]["Description"]
                    subdict["Status"] = datas["TreeList"][j]["Status"]
                    subdict["Value"] = datas["TreeList"][j]["Value"]
                    if "children" in superlist[i]:
                        superlist[i]["children"].append(subdict)
                    else:
                        superlist[i]["children"] = []
                        superlist[i]["children"].append(subdict)
                else:
                    continue
    if len(superlist) > 0:
        return {"success": True, "data_status": statuslist, "data_tree": superlist}
    else:
        return {"success": False, "error": "No Data"}

# ===== 추가: 기본 조회 기간 제한이 있는 count 함수 =====
# def count_influx_records_with_limit_v2(measurement: str, channel: str,
#                                     page_size: int = 10, days_limit: int = 30):
#     """
#     필드 수를 확인하고 정확히 계산하는 방법
#     """
#     local_tz = get_local_timezone()
#     enddate_local = datetime.now(local_tz)
#     startdate_local = enddate_local - timedelta(days=days_limit)

#     start_ts = int(startdate_local.timestamp())
#     end_ts = int(enddate_local.timestamp())

#     # 1. 먼저 필드 수 확인
#     field_query = f'''
#     from(bucket: "ntek")
#       |> range(start: {start_ts}, stop: {end_ts})
#       |> filter(fn: (r) => r._measurement == "{measurement}")
#       |> filter(fn: (r) => r.channel == "{channel}")
#       |> limit(n: 1)
#       |> group()
#       |> keep(columns: ["_field"])
#     '''

#     try:
#         field_result = influx_state.query_api.query(field_query)
#         field_count = 0
#         fields_set = set()
#         for table in field_result:
#             for record in table.records:
#                 field = record.values.get('_field')
#                 if field:
#                     fields_set.add(field)
#         field_count = len(fields_set)

#         if field_count == 0:
#             field_count = 1  # 기본값

#         print(f"Found {field_count} fields: {fields_set}")

#         # 2. 전체 포인트 카운트
#         count_query = f'''
#         from(bucket: "ntek")
#           |> range(start: {start_ts}, stop: {end_ts})
#           |> filter(fn: (r) => r._measurement == "{measurement}")
#           |> filter(fn: (r) => r.channel == "{channel}")
#           |> count()
#         '''

#         count_result = influx_state.query_api.query(count_query)
#         total_points = 0
#         for table in count_result:
#             for record in table.records:
#                 val = record.get_value()
#                 if val:
#                     total_points = val
#                     break  # 첫 번째 값만 사용

#         # 3. 실제 레코드 수 = 전체 포인트 / 필드 수
#         total_records = total_points // field_count if field_count > 0 else 0
#         total_pages = (total_records + page_size - 1) // page_size if total_records > 0 else 0

#         return {
#             "total_records": total_records,
#             "total_pages": total_pages,
#             "page_size": page_size,
#             "days_included": days_limit,
#             "field_count": field_count
#         }

#     except Exception as e:
#         print(f"Count error: {e}")
#         return {
#             "total_records": 0,
#             "total_pages": 0,
#             "page_size": page_size,
#             "days_included": days_limit,
#             "error": str(e)
#         }


# def count_influx_records_with_limit(measurement: str, channel: str,
#                                     page_size: int = 10, days_limit: int = 30):
#     """
#     최근 N일로 제한된 카운트 (기본 조회용)
#     """
#     # 로컬 timezone 가져오기
#     local_tz = get_local_timezone()

#     # 로컬 시간 기준 날짜 계산 후 UTC 변환
#     end_dt = datetime.now(local_tz)
#     start_dt = end_dt - timedelta(days=days_limit)

#     startdate = start_dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
#     enddate = end_dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')

#     # 카운트 쿼리
#     query = f'''
#     from(bucket: "ntek")
#       |> range(start: time(v: "{startdate}"), stop: time(v: "{enddate}"))
#       |> filter(fn: (r) => r._measurement == "{measurement}")
#       |> filter(fn: (r) => r["channel"] == "{channel}")
#       |> group(columns: ["_measurement"])
#       |> count()
#     '''

#     result = influx_state.query_api.query(query)

#     total_records = 0
#     for table in result:
#         for record in table.records:
#             count_value = record.get_value()
#             if count_value > total_records:
#                 total_records = count_value

#     total_pages = (total_records + page_size - 1) // page_size

#     return {
#         "total_records": total_records,
#         "total_pages": total_pages,
#         "page_size": page_size,
#         "days_included": days_limit
#     }

# @router.get("/getTrendParameters/{asset}/{type}")  # Diagnosis Vue : get diagnosis PQ
# async def get_trendParams(asset, type, request: Request):
#     response = await  http_state.client.get(f"/getTrendHierarchy?name={asset}&type={type}")
#     datas = response.json()
#
#     if len(datas) > 0:
#         superlist = []
#         for a in range(0, len(datas)):
#             superdict = dict()
#             superdict["ID"] = datas[a]["ID"]
#             superdict["Name"] = datas[a]["Name"]
#             superdict["Title"] = datas[a]["Title"]
#             superdict["Titles"] = datas[a]["Titles"]
#             superdict["Path"] = datas[a]["Path"]
#             superdict["AssemblyID"] = datas[a]["AssemblyID"]
#             superdict["isParent"] = False
#             superdict["isSuper"] = True
#             Titles = findNode(superlist, datas[a]["Name"], datas[a]["Path"])
#             if Titles is True:
#                 continue
#             elif Titles != "":
#                 superdict["Title"] = superdict["Title"].rstrip() + "_" + Titles
#                 superlist.append(superdict)
#             else:
#                 superlist.append(superdict)
#         sublist = list()
#
#         for j in range(0, len(datas)):
#             isSuper = True
#             for i in range(0, len(superlist)):
#                 if superlist[i]["ID"] == datas[j]["ParentID"]:
#                     subdict = dict()
#                     subdict["ID"] = datas[j]["ID"]
#                     subdict["Name"] = datas[j]["Name"]
#                     subdict["Title"] = datas[j]["Title"]
#                     subdict["Titles"] = datas[j]["Titles"]
#                     if "children" in superlist[i]:
#                         superlist[i]["children"].append(subdict)
#                     else:
#                         superlist[i]["children"] = []
#                         superlist[i]["children"].append(subdict)
#                     isSuper = False
#                     sublist.append(datas[j]["ID"])
#
#             if isSuper and datas[j]["NodeType"] == 11:
#                 superdict = dict()
#                 superdict["ID"] = datas[j]["ID"]
#                 superdict["Name"] = datas[j]["Name"]
#                 superdict["Title"] = datas[j]["Title"]
#                 superdict["Titles"] = datas[j]["Titles"]
#                 superdict["Path"] = datas[j]["Path"]
#                 superdict["isParent"] = True
#                 Titles = findNode(superlist, datas[j]["Name"], datas[j]["Path"])
#
#                 if Titles is True:
#                     continue  # 완전 중복이면 추가하지 않음
#                 elif Titles != "":
#                     superdict["Title"] = superdict["Title"].rstrip() + "_" + Titles
#                 superlist.append(superdict)
#
#         superlist = [item for item in superlist if item["ID"] not in sublist]
#     if len(superlist) > 0:
#         return {"success": True, "superlist": superlist}
#     else:
#         return {"success": False, "error": "No Data"}

# def diagnose_paging_issue(measurement: str, channel: str, days_limit: int = 30):
#     """
#     페이징 카운트 문제 진단
#     """
#     # 1. 카운트 함수 실행
#     count_result = count_influx_records_with_limit(measurement, channel, 10, days_limit)
#     print(f"=== 카운트 함수 결과 ===")
#     print(f"Total Records: {count_result['total_records']}")
#     print(f"Total Pages: {count_result['total_pages']}")

#     # 2. 실제 첫 페이지 조회
#     first_page = query_influx_pages(measurement, channel, "time", 1, 10, days_limit)
#     print(f"\n=== 첫 페이지 실제 데이터 ===")
#     print(f"첫 페이지 레코드 수: {len(first_page)}")

#     # 3. 마지막 페이지까지 실제로 조회해보기
#     total_actual_records = 0
#     page = 1
#     max_pages = count_result['total_pages'] + 5  # 여유있게 확인

#     print(f"\n=== 페이지별 실제 데이터 확인 ===")
#     while page <= max_pages:
#         page_data = query_influx_pages(measurement, channel, "time", page, 10, days_limit)
#         if not page_data:
#             break
#         total_actual_records += len(page_data)
#         print(f"Page {page}: {len(page_data)} records")
#         if len(page_data) < 10:
#             break
#         page += 1

#     print(f"\n=== 결과 비교 ===")
#     print(f"카운트 함수: {count_result['total_records']} records, {count_result['total_pages']} pages")
#     print(f"실제 데이터: {total_actual_records} records, {page} pages")
#     print(f"일치 여부: {'✅ 일치' if count_result['total_records'] == total_actual_records else '❌ 불일치'}")

#     return {
#         "count_function": count_result,
#         "actual_total": total_actual_records,
#         "actual_pages": page,
#         "match": count_result['total_records'] == total_actual_records
#     }

# def verify_new_count(measurement: str, channel: str, days_limit: int = 30):
#     """
#     새로운 카운트 함수 검증
#     """
#     # 새 카운트 함수 테스트
#     count_result = count_influx_records_with_limit(measurement, channel, 10, days_limit)
#     print(f"카운트 함수 결과: {count_result['total_records']} records")

#     # 실제 페이징으로 확인
#     total_actual = 0
#     page = 1
#     while True:
#         rows = query_influx_pages(measurement, channel, "time", page, 10, days_limit)
#         if not rows:
#             break
#         total_actual += len(rows)
#         if len(rows) < 10:
#             break
#         page += 1

#     print(f"실제 데이터: {total_actual} records")
#     print(f"매치: {'✅' if count_result['total_records'] == total_actual else '❌'}")

#     # 차이가 있으면 상세 분석
#     if count_result['total_records'] != total_actual:
#         print(f"\n차이: {abs(count_result['total_records'] - total_actual)}")
#         print(f"비율: {count_result['total_records'] / total_actual if total_actual > 0 else 'N/A'}")

#     return count_result['total_records'] == total_actual

# @router.get("/getAlarms/{channel}/{page}")
# @gc_after_large_data(threshold_mb=30)
# async def get_alarms(channel: str, page: int):
#     """최적화된 알람 조회"""
#     try:
#         # 병렬 실행을 위한 태스크 생성
#         data_task = run_influx_query(
#             query_influx_pages,
#             "alarms", channel, "time", int(page),
#             timeout=20
#         )

#         count_task = run_influx_query(
#             count_influx_records_optimized,
#             "alarms", channel,
#             timeout=10
#         )

#         # 동시 실행
#         result, countDict = await asyncio.gather(data_task, count_task)

#         # 데이터 포맷팅
#         for i in range(len(result)):
#             if os_spec.os == 'Windows':
#                 result[i]["condition_str"] = convert_inequality_to_text(result[i]["condition_str"])
#                 result[i]["alarm_ts"] = format_influx_time(result[i]["alarm_ts"])
#             else:
#                 result[i]["condition_str"] = f"{result[i]['chan_text']} {result[i]['condition']} {result[i]['level']}"
#                 result[i]["alarm_ts"] = format_influx_time(result[i]["time"])

#         return {
#             "success": True,
#             "data": result,
#             "totalRecord": countDict['total_records'],
#             "totalPages": countDict['total_pages']
#         }

#     except HTTPException:
#         raise  # HTTPException은 그대로 전달
#     except Exception as e:
#         logging.error(f"Unexpected error in get_alarms: {e}")
#         return {
#             "success": False,
#             "error": str(e),
#             "data": [],
#             "totalRecord": 0,
#             "totalPages": 0
#         }


# @router.post("/getAlarmSearch/{channel}/{page}")
# async def get_alarmSearch(data: AlarmSearch, channel: str, page: int):
#     """최적화된 알람 검색"""
#     try:
#         # 병렬 실행
#         data_task = run_influx_query(
#             query_paged_search,
#             "alarms", channel, data.param,
#             data.StartDate, data.EndDate, int(page),
#             timeout=20
#         )

#         count_task = run_influx_query(
#             count_search_records_optimized,
#             "alarms", channel, data.param,
#             data.StartDate, data.EndDate,
#             timeout=10
#         )

#         result, countDict = await asyncio.gather(data_task, count_task)

#         # 포맷팅
#         for i in range(len(result)):
#             result[i]["condition_str"] = f"{result[i]['chan_text']} {result[i]['condition']} {result[i]['level']}"
#             result[i]["alarm_ts"] = format_influx_time(result[i]["time"])

#         return {
#             "success": True,
#             "data": result,
#             "totalRecord": countDict['total_records'],
#             "totalPages": countDict['total_pages']
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         logging.error(f"Error in get_alarmSearch: {e}")
#         return {
#             "success": False,
#             "error": str(e),
#             "data": [],
#             "totalRecord": 0,
#             "totalPages": 0
#         }


# @router.get("/getEventlist/{channel}/{page}")
# @gc_after_large_data(threshold_mb=30)
# async def get_eventlist(channel: str, page: int):
#     """최적화된 이벤트 조회 - 기존 함수 재사용"""
#     try:
#         page = int(page)

#         # 현재 페이지 데이터 조회
#         data_task = run_influx_query(
#             query_influx_pages,
#             "events", channel, "time", page,
#             timeout=20
#         )

#         # 다음 페이지 첫 번째 레코드만 조회 (존재 여부 확인)
#         next_check_task = run_influx_query(
#             query_influx_pages,
#             "events", channel, "time", page + 1, 1,  # 1개만 조회
#             timeout=5
#         )

#         result, next_check = await asyncio.gather(data_task, next_check_task)

#         # 데이터 포맷팅
#         for i in range(len(result)):
#             if isinstance(result[i]["time"], datetime):
#                 timestamp = result[i]["time"].timestamp()
#             else:
#                 timestamp = float(result[i]["time"])

#             # duration을 초 단위로 변환 (밀리초인 경우)
#             duration_seconds = float(result[i].get("duration", 0)) / 1000.0

#             # 종료 시간 계산
#             end_timestamp = timestamp + duration_seconds
#             end_datetime = datetime.fromtimestamp(end_timestamp)

#             # 포맷팅
#             result[i]["end_ts"] = format_influx_militime(end_datetime)
#             result[i]["start_ts"] = format_influx_militime(result[i]["time"])

#         ret = {
#             "success": True,
#             "data": result,
#             "page": page,
#             "hasNext": len(next_check) > 0,
#             "hasPrev": page > 1,
#             # 하위 호환성
#             "totalRecord": -1,
#             "totalPages": -1
#         }

#         return {
#             "success": True,
#             "data": result,
#             "page": page,
#             "hasNext": len(next_check) > 0,
#             "hasPrev": page > 1,
#             # 하위 호환성
#             "totalRecord": -1,
#             "totalPages": -1
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         logging.error(f"Error in get_eventlist: {e}")
#         return {
#             "success": False,
#             "error": str(e),
#             "data": [],
#             "page": page,
#             "hasNext": False,
#             "hasPrev": False,
#             "totalRecord": 0,
#             "totalPages": 0
#         }

# @router.get("/getEventlist/{channel}/{page}")
# @gc_after_large_data(threshold_mb=30)
# async def get_eventlist(channel: str, page: int):
#     """최적화된 이벤트 조회"""
#     try:
#         # 병렬 실행
#         data_task = run_influx_query(
#             query_influx_pages,
#             "events", channel, "time", int(page),
#             timeout=20
#         )
#         #count_influx_records_optimized , count_influx_records_with_limit
#         count_task = run_influx_query(
#              count_influx_records_with_limit_v2,
#             "events", channel,
#             timeout=10
#         )


#         result, countDict = await asyncio.gather(data_task, count_task)

#         # 데이터 포맷팅
#         for i in range(len(result)):
#             if isinstance(result[i]["time"], datetime):
#                 timestamp = result[i]["time"].timestamp()
#             else:
#                 timestamp = float(result[i]["time"])

#             # duration을 초 단위로 변환 (밀리초인 경우)
#             duration_seconds = float(result[i]["duration"]) / 1000.0

#             # 종료 시간 계산
#             end_timestamp = timestamp + duration_seconds
#             end_datetime = datetime.fromtimestamp(end_timestamp)

#             # 포맷팅
#             result[i]["end_ts"] = format_influx_militime(end_datetime)
#             result[i]["start_ts"] = format_influx_militime(result[i]["time"])

#         print(countDict)

#         return {
#             "success": True,
#             "data": result,
#             "totalRecord": countDict['total_records'],
#             "totalPages": countDict['total_pages']
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         logging.error(f"Error in get_eventlist: {e}")
#         return {
#             "success": False,
#             "error": str(e),
#             "data": [],
#             "totalRecord": 0,
#             "totalPages": 0
#         }


# @router.post("/getEventSearch/{channel}/{page}")
# async def get_eventSearch(data: EventSearch, channel: str, page: int):
#     """최적화된 이벤트 검색"""
#     try:
#         startdate = data.StartDate
#         param = eventType[int(data.param)]  # eventType 배열에서 변환
#         enddate = data.EndDate

#         # 병렬 실행
#         data_task = run_influx_query(
#             query_paged_search_event,
#             "events", channel, param,
#             startdate, enddate, int(page),
#             timeout=20
#         )

#         count_task = run_influx_query(
#             count_search_records_event_optimized,
#             "events", channel, param,
#             startdate, enddate,
#             timeout=10
#         )

#         result, countDict = await asyncio.gather(data_task, count_task)

#         # 데이터 포맷팅
#         for i in range(len(result)):
#             if isinstance(result[i]["time"], datetime):
#                 timestamp = result[i]["time"].timestamp()
#             else:
#                 timestamp = float(result[i]["time"])

#             # duration을 초 단위로 변환 (밀리초인 경우)
#             duration_seconds = float(result[i]["duration"]) / 1000.0

#             # 종료 시간 계산
#             end_timestamp = timestamp + duration_seconds
#             end_datetime = datetime.fromtimestamp(end_timestamp)

#             # 포맷팅
#             result[i]["end_ts"] = format_influx_militime(end_datetime)
#             result[i]["start_ts"] = format_influx_militime(result[i]["time"])

#         return {
#             "success": True,
#             "data": result,
#             "totalRecord": countDict['total_records'],
#             "totalPages": countDict['total_pages']
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         logging.error(f"Error in get_eventSearch: {e}")
#         return {
#             "success": False,
#             "error": str(e),
#             "data": [],
#             "totalRecord": 0,
#             "totalPages": 0
#         }
# @router.get("/getAlarms/{channel}/{page}")
# async def get_alarms(channel: str, page: int):
#     """최적화된 알람 조회"""
#     try:
#         # 병렬로 데이터와 카운트 실행
#         data_task = run_with_timeout(
#             query_influx_pages,
#             "alarms", channel, "time", int(page),
#             timeout=20
#         )
#
#         count_task = run_with_timeout(
#             count_influx_records_optimized,
#             "alarms", channel,
#             timeout=10
#         )
#
#         # 동시 실행
#         result, countDict = await asyncio.gather(data_task, count_task)
#
#         # 데이터 포맷팅
#         for i in range(len(result)):
#             if os_spec.os == 'Windows':
#                 result[i]["condition_str"] = convert_inequality_to_text(result[i]["condition_str"])
#                 result[i]["alarm_ts"] = format_influx_time(result[i]["alarm_ts"])
#             else:
#                 result[i]["condition_str"] = f"{result[i]['chan_text']} {result[i]['condition']} {result[i]['level']}"
#                 result[i]["alarm_ts"] = format_influx_time(result[i]["time"])
#
#         return {
#             "success": True,
#             "data": result,
#             "totalRecord": countDict['total_records'],
#             "totalPages": countDict['total_pages']
#         }
#
#     except asyncio.TimeoutError:
#         return {
#             "success": False,
#             "error": "Query timeout - please narrow your search range",
#             "data": [],
#             "totalRecord": 0,
#             "totalPages": 0
#         }
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e),
#             "data": [],
#             "totalRecord": 0,
#             "totalPages": 0
#         }
#
#
# @router.post("/getAlarmSearch/{channel}/{page}")
# async def get_alarmSearch(data: AlarmSearch, channel: str, page: int):
#     """최적화된 알람 검색"""
#     startdate = data.StartDate
#     param = data.param
#     enddate = data.EndDate
#
#     try:
#         # 병렬 실행
#         data_task = run_with_timeout(
#             query_paged_search,
#             "alarms", channel, param, startdate, enddate, int(page),
#             timeout=20
#         )
#
#         count_task = run_with_timeout(
#             count_search_records_optimized,
#             "alarms", channel, param, startdate, enddate,
#             timeout=10
#         )
#
#         result, countDict = await asyncio.gather(data_task, count_task)
#
#         # 데이터 포맷팅
#         for i in range(len(result)):
#             result[i]["condition_str"] = f"{result[i]['chan_text']} {result[i]['condition']} {result[i]['level']}"
#             result[i]["alarm_ts"] = format_influx_time(result[i]["time"])
#
#         return {
#             "success": True,
#             "data": result,
#             "totalRecord": countDict['total_records'],
#             "totalPages": countDict['total_pages']
#         }
#
#     except asyncio.TimeoutError:
#         return {
#             "success": False,
#             "error": "Query timeout - please narrow your date range",
#             "data": [],
#             "totalRecord": 0,
#             "totalPages": 0
#         }
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e),
#             "data": [],
#             "totalRecord": 0,
#             "totalPages": 0
#         }


# @router.get("/getEventlist/{channel}/{page}")
# async def get_eventlist(channel: str, page: int):
#     """최적화된 이벤트 조회"""
#     try:
#         # 병렬 실행
#         data_task = run_with_timeout(
#             query_influx_pages,
#             "events", channel, "time", int(page),
#             timeout=20
#         )
#
#         count_task = run_with_timeout(
#             count_influx_records_optimized,
#             "events", channel,
#             timeout=10
#         )
#
#         result, countDict = await asyncio.gather(data_task, count_task)
#
#         # 데이터 포맷팅
#         for i in range(len(result)):
#             if isinstance(result[i]["time"], datetime):
#                 timestamp = result[i]["time"].timestamp()
#             else:
#                 timestamp = float(result[i]["time"])
#
#             duration_seconds = float(result[i]["duration"]) / 1000.0
#             end_timestamp = timestamp + duration_seconds
#             end_datetime = datetime.fromtimestamp(end_timestamp)
#
#             result[i]["end_ts"] = format_influx_militime(end_datetime)
#             result[i]["start_ts"] = format_influx_militime(result[i]["time"])
#
#         return {
#             "success": True,
#             "data": result,
#             "totalRecord": countDict['total_records'],
#             "totalPages": countDict['total_pages']
#         }
#
#     except asyncio.TimeoutError:
#         return {
#             "success": False,
#             "error": "Query timeout - please try with smaller date range",
#             "data": [],
#             "totalRecord": 0,
#             "totalPages": 0
#         }
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e),
#             "data": [],
#             "totalRecord": 0,
#             "totalPages": 0
#         }
#
#
# @router.post("/getEventSearch/{channel}/{page}")
# async def get_eventSearch(data: EventSearch, channel: str, page: int):
#     """최적화된 이벤트 검색"""
#     startdate = data.StartDate
#     param = eventType[int(data.param)]
#     enddate = data.EndDate
#
#     try:
#         # 병렬 실행
#         data_task = run_with_timeout(
#             query_paged_search_event,
#             "events", channel, param, startdate, enddate, int(page),
#             timeout=20
#         )
#
#         count_task = run_with_timeout(
#             count_search_records_event_optimized,
#             "events", channel, param, startdate, enddate,
#             timeout=10
#         )
#
#         result, countDict = await asyncio.gather(data_task, count_task)
#
#         # 데이터 포맷팅
#         for i in range(len(result)):
#             if isinstance(result[i]["time"], datetime):
#                 timestamp = result[i]["time"].timestamp()
#             else:
#                 timestamp = float(result[i]["time"])
#
#             duration_seconds = float(result[i]["duration"]) / 1000.0
#             end_timestamp = timestamp + duration_seconds
#             end_datetime = datetime.fromtimestamp(end_timestamp)
#
#             result[i]["end_ts"] = format_influx_militime(end_datetime)
#             result[i]["start_ts"] = format_influx_militime(result[i]["time"])
#
#         return {
#             "success": True,
#             "data": result,
#             "totalRecord": countDict['total_records'],
#             "totalPages": countDict['total_pages']
#         }
#
#     except asyncio.TimeoutError:
#         return {
#             "success": False,
#             "error": "Query timeout - please narrow your search criteria",
#             "data": [],
#             "totalRecord": 0,
#             "totalPages": 0
#         }
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e),
#             "data": [],
#             "totalRecord": 0,
#             "totalPages": 0
#         }
# @router.get("/getAlarms/{channel}/{page}")
# async def get_alarms(channel: str, page: int):
#     """기존 엔드포인트를 비동기로 변경"""
#     loop = asyncio.get_event_loop()
#
#     try:
#         result = await loop.run_in_executor(
#             executor,
#             query_influx_pages,
#             "alarms", channel, "time", int(page)
#         )
#         # 카운트도 비동기로
#         countDict = await loop.run_in_executor(
#             executor,
#             count_influx_records_optimized,
#             "alarms", channel
#         )
#
#         # 데이터 포맷팅 (동일)
#         for i in range(len(result)):
#             if os_spec.os == 'Windows':
#                 result[i]["condition_str"] = convert_inequality_to_text(result[i]["condition_str"])
#                 result[i]["alarm_ts"] = format_influx_time(result[i]["alarm_ts"])
#             else:
#                 result[i]["condition_str"] = f"{result[i]['chan_text']} {result[i]['condition']} {result[i]['level']}"
#                 result[i]["alarm_ts"] = format_influx_time(result[i]["time"])
#
#         return {
#             "success": True,
#             "data": result,
#             "totalRecord": countDict['total_records'],
#             "totalPages": countDict['total_pages']
#         }
#
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e),
#             "data": [],
#             "totalRecord": 0,
#             "totalPages": 0
#         }
#
#
#
# @router.post("/getAlarmSearch/{channel}/{page}")
# async def get_alarmSearch(request:Request, data:AlarmSearch, channel, page):
#     #body = await request.json()
#     startdate = data.StartDate
#     param = data.param
#     enddate = data.EndDate
#     result = query_paged_search("alarms", channel,param, startdate,enddate, page=int(page))
#     for i in range(len(result)):
#         result[i]["condition_str"] = f"{result[i]['chan_text']} {result[i]['condition']} {result[i]['level']}"
#         result[i]["alarm_ts"] = format_influx_time(result[i]["time"])
# #        result[i]["alarm_ts"] = format_influx_time(result[i]["alarm_ts"])
#     countDict = count_search_records_optimized("alarms", channel,param,startdate, enddate)
#
#     return {"success":True , "data":result, "totalRecord":countDict['total_records'], "totalPages":countDict['total_pages']}
#
#
#
# @router.get("/getEventlist/{channel}/{page}")
# async def get_eventlist(channel, page):
#     # existed version
#     loop = asyncio.get_event_loop()
#
#     result = await loop.run_in_executor(
#         executor, query_influx_pages, "events", channel, "time", int(page)
#     )
#     for i in range(len(result)):
#         #            result[i]["end_ts"] = format_influx_time(float(result[i]["time"]) + float(result[i]["duration"]))
#         #            result[i]["start_ts"] = format_influx_time(result[i]["time"])
#         if isinstance(result[i]["time"], datetime):
#             timestamp = result[i]["time"].timestamp()
#         else:
#             timestamp = float(result[i]["time"])
#
#         # duration을 초 단위로 변환 (밀리초인 경우)
#         duration_seconds = float(result[i]["duration"]) / 1000.0
#
#         # 종료 시간 계산
#         end_timestamp = timestamp + duration_seconds
#         end_datetime = datetime.fromtimestamp(end_timestamp)
#
#         # 포맷팅
#         result[i]["end_ts"] = format_influx_militime(end_datetime)
#         result[i]["start_ts"] = format_influx_militime(result[i]["time"])
#     countDict = count_influx_records_optimized("events", channel)
#
#     return {"success": True, "data": result, "totalRecord": countDict['total_records'],
#             "totalPages": countDict['total_pages']}
#
#
# @router.post("/getEventSearch/{channel}/{page}")
# async def get_eventSearch(data: EventSearch, channel, page):
#     startdate = data.StartDate
#     param = eventType[int(data.param)]
#     enddate = data.EndDate
#     result = query_paged_search_event("events", channel, param, startdate, enddate, page=int(page))
#     print(result)
#     for i in range(len(result)):
#         if isinstance(result[i]["time"], datetime):
#             timestamp = result[i]["time"].timestamp()
#         else:
#             timestamp = float(result[i]["time"])
#
#         # duration을 초 단위로 변환 (밀리초인 경우)
#         duration_seconds = float(result[i]["duration"]) / 1000.0
#
#         # 종료 시간 계산
#         end_timestamp = timestamp + duration_seconds
#         end_datetime = datetime.fromtimestamp(end_timestamp)
#
#         # 포맷팅
#         result[i]["end_ts"] = format_influx_militime(end_datetime)
#         result[i]["start_ts"] = format_influx_militime(result[i]["time"])
#     countDict = count_search_records_event_optimized("events", channel, param, startdate, enddate)
#     return {"success": True, "data": result, "totalRecord": countDict['total_records'],
#             "totalPages": countDict['total_pages']}


# @router.get("/getStatuscached/{asset}/{channel}")
# @gc_after_large_data(threshold_mb=30)
# async def getStatus_cached(asset, channel):  # 파라미터 순서 수정
#     """
#     진단 데이터 조회 - Redis 우선, 없으면 API 호출
#     """
#     redis_state.client.select(1)
#     if channel == 'main' or channel == 'Main':
#         chName = 'Main'
#     else:
#         chName = 'Sub'
#     cache_key = f"SmartAPI:{chName}"
#     cache_field = "Diagnosis"
#     data = None  # datas -> data로 통일
#
#     # 1. Redis에서 조회
#     try:
#         # redis_state.client.select(1)
#         cached_data = redis_state.client.hget(cache_key, cache_field)
#         if cached_data:
#             data = json.loads(cached_data)  # ✅ 조회한 데이터 사용
#             print(f"[Redis HIT] Data found for {chName}")
#     except Exception as e:
#         print(f"[Redis Error] {e}")
#
#     # 2. Redis에 없으면 API 호출
#     if data is None:  # ✅ datas -> data
#         try:
#             print(f"[API CALL] Fetching data for {asset}")
#             async with httpx.AsyncClient(timeout=api_timeout) as client:
#                 response = await client.get(f"http://{os_spec.restip}:5000/api/getDiagnostic?name={asset}")
#                 data = response.json()
#
#             #API에서 가져온 데이터 Redis에 저장
#             # if data:  # ✅ datas -> data
#             #     try:
#             #         redis_state.client.hset(cache_key, cache_field, json.dumps(data, ensure_ascii=False))  # ✅ data 저장
#             #         print(f"[Redis SAVE] Data saved for {chName}")
#             #     except Exception as e:
#             #         print(f"[Redis Save Error] {e}")
#
#         except Exception as e:
#             return {"success": False, "error": f"Failed to fetch data: {str(e)}"}
#
#     # 3. 데이터 처리 및 반환
#     if data and len(data) > 0:
#         runhours = get_running(channel)["total"]
#         updateTimes = data["LastRecordDateTime"]
#         # BarGraph가 있는지 확인
#         if "BarGraph" not in data or len(data["BarGraph"]) == 0:
#             return {"status": -1, "runhours": runhours}
#
#         # Status 추출
#         status_list = [item["Status"] for item in data["BarGraph"] if "Status" in item]
#
#         # 상태 판단
#         if not status_list:
#             return {"status": 0, "runhours": runhours}
#
#         if all(status == 1 for status in status_list):
#             return {"status": 1, "runhours": runhours}
#
#         if all(status == 0 for status in status_list):
#             return {"status": 0, "runhours": runhours}
#
#         # 우선순위 체크
#         for priority_status in [4, 3, 2, 1]:
#             if priority_status in status_list:
#                 return {"status": priority_status, "runhours": runhours, "updateTime": updateTimes}
#
#         return {"status": -2, "runhours": runhours, "updateTime": updateTimes}
#     else:
#         return {"success": False, "error": "No Data"}
#
# @router.get("/getStatus/{asset}/{channel}")  # Master Dashboard Status
# @gc_after_large_data(threshold_mb=30)
# async def getStatus(asset, channel):
#     try:
#         # response = await  http_state.client.get(f"/getDiagnostic?name={asset}")
#         # data = response.json()
#         async with httpx.AsyncClient(timeout=api_timeout) as client:
#             response = await client.get(f"http://{os_spec.restip}:5000/api/getDiagnostic?name={asset}")
#             data = response.json()  # JSON 데이터 파싱
#         #     if response.status_code in [400, 401, 500]:
#         #         flag = await checkLoginAPI(request)
#         #         if not flag:
#         #             return {"success": False, "error": "Restful API Login Failed"}
#         #         else:
#         #             response = await client.get(f"http://{os_spec.restip}:5000/api/getDiagnostic?name={asset}")
#         #             data = response.json()  # JSON 데이터 파싱
#     except Exception as e:
#         print(str(e))
#         return {"status": -1}
#     runhours = get_running(channel)["total"]
#     # success가 True인지 확인
#     if len(data) == 0:
#         return {"status": -1, "runhours": runhours}
#
#     # "data" 항목이 존재하는지 확인
#     status_list = [item["Status"] for item in data["BarGraph"] if "Status" in item]
#
#     # print(status_list)
#
#     # 모든 값이 1이면 "OK"
#     if all(status == 1 for status in status_list):
#         return {"status": 1, "runhours": runhours}
#
#     # 모든 값이 0이면 "No Data"
#     if all(status == 0 for status in status_list):
#         return {"status": 0, "runhours": runhours}
#
#     # 우선순위: Repair(4) > Inspect(3) > Warning(2)
#     if 4 in status_list:
#         return {"status": 4, "runhours": runhours}
#     elif 3 in status_list:
#         return {"status": 3, "runhours": runhours}
#     elif 2 in status_list:
#         return {"status": 2, "runhours": runhours}
#     elif 1 in status_list:
#         return {"status": 1, "runhours": runhours}
#     else:
#         return {"status": -2, "runhours": runhours}


# @router.get("/getPQStatusCached/{asset}/{channel}")
# @gc_after_large_data(threshold_mb=30)
# async def getPQStatus_cached(asset, channel):
#     redis_state.client.select(1)
#     if channel == 'main' or channel == 'Main':
#         chName = 'Main'
#     else:
#         chName = 'Sub'
#     cache_key = f"SmartAPI:{chName}"
#     cache_field = "PQ"
#     data = None
#
#     # 1. Redis에서 조회
#     try:
#         # redis_state.client.select(1)
#         cached_data = redis_state.client.hget(cache_key, cache_field)
#         if cached_data:
#             data = json.loads(cached_data)
#             print(f"[Redis HIT] PQ data found for {chName}")
#     except Exception as e:
#         print(f"[Redis Error] {e}")
#
#     # 2. Redis에 없으면 API 호출
#     if data is None:
#         try:
#             print(f"[API CALL] Fetching PQ data for {asset}")
#             async with httpx.AsyncClient(timeout=api_timeout) as client:
#                 response = await client.get(f"http://{os_spec.restip}:5000/api/getPQ?name={asset}")
#                 data = response.json()
#
#             # ✅ Redis에 저장 (빠진 부분 추가!)
#             # if data:
#             #     try:
#             #         redis_state.client.hset(cache_key, cache_field, json.dumps(data, ensure_ascii=False))
#             #         print(f"[Redis SAVE] PQ data saved for {channel}")
#             #     except Exception as e:
#             #         print(f"[Redis Save Error] {e}")
#
#         except Exception as e:
#             return {"status": -1}
#
#     # 3. 데이터 처리 (기존 로직 그대로)
#     if not data or len(data) == 0:
#         return {"status": -1}
#
#     status_items = [
#         {"Title": item["Title"], "Status": item["Status"]}
#         for item in data.get("BarGraph", [])
#         if "Status" in item and "Title" in item
#     ]
#     updateTimes = data["LastRecordDateTime"]
#
#     if not status_items:
#         return {"status": -2}
#
#     if all(item["Status"] == 0 for item in status_items):
#         return {"status": 0, "item": "All"}
#
#     if all(item["Status"] == 1 for item in status_items):
#         return {"status": 1, "item": "All"}
#
#     sorted_items = sorted(status_items, key=lambda x: x["Status"], reverse=True)
#     highest_status = sorted_items[0]["Status"]
#     top_items = [item for item in sorted_items if item["Status"] == highest_status]
#
#     if len(top_items) == 1:
#         item_label = top_items[0]["Title"]
#     elif len(top_items) == 2:
#         item_label = f"{top_items[0]['Title']}, {top_items[1]['Title']}"
#     else:
#         item_label = f"{top_items[0]['Title']} ... +{len(top_items) - 1}"
#
#     return {"status": highest_status, "item": item_label, "updateTime": updateTimes}

# @router.get("/getPQCached/{channel}/{asset}")
# @gc_after_large_data(threshold_mb=30)
# async def get_PQ_cached(channel, asset):
#     """
#     진단 데이터 조회 - Redis 우선, 없으면 API 호출
#     """
#     redis_state.client.select(1)
#     if channel == 'main' or channel == 'Main':
#         chName = 'Main'
#     else:
#         chName = 'Sub'
#     cache_key = f"SmartAPI:{chName}"
#     cache_field = "PQ"
#     datas = None
#
#     # 1. Redis에서 조회
#     try:
#
#         cached_data = redis_state.client.hget(cache_key, cache_field)
#         if cached_data:
#             datas = json.loads(cached_data)
#     except Exception as e:
#         print(f"[Redis Error] {e}")
#
#     # 2. Redis에 없으면 API 호출
#     if datas is None:
#         try:
#             print(f"[API CALL] Fetching PQ data for {asset}")
#             async with httpx.AsyncClient(timeout=api_timeout) as client:
#                 response = await client.get(f"http://{os_spec.restip}:5000/api/getPQ?name={asset}")
#                 data = response.json()
#
#             # ✅ Redis에 저장 (빠진 부분 추가!)
#             if data:
#                 try:
#                     redis_state.client.hset(cache_key, cache_field, json.dumps(data, ensure_ascii=False))
#                 except Exception as e:
#                     pass
#
#         except Exception as e:
#             return {"success": False, "error": f"Failed to fetch data: {str(e)}"}
#
#     # 3. 데이터 처리 및 반환
#     if datas and len(datas) > 0:
#         ret = proc_DiagnosisData_optimized(datas)
#         return {"success": True, "data_status": ret['data_status'], "data_tree": ret['data_tree']}
#     else:
#         return {"success": False, "error": "No Data"}



# @router.get("/getFaultCached/{channel}/{asset}")
# async def get_Fault_cached(channel, asset):
#     """
#     진단 데이터 조회 - Redis 우선, 없으면 API 호출
#     """
#     redis_state.client.select(1)
#     if channel == 'main' or channel == 'Main':
#         chName = 'Main'
#     else:
#         chName = 'Sub'
#     cache_key = f"SmartAPI:{chName}"
#     cache_field = "Fault"
#     datas = None
#
#     # 1. Redis에서 조회
#     try:
#         # redis_state.client.select(1)
#         cached_data = redis_state.client.hget(cache_key, cache_field)
#         if cached_data:
#             datas = json.loads(cached_data)
#     except Exception as e:
#         print(f"[Redis Error] {e}")
#
#     # 2. Redis에 없으면 API 호출
#     if datas is None:
#         try:
#             print(f"[API] Fetching data for {chName}")
#             async with httpx.AsyncClient(timeout=api_timeout) as client:
#                 response = await client.get(f"http://{os_spec.restip}:5000/api/getFaults?name={asset}")
#                 datas = response.json()
#
#             # API에서 가져온 데이터 Redis에 저장
#             if datas:
#                 try:
#                     redis_state.client.hset(cache_key, cache_field, json.dumps(datas, ensure_ascii=False))
#                 except:
#                     pass  # 저장 실패 무시
#
#         except Exception as e:
#             return {"success": False, "error": f"Failed to fetch data: {str(e)}"}
#
#     # 3. 데이터 처리 및 반환
#     if datas and len(datas) > 0:
#         ret = proc_eventFaultData(datas)
#         return {"success": True, "data_status": ret['data_status'], "data_tree": ret['data_tree']}
#     else:
#         return {"success": False, "error": "No Data"}



# @router.get("/getEventsCached/{channel}/{asset}")
# async def get_Event_cached(channel, asset):
#     """
#     진단 데이터 조회 - Redis 우선, 없으면 API 호출
#     """
#     redis_state.client.select(1)
#     if channel == 'main' or channel == 'Main':
#         chName = 'Main'
#     else:
#         chName = 'Sub'
#     cache_key = f"SmartAPI:{chName}"
#     cache_field = "Event"
#     datas = None
#
#     # 1. Redis에서 조회
#     try:
#         # redis_state.client.select(1)
#         cached_data = redis_state.client.hget(cache_key, cache_field)
#         if cached_data:
#             datas = json.loads(cached_data)
#     except Exception as e:
#         print(f"[Redis Error] {e}")
#
#     # 2. Redis에 없으면 API 호출
#     if datas is None:
#         try:
#             print(f"[API] Fetching data for {chName}")
#             async with httpx.AsyncClient(timeout=api_timeout) as client:
#                 response = await client.get(f"http://{os_spec.restip}:5000/api/getEvents?name={asset}")
#                 datas = response.json()
#
#             # API에서 가져온 데이터 Redis에 저장
#             if datas:
#                 try:
#                     redis_state.client.hset(cache_key, cache_field, json.dumps(datas, ensure_ascii=False))
#                 except:
#                     pass  # 저장 실패 무시
#
#         except Exception as e:
#             return {"success": False, "error": f"Failed to fetch data: {str(e)}"}
#
#     # 3. 데이터 처리 및 반환
#     if datas and len(datas) > 0:
#         ret = proc_eventFaultData(datas)
#         return {"success": True, "data_status": ret['data_status'], "data_tree": ret['data_tree']}
#     else:
#         return {"success": False, "error": "No Data"}

# @router.get("/getEventStatus/{asset}/{channel}")
# @gc_after_large_data(threshold_mb=30)
# async def get_eventstatus(asset, channel):
#     try:
#         # 1. API에서 PQ 데이터 가져오기
#         async with httpx.AsyncClient(timeout=api_timeout) as client:
#             response = await client.get(f"http://{os_spec.restip}:5000/api/getEvents?name={asset}")
#             data = response.json()
#
#         # 2. Redis에서 DashAlarms 설정 가져오기
#         redis_state.client.select(0)
#         redis_data = redis_state.client.hget("Equipment", "DashAlarms")
#
#         # 설정이 없으면 기존 로직 사용
#         if not redis_data:
#             return await getEventFault_legacy(data)
#
#         dash_alarms = json.loads(redis_data)
#         channel_config = dash_alarms.get(channel)
#
#         # 해당 채널 설정이 없으면 기존 로직 사용
#         if not channel_config:
#             return await getEventFault_legacy(data)
#
#         if not channel_config.get("event"):
#             return await getEventFault_legacy(data)
#
#     except Exception as e:
#         return {"status": -1}
#
#     # 데이터 검증
#     if not data or not isinstance(data, dict):  # ✅ 딕셔너리 체크
#         return {"status": -1}
#
#     bar_graph = data.get("BarGraph", [])
#     if not bar_graph:
#         return {"status": -2}
#
#     # 3. AlarmStatusMatcher로 PQ 계산
#     try:
#         matcher = AlarmStatusMatcher()
#         status_info = {
#             "diagnosis": [],  # PQ만 계산
#             "pq": [],
#             "event": channel_config.get("event", []),
#             "fault": []
#         }
#
#         result = matcher.diagnose(status_info, bar_graph)
#         final_status = result["final_status"]
#         matched_params = result["matched_parameters"]
#
#         # 매칭된 항목이 없으면
#         if not matched_params:
#             return {"status": 1, "item": "All"}
#
#         # 매칭된 항목들 중 가장 높은 status들만
#         max_status = max(p["actual_status"] for p in matched_params)
#         top_items = [p for p in matched_params if p["actual_status"] == max_status]
#
#         # item 리턴 포맷 구성
#         if len(top_items) == 1:
#             item_label = top_items[0]["name"]
#         elif len(top_items) == 2:
#             item_label = f"{top_items[0]['name']}, {top_items[1]['name']}"
#         else:
#             item_label = f"{top_items[0]['name']} ... +{len(top_items) - 1}"
#
#         return {"status": final_status, "item": item_label}
#
#     except Exception as e:
#         print(f"AlarmStatusMatcher error: {str(e)}")
#         # 에러 시 기존 로직으로 fallback
#         return await getEventFault_legacy(data)
#
#
# @router.get("/getFaultStatus/{asset}/{channel}")
# @gc_after_large_data(threshold_mb=30)
# async def get_faultstatus(asset, channel):
#     try:
#         # 1. API에서 PQ 데이터 가져오기
#         async with httpx.AsyncClient(timeout=api_timeout) as client:
#             response = await client.get(f"http://{os_spec.restip}:5000/api/getFaults?name={asset}")
#             data = response.json()
#
#         # 2. Redis에서 DashAlarms 설정 가져오기
#         redis_state.client.select(0)
#         redis_data = redis_state.client.hget("Equipment", "DashAlarms")
#
#         # 설정이 없으면 기존 로직 사용
#         if not redis_data:
#             # print(f"{channel} - Not Redis : getEventFault_legacy")
#             return await getEventFault_legacy(data)
#
#         dash_alarms = json.loads(redis_data)
#         channel_config = dash_alarms.get(channel)
#
#         # 해당 채널 설정이 없으면 기존 로직 사용
#         if not channel_config:
#             # print(f"{channel} - Not Channel : getEventFault_legacy")
#             return await getEventFault_legacy(data)
#
#         if not channel_config.get("fault"):
#             # print(f"{channel} - Not Setup : getEventFault_legacy")
#             return await getEventFault_legacy(data)
#
#     except Exception as e:
#         print(str(e))
#         return {"status": -1}
#
#     # 데이터 검증
#     if not data or not isinstance(data, dict):  # ✅ 딕셔너리 체크
#         return {"status": -1}
#
#     bar_graph = data.get("BarGraph", [])
#     if not bar_graph:
#         return {"status": -2}
#
#     # 3. AlarmStatusMatcher로 PQ 계산
#     try:
#         matcher = AlarmStatusMatcher()
#         status_info = {
#             "diagnosis": [],  # PQ만 계산
#             "pq": [],
#             "event": [],
#             "fault": channel_config.get("fault", [])
#         }
#
#         result = matcher.diagnose(status_info, bar_graph)
#         final_status = result["final_status"]
#         matched_params = result["matched_parameters"]
#
#         # 매칭된 항목이 없으면
#         if not matched_params:
#             return {"status": 1, "item": "All"}
#
#         # 매칭된 항목들 중 가장 높은 status들만
#         max_status = max(p["actual_status"] for p in matched_params)
#         top_items = [p for p in matched_params if p["actual_status"] == max_status]
#
#         # item 리턴 포맷 구성
#         if len(top_items) == 1:
#             item_label = top_items[0]["name"]
#         elif len(top_items) == 2:
#             item_label = f"{top_items[0]['name']}, {top_items[1]['name']}"
#         else:
#             item_label = f"{top_items[0]['name']} ... +{len(top_items) - 1}"
#
#         return {"status": final_status, "item": item_label}
#
#     except Exception as e:
#         print(f"AlarmStatusMatcher error: {str(e)}")
#         # 에러 시 기존 로직으로 fallback
#         return await getPQStatus_legacy(data)
#
# async def getEventFault_legacy(data):
#     """기존 로직 (fallback용)"""
#     if not data or not isinstance(data, dict):  # ✅ 딕셔너리 체크
#         return {"status": -1}
#
#     status_items = [
#         {"Title": item["Title"], "Status": item["Status"]}
#         for item in data.get("BarGraph", [])
#         if "Status" in item and "Title" in item
#     ]
#
#     if not status_items:
#         return {"status": -2}
#
#     # 모든 값이 0이면 "No Data"
#     if all(item["Status"] == 0 for item in status_items):
#         return {"status": 0, "item": "All"}
#
#     if all(item["Status"] == 1 for item in status_items):
#         return {"status": 1, "item": "All"}
#
#     # 상태가 높은 순으로 정렬 (내림차순)
#     sorted_items = sorted(status_items, key=lambda x: x["Status"], reverse=True)
#     highest_status = sorted_items[0]["Status"]
#
#     # 가장 높은 status를 가진 항목들 필터링
#     top_items = [item for item in sorted_items if item["Status"] == highest_status]
#
#     # item 리턴 포맷 구성
#     if len(top_items) == 1:
#         item_label = top_items[0]["Title"]
#     elif len(top_items) == 2:
#         item_label = f"{top_items[0]['Title']}, {top_items[1]['Title']}"
#     else:
#         item_label = f"{top_items[0]['Title']} ... +{len(top_items) - 1}"
#
#
#     return {"status": highest_status, "item": item_label}
#

# @router.get("/getRealTimeCached/{assettype}/{asset}/{channel}")
# @gc_after_large_data(threshold_mb=30)
# async def get_asset_cached(assettype, asset, channel):
#     if channel == 'main' or channel == 'Main':
#         ch = 'Main'
#     else:
#         ch = 'Sub'
#     cache_key = f"SmartAPI:{ch}"
#     # cache_key = f"SmartAPI:{channel}"
#     cache_field = "AssetData"
#     data = None
#     redis_state.client.select(1)
#     # 1. Redis에서 조회
#     try:
#         cached_data = redis_state.client.hget(cache_key, cache_field)
#         if cached_data:
#             data = json.loads(cached_data)
#             print(f"[Redis HIT] AssetData found for {ch}")
#     except Exception as e:
#         print(f"[Redis Error] {e}")
#
#     # 2. Redis에 없으면 API 호출
#     if data is None:
#         try:
#             print(f"[API CALL] Fetching AssetData for {asset}")
#             async with httpx.AsyncClient(timeout=api_timeout) as client:
#                 response = await client.get(f"http://{os_spec.restip}:5000/api/getRealTimeData?name={asset}")
#                 data = response.json()
#
#             # ✅ Redis에 저장 (누락된 부분!)
#             # if data:
#             #     try:
#             #         redis_state.client.hset(cache_key, cache_field, json.dumps(data, ensure_ascii=False))
#             #         print(f"[Redis SAVE] AssetData saved for {ch}")
#             #     except Exception as e:
#             #         print(f"[Redis Save Error] {e}")
#
#         except Exception as e:
#             return {"success": False, "error": f"API call failed: {str(e)}"}
#
#     # 3. 데이터 처리
#     if data and len(data["Data"]) > 0:
#         datalist = []
#
#         if assettype != 'MotorFeed':
#             # Motor 관련 데이터
#             for item in data["Data"]:
#                 if item["Name"] in ["Speed", "Torque"]:
#                     datalist.append({
#                         "Assembly": item["AssemblyID"],
#                         "Title": item["Title"],
#                         "Value": item["Value"],
#                         "Unit": item["Unit"]
#                     })
#         else:
#             # PowerSupply 관련 데이터
#             target_names = ["SwitchingFrequency", "DCLink", "Rectifier"]
#             for item in data["Data"]:
#                 if item["Name"] in target_names:
#                     datalist.append({
#                         "Assembly": item["AssemblyID"],
#                         "Title": item["Title"],
#                         "Value": item["Value"],
#                         "Unit": item["Unit"]
#                     })
#         runhours = get_running(ch)
#
#         return {"success": True, "data": datalist, "runhours":runhours["total"]}
#         # return {"success": True, "data": datalist}
#     else:
#         return {"success": False, "error": "No Data"}
