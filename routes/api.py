from functools import wraps
from fastapi import APIRouter, Request, HTTPException
import os, httpx, re, logging, gc, psutil
import ujson as json
from datetime import datetime, time, timezone, timedelta
from pydantic import BaseModel
from typing import List, Optional
from states.global_state import influx_state, redis_state, os_spec
from collections import defaultdict
from .redismap import RedisMapDetail2, RedisMapped, RedisMapCalibrate
# from .auth import checkLoginAPI
from .RedisBinary import RedisDataType
from .DemandMap import DemandDataFormatter
from .util import is_service_active
from. diagnosis_map import AlarmStatusMatcher
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


async def run_influx_query(func, *args, timeout: int = 30, **kwargs):
    loop = asyncio.get_event_loop()
    executor = get_or_create_executor()

    try:
        # kwargs 처리
        if kwargs:
            from functools import partial
            func = partial(func, **kwargs)

        result = await asyncio.wait_for(
            loop.run_in_executor(executor, func, *args),
            timeout=timeout
        )
        return result

    except asyncio.TimeoutError:
        logging.warning(f"Query timeout after {timeout}s: {func.__name__}")
        raise HTTPException(
            status_code=504,
            detail=f"Query timeout - please try with smaller date range"
        )
    except Exception as e:
        logging.error(f"Query error in {func.__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )


def get_RedisKey(channel, item):
    return f"{item}_{'main' if channel == 'Main' else 'sub'}"


def get_allRedisKey(channel):
    result = dict()
    for group, items in RedisMapped.mapdict.items():
        if channel == 'Main':
            keyname = group + '_main'
        else:
            keyname = group + '_sub'
        result[keyname] = items
    return result


class Trend(BaseModel):
    ParametersIds: List[int]
    StartDate: str
    EndDate: str


class AlarmSearch(BaseModel):
    param: int
    StartDate: str
    EndDate: str


class EventSearch(BaseModel):
    param: str
    StartDate: str
    EndDate: str

class TrendRequest(BaseModel):
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    fields: Optional[List[str]] = None  # 필드 목록


parameter_options = [
    "None",
    "Temperature",
    "Frequency",
    "Phase Voltage L1",
    "Phase Voltage L2",
    "Phase Voltage L3",
    "Phase Voltage Average",
    "Phase Voltage L12",
    "Phase Voltage L23",
    "Phase Voltage L31",
    "Line Voltage Average",
    "Voltage Unbalance(Uo)",
    "Voltage Unbalance(Uu)",
    "Phase Current L1",
    "Phase Current L2",
    "Phase Current L3",
    "Phase Current Average",
    "Phase Current Total",
    "Phase Current Neutral",
    "Active Power L1",
    "Active Power L2",
    "Active Power L3",
    "Active Power Total",
    "Reactive Power L1",
    "Reactive Power L2",
    "Reactive Power L3",
    "Reactive Power Total",
    "D1",
    "D2",
    "D3",
    "D",
    "Apparent Power L1",
    "Apparent Power L2",
    "Apparent Power L3",
    "Apparent Power Total",
    "Power Factor L1",
    "Power Factor L2",
    "Power Factor L3",
    "Power Factor Total",
    "THD Voltage L1",
    "THD Voltage L2",
    "THD Voltage L3",
    "THD Voltage L12",
    "THD Voltage L23",
    "THD Voltage L31",
    "THD Current L1",
    "THD Current L2",
    "THD Current L3"
]


@router.get('/getChannelSetting/{channel}')  # report_info
def getChannelSetting(channel):
    redis_state.client.execute_command("SELECT", 0)
    if redis_state.client.hexists("System", "setup"):
        redisContext = redis_state.client.hget("System", "setup")
        setting = json.loads(redisContext)
    else:
        file_path = os.path.join(SETTING_FOLDER, 'setup.json')
        if not os.path.exists(file_path):
            return {"passOK": "0", "error": "setting file not found"}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    setting = json.load(f)
                except json.JSONDecodeError as e:
                    return {"passOK": "0", "error": f"JSON decode error: {str(e)}"}
        except Exception as e:
            return {"passOK": "0", "error": f"An unexpected error occurred: {str(e)}"}
    if channel in setting:
        print(setting[channel])
        return {"passOK": "1", "data": setting[channel]}
    else:
        # main_channel = [ch for ch in setting["channel"] if ch["channel"] == channel]
        main_channel = next((ch for ch in setting["channel"] if ch.get("channel") == channel), None)
        if not main_channel:
            return {"passOK": "0"}
        else:
            result = {"ct_direction": [main_channel["ctInfo"]["direction"][0], main_channel["ctInfo"]["direction"][1],
                                       main_channel["ctInfo"]["direction"][2]],
                      "ct_inorminal": main_channel["ctInfo"]["inorminal"],
                      "pt_wiringmode": main_channel["ptInfo"]["wiringmode"],
                      "pt_vnorminal": main_channel["ptInfo"]["vnorminal"],
                      "pt_linefrequency": main_channel["ptInfo"]["linefrequency"]}
            return {"passOK": "1", "data": result}


@router.get('/getHarmonics/{channel}')  # get harmonics with redis
def getHarmonics(channel):
    key = get_RedisKey(channel, 'pq')
    try:
        redis_state.client.execute_command("SELECT", 1)
        harms = redis_state.client.hget(key, "harmonics")
        harmdict = json.loads(harms)
        for key in harmdict:
            harmdict[key] = [x / 100 for x in harmdict[key]]
        return {"success": True, "data": harmdict}
    except Exception as e:
        return {"success": False, "error": "Redis Read Error"}


@router.get('/setWave/{channel}/{state}')
def setWave(channel, state):
    key = get_RedisKey(channel, 'pq')
    try:
        redis_state.client.select(1)
        redis_state.client.hset(key, f"setWave", int(state))
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# get harmonics with redis
def getWave(channel):
    key = get_RedisKey(channel, 'pq')
    try:
        redis_state.client.execute_command("SELECT", 9)
        harms = redis_state.client.hget(key, "waveform")
        harmdict = json.loads(harms)
        return {"success": True, "data": harmdict}
    except Exception as e:
        return {"success": False, "error": "Redis Read Error"}


async def get_waveform(channel: str):
    """
    Waveform 데이터 가져오기

    Args:
        channel: 채널 ID (Main/Sub 등)

    Returns:
        파싱된 Waveform 데이터
    """
    try:
        # Redis 키 생성 (실제 키 패턴에 맞게 수정 필요)
        redis_state.binary_client.select(1)
        redis_key = f"pq_{channel.lower()}"
        processor = redis_state.processor
        # 바이너리 데이터 가져오기
        binary_data = processor.get_redis_data(
            key=redis_key,
            data_type=RedisDataType.HASH,
            field='waveform'
        )

        if not binary_data:
            return {
                "success": False,
                "message": f"No waveform data found for channel: {channel}"
            }

        # 데이터 파싱
        parsed_data = processor.parse_data("waveform", binary_data)

        return {
            "success": True,
            "data": parsed_data
        }

    except ValueError as e:
        return {
            "success": False,
            "message": f"Data parsing error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Server error: {str(e)}"
        }


@router.get('/getWave/{channel}')
async def get_waves(channel):
    if os_spec.os == 'Windows':
        result = getWave(channel)
    else:
        result = await get_waveform(channel)

    return result


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

def getSmartData(mode, channel):
    redis_state.client.select(1)
    rkey = f"SmartAPI:{channel}"
    data = redis_state.client.hget(rkey, mode)
    return data

def proc_eventFaultData(datas):
    superNodes = []
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
    ret = {"data_status": statuslist, "data_tree": superlist}
    return ret

def proc_DiagnosisData_optimized(datas):
    import time
    start = time.time()

    # 1. NodeType 집합으로 변환 (O(1) 조회)
    superNodes = {item["NodeType"] for item in datas["BarGraph"]}

    # 2. ParentID로 인덱싱 (O(n) -> O(1) 조회)
    children_by_parent = {}
    for item in datas["TreeList"]:
        parent_id = item["ParentID"]
        if parent_id not in children_by_parent:
            children_by_parent[parent_id] = []
        children_by_parent[parent_id].append(item)

    # 3. superlist 생성 (한 번만 순회)
    superlist = []
    for item in datas["TreeList"]:
        if item["NodeType"] in superNodes:
            superdict = {
                "ID": item["ID"],
                "Name": item["Name"],
                "Title": item["Title"],
                "Titles": item["Titles"],
                "AssemblyID": item["AssemblyID"],
                "Description": item["Description"],
                "Descriptions": item["Descriptions"],
                "Path": item["Path"],
                "Status": item["Status"],
                "Value": item["Value"],
                "isParent": True
            }

            # 4. 자식들 바로 추가 (인덱스 활용)
            if item["ID"] in children_by_parent:
                superdict["children"] = []
                for child in children_by_parent[item["ID"]]:
                    child_dict = {
                        "ID": child["ID"],
                        "Name": child["Name"],
                        "Title": child["Title"],
                        "Titles": child["Titles"],
                        "AssemblyID": child["AssemblyID"],
                        "Description": child["Description"],
                        "Descriptions": child["Descriptions"],
                        "Status": child["Status"],
                        "Value": child["Value"],
                        "NodeType": child["NodeType"],
                        "isSub": child["NodeType"] == 10
                    }

                    # 5. NodeType 10의 자식들 (NodeType 11) 처리
                    if child["NodeType"] == 10 and child["ID"] in children_by_parent:
                        child_dict["children"] = []
                        for subchild in children_by_parent[child["ID"]]:
                            if subchild["NodeType"] == 11:
                                child_dict["children"].append({
                                    "ID": subchild["ID"],
                                    "Name": subchild["Name"],
                                    "Title": subchild["Title"],
                                    "Titles": subchild["Titles"],
                                    "AssemblyID": subchild["AssemblyID"],
                                    "Description": subchild["Description"],
                                    "Descriptions": subchild["Descriptions"],
                                    "Status": subchild["Status"],
                                    "Value": subchild["Value"]
                                })

                    superdict["children"].append(child_dict)

            superlist.append(superdict)

    print(f"Processing time: {time.time() - start:.3f}s")
    return {"data_status": datas["BarGraph"], "data_tree": superlist}

def proc_DiagnosisData(datas):
    superNodes = []
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

    return {"data_status": statuslist, "data_tree": superlist}

@router.get("/getDiagnosisCached/{channel}/{asset}")
@gc_after_large_data(threshold_mb=30)
async def get_diagnosis_cached(channel, asset):
    """
    진단 데이터 조회 - Redis 우선, 없으면 API 호출
    """
    redis_state.client.select(1)
    if channel == 'main' or channel == 'Main':
        chName = 'Main'
    else:
        chName = 'Sub'
    cache_key = f"SmartAPI:{chName}"
    cache_field = "Diagnosis"
    datas = None

    # 1. Redis에서 조회
    try:

        cached_data = redis_state.client.hget(cache_key, cache_field)
        if cached_data:
            datas = json.loads(cached_data)
            print(f"[Redis] Data found for {chName}")
    except Exception as e:
        print(f"[Redis Error] {e}")

    # 2. Redis에 없으면 API 호출
    if datas is None:
        try:
            print(f"[API] Fetching data for {chName}")
            async with httpx.AsyncClient(timeout=api_timeout) as client:
                response = await client.get(f"http://{os_spec.restip}:5000/api/getDiagnostic?name={asset}")
                datas = response.json()

            # API에서 가져온 데이터 Redis에 저장
            if datas:
                try:
                    redis_state.client.hset(cache_key, cache_field, json.dumps(datas, ensure_ascii=False))
                except:
                    pass  # 저장 실패 무시

        except Exception as e:
            return {"success": False, "error": f"Failed to fetch data: {str(e)}"}

    # 3. 데이터 처리 및 반환
    if datas and len(datas) > 0:
        ret = proc_DiagnosisData_optimized(datas)
        return {"success": True, "data_status": ret['data_status'], "data_tree": ret['data_tree']}
    else:
        return {"success": False, "error": "No Data"}

@router.get("/getDiagnosisDetail/{asset}")
@gc_after_large_data(threshold_mb=30)  # Diagnosis Vue : get diagnosis
async def get_diagnosis(asset, request: Request):
    async with httpx.AsyncClient(timeout=api_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getDiagnostic?name={asset}")
        datas = response.json()

    if datas:
        ret = proc_DiagnosisData_optimized(datas)
        return {"success": True, "data_status": ret['data_status'], "data_tree": ret['data_tree']}
    else:
        return {"success": False, "error": "No Data"}


@router.get("/getDiagPQ/{asset}")  # Diagnosis Vue : get diagnosis PQ
@gc_after_large_data(threshold_mb=30)
async def get_diagPQ(asset, request: Request):
    async with httpx.AsyncClient(timeout=api_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getPQ?name={asset}")
        datas = response.json()

    if datas:
        ret = proc_DiagnosisData_optimized(datas)
        return {"success": True, "data_status": ret['data_status'], "data_tree": ret['data_tree']}
    else:
        return {"success": False, "error": "No Data"}

@router.get("/getPQCached/{channel}/{asset}")
@gc_after_large_data(threshold_mb=30)
async def get_PQ_cached(channel, asset):
    """
    진단 데이터 조회 - Redis 우선, 없으면 API 호출
    """
    redis_state.client.select(1)
    if channel == 'main' or channel == 'Main':
        chName = 'Main'
    else:
        chName = 'Sub'
    cache_key = f"SmartAPI:{chName}"
    cache_field = "PQ"
    datas = None

    # 1. Redis에서 조회
    try:

        cached_data = redis_state.client.hget(cache_key, cache_field)
        if cached_data:
            datas = json.loads(cached_data)
    except Exception as e:
        print(f"[Redis Error] {e}")

    # 2. Redis에 없으면 API 호출
    if datas is None:
        try:
            print(f"[API CALL] Fetching PQ data for {asset}")
            async with httpx.AsyncClient(timeout=api_timeout) as client:
                response = await client.get(f"http://{os_spec.restip}:5000/api/getPQ?name={asset}")
                data = response.json()

            # ✅ Redis에 저장 (빠진 부분 추가!)
            if data:
                try:
                    redis_state.client.hset(cache_key, cache_field, json.dumps(data, ensure_ascii=False))
                except Exception as e:
                    pass

        except Exception as e:
            return {"success": False, "error": f"Failed to fetch data: {str(e)}"}

    # 3. 데이터 처리 및 반환
    if datas and len(datas) > 0:
        ret = proc_DiagnosisData_optimized(datas)
        return {"success": True, "data_status": ret['data_status'], "data_tree": ret['data_tree']}
    else:
        return {"success": False, "error": "No Data"}

@router.get("/getFaults/{asset}")  # Diagnosis Vue : get diagnosis
async def get_faults(asset, request: Request):
    async with httpx.AsyncClient(timeout=api_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getFaults?name={asset}")
        datas = response.json()

    if datas:
        ret = proc_eventFaultData(datas)
        return {"success": True, "data_status": ret['data_status'], "data_tree": ret['data_tree']}
    else:
        return {"success": False, "error": "No Data"}

@router.get("/getFaultCached/{channel}/{asset}")
async def get_Fault_cached(channel, asset):
    """
    진단 데이터 조회 - Redis 우선, 없으면 API 호출
    """
    redis_state.client.select(1)
    if channel == 'main' or channel == 'Main':
        chName = 'Main'
    else:
        chName = 'Sub'
    cache_key = f"SmartAPI:{chName}"
    cache_field = "Fault"
    datas = None

    # 1. Redis에서 조회
    try:
        # redis_state.client.select(1)
        cached_data = redis_state.client.hget(cache_key, cache_field)
        if cached_data:
            datas = json.loads(cached_data)
    except Exception as e:
        print(f"[Redis Error] {e}")

    # 2. Redis에 없으면 API 호출
    if datas is None:
        try:
            print(f"[API] Fetching data for {chName}")
            async with httpx.AsyncClient(timeout=api_timeout) as client:
                response = await client.get(f"http://{os_spec.restip}:5000/api/getFaults?name={asset}")
                datas = response.json()

            # API에서 가져온 데이터 Redis에 저장
            if datas:
                try:
                    redis_state.client.hset(cache_key, cache_field, json.dumps(datas, ensure_ascii=False))
                except:
                    pass  # 저장 실패 무시

        except Exception as e:
            return {"success": False, "error": f"Failed to fetch data: {str(e)}"}

    # 3. 데이터 처리 및 반환
    if datas and len(datas) > 0:
        ret = proc_eventFaultData(datas)
        return {"success": True, "data_status": ret['data_status'], "data_tree": ret['data_tree']}
    else:
        return {"success": False, "error": "No Data"}

@router.get("/getEvents/{asset}")  # Diagnosis Vue : get diagnosis
async def get_events(asset, request: Request):
    async with httpx.AsyncClient(timeout=api_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getEvents?name={asset}")
        datas = response.json()
    if datas:
        ret = proc_eventFaultData(datas)
        return {"success": True, "data_status": ret['data_status'], "data_tree": ret['data_tree']}
    else:
        return {"success": False, "error": "No Data"}

@router.get("/getEventsCached/{channel}/{asset}")
async def get_Event_cached(channel, asset):
    """
    진단 데이터 조회 - Redis 우선, 없으면 API 호출
    """
    redis_state.client.select(1)
    if channel == 'main' or channel == 'Main':
        chName = 'Main'
    else:
        chName = 'Sub'
    cache_key = f"SmartAPI:{chName}"
    cache_field = "Event"
    datas = None

    # 1. Redis에서 조회
    try:
        # redis_state.client.select(1)
        cached_data = redis_state.client.hget(cache_key, cache_field)
        if cached_data:
            datas = json.loads(cached_data)
    except Exception as e:
        print(f"[Redis Error] {e}")

    # 2. Redis에 없으면 API 호출
    if datas is None:
        try:
            print(f"[API] Fetching data for {chName}")
            async with httpx.AsyncClient(timeout=api_timeout) as client:
                response = await client.get(f"http://{os_spec.restip}:5000/api/getEvents?name={asset}")
                datas = response.json()

            # API에서 가져온 데이터 Redis에 저장
            if datas:
                try:
                    redis_state.client.hset(cache_key, cache_field, json.dumps(datas, ensure_ascii=False))
                except:
                    pass  # 저장 실패 무시

        except Exception as e:
            return {"success": False, "error": f"Failed to fetch data: {str(e)}"}

    # 3. 데이터 처리 및 반환
    if datas and len(datas) > 0:
        ret = proc_eventFaultData(datas)
        return {"success": True, "data_status": ret['data_status'], "data_tree": ret['data_tree']}
    else:
        return {"success": False, "error": "No Data"}

@router.get("/getTrendParameters/{channel}")
def get_trendParams(channel):
    redis_state.client.execute_command("SELECT", 0)
    if redis_state.client.hexists("System", "setup"):
        dstr = redis_state.client.hget("System", "setup")
        data = json.loads(dstr)
    else:
        try:
            readpath = os.path.join(SETTING_FOLDER, "setup.json")
            with open(readpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError as e:
            print(str(e))
            return {"success": False, "error": "setup file not found"}

    idx = -1
    for i in range(0, len(data["channel"])):
        if data["channel"][i]["channel"] == channel:
            idx = i
            break
    result = data["channel"][idx]["trendInfo"]
    return {"success": True, "data": result}


@router.get("/getParameters/{asset}/{type}")
@gc_after_large_data(threshold_mb=30)
async def get_params(asset, type, request: Request):
    # response = await  http_state.client.get(f"/getTrendHierarchy?name={asset}&type={type}")
    # datas = response.json()
    async with httpx.AsyncClient(timeout=api_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getTrendHierarchy?name={asset}&type={type}")
        datas = response.json()
    #     if response.status_code in [400, 401, 500]:
    #         flag = await checkLoginAPI(request)
    #         if not flag:
    #             return {"success": False, "error": "Restful API Login Failed"}
    #         else:
    #             response = await client.get(
    #                 f"http://{os_spec.restip}:5000/api/getTrendHierarchy?name={asset}&type={type}")
    #             datas = response.json()
    if len(datas) > 0:
        return {"success": True, "data": datas}
    else:
        return {"success": False}


@router.get("/getTrendParameters/{asset}/{type}")  # Diagnosis Vue : get diagnosis PQ
@gc_after_large_data(threshold_mb=30)
async def get_trendParams(asset, type, request: Request):
    # response = await  http_state.client.get(f"/getTrendHierarchy?name={asset}&type={type}")
    # datas = response.json()
    async with httpx.AsyncClient(timeout=api_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getTrendHierarchy?name={asset}&type={type}")
        datas = response.json()
    if len(datas) > 0:
        superlist = []
        for a in range(0, len(datas)):
            superdict = dict()
            superdict["ID"] = datas[a]["ID"]
            superdict["Name"] = datas[a]["Name"]
            superdict["Title"] = datas[a]["Title"]
            superdict["Titles"] = datas[a]["Titles"]
            superdict["Path"] = datas[a]["Path"]
            superdict["AssemblyID"] = datas[a]["AssemblyID"]
            superdict["isParent"] = False
            superdict["isSuper"] = True
            Titles = checkNode(superlist, datas[a]["Name"], datas[a]["AssemblyID"])
            if Titles is True:
                continue
            else:
                superlist.append(superdict)

        sublist = list()

        for j in range(0, len(datas)):
            for i in range(0, len(superlist)):
                if superlist[i]["ID"] == datas[j]["ParentID"]:
                    subdict = dict()
                    subdict["ID"] = datas[j]["ID"]
                    subdict["Name"] = datas[j]["Name"]
                    subdict["Title"] = datas[j]["Title"]
                    subdict["Titles"] = datas[j]["Titles"]
                    subdict["AssemblyID"] = datas[j]["AssemblyID"]
                    if "children" in superlist[i]:
                        superlist[i]["children"].append(subdict)
                    else:
                        superlist[i]["children"] = []
                        superlist[i]["children"].append(subdict)
                    isSuper = False
                    sublist.append(datas[j]["ID"])

        superlist = [item for item in superlist if item["ID"] not in sublist]

    if len(superlist) > 0:
        return {"success": True, "superlist": superlist}
    else:
        return {"success": False, "error": "No Data"}


@router.post("/getTrendData")
@gc_after_large_data(threshold_mb=30)
async def get_trendData(data: Trend, request: Request):
    # response = await  http_state.client.post(f"/getTrendData", json=data.dict())
    # result = response.json()
    async with httpx.AsyncClient(timeout=api_timeout) as client:
        response = await client.post(f"http://{os_spec.restip}:5000/api/getTrendData", json=data.dict())
        result = response.json()
    #     if 'status' in result and result['status'] == 500:
    #         flag = await checkLoginAPI(request)
    #         if not flag:
    #             return {"success": False, "error": "Restful API Login Failed"}
    #         else:
    #             response = await client.post(f"http://{os_spec.restip}:5000/api/getTrendData", json=data.model_dump())
    #             result = response.json()
    #             print(result)
    if len(result) > 0:
        datDict = dict()
        if "Parameters" in result:
            for i in range(0, len(result)):
                if len(result["Parameters"]) > 0:
                    for j in range(0, len(result["Parameters"])):
                        if not result["Parameters"][j]["Title"] in datDict.keys():
                            datDict[result["Parameters"][j]["Title"]] = {
                                "Title": result["Parameters"][j]["Title"],
                                "data": result["Parameters"][j]["Data"]}
                        # if not result["Parameters"][j]["UID"]["Name"] in datDict.keys():
                        #     datDict[result["Parameters"][j]["UID"]["Name"]] = {
                        #         "Title": result["Parameters"][j]["UID"]["Title"], "data": result["Parameters"][j]["Data"]}
                if result["Thresholds"] and len(result["Thresholds"]) > 0:
                    datDict["Thresholds"] = result["Thresholds"]
                else:
                    datDict["Thresholds"] = []
            return {"success": True, "data": datDict, "date":result["LastRecordDateTime"]}
        else:
            return {"success": False, "error": "No Data", "date":""}
    else:
        return {"success": False, "error": "No Data", "date":""}


@router.get("/getDiagnosis/{asset}")  # Report Vue : get Diagnosis
@gc_after_large_data(threshold_mb=30)
async def get_diagnosis(asset, request: Request):
    # response = await  http_state.client.get(f"/getDiagnostic?name={asset}")
    # data = response.json()
    async with httpx.AsyncClient(timeout=api_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getDiagnostic?name={asset}")
        data = response.json()
    #     if response.status_code in [400, 401, 500]:
    #         flag = await checkLoginAPI(request)
    #         if not flag:
    #             return {"success": False, "error": "Restful API Login Failed"}
    #         else:
    #             response = await client.get(f"http://{os_spec.restip}:5000/api/getDiagnostic?name={asset}")
    #             data = response.json()

    if len(data) > 0:
        return {"success": True, "data": data["BarGraph"]}
    else:
        return {"success": False, "error": "No Data"}


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

@router.get("/getStatus/{asset}/{channel}")  # Master Dashboard Status
@gc_after_large_data(threshold_mb=30)
async def getStatus(asset, channel):
    try:
        # 1. API에서 진단 데이터 가져오기
        async with httpx.AsyncClient(timeout=api_timeout) as client:
            response = await client.get(f"http://{os_spec.restip}:5000/api/getDiagnostic?name={asset}")
            data = response.json()

        # 2. Redis에서 DashAlarms 설정 가져오기
        redis_state.client.select(0)
        redis_data = redis_state.client.hget("Equipment", "DashAlarms")

        # 설정이 없으면 기존 로직 사용
        if not redis_data:
            return await getStatus_legacy(data, channel)

        dash_alarms = json.loads(redis_data)
        channel_config = dash_alarms.get(channel)

        # 해당 채널 설정이 없으면 기존 로직 사용
        if not channel_config:
            return await getStatus_legacy(data, channel)

        if not channel_config.get("diagnosis"):
            return await getStatus_legacy(data, channel)

    except Exception as e:
        print(str(e))
        runhours = get_running(channel)["total"]
        return {"status": -1, "runhours": runhours}

    runhours = get_running(channel)["total"]

    # 데이터 검증
    if not data or not isinstance(data, dict):
        return {"status": -1, "runhours": runhours}

    bar_graph = data.get("BarGraph", [])
    if not bar_graph:
        return {"status": 0, "runhours": runhours}

    # 3. AlarmStatusMatcher로 진단 계산
    try:
        alarm_matcher = AlarmStatusMatcher()
        status_info = {
            "diagnosis": channel_config.get("diagnosis", []),
            "pq": channel_config.get("pq", [])
        }

        result = alarm_matcher.diagnose(status_info, bar_graph)
        final_status = result["final_status"]

        return {"status": final_status, "runhours": runhours}

    except Exception as e:
        print(f"AlarmStatusMatcher error: {str(e)}")
        # 에러 시 기존 로직으로 fallback
        return await getStatus_legacy(data, channel)


async def getStatus_legacy(data, channel):
    """기존 로직 (fallback용)"""
    runhours = get_running(channel)["total"]

    if not data or not isinstance(data, dict):
        return {"status": -1, "runhours": runhours}

    status_list = [item["Status"] for item in data.get("BarGraph", []) if "Status" in item]

    # 모든 값이 1이면 "OK"
    if all(status == 1 for status in status_list):
        return {"status": 1, "runhours": runhours}

    # 모든 값이 0이면 "No Data"
    if all(status == 0 for status in status_list):
        return {"status": 0, "runhours": runhours}

    # 우선순위: Repair(4) > Inspect(3) > Warning(2)
    if 4 in status_list:
        return {"status": 4, "runhours": runhours}
    elif 3 in status_list:
        return {"status": 3, "runhours": runhours}
    elif 2 in status_list:
        return {"status": 2, "runhours": runhours}
    elif 1 in status_list:
        return {"status": 1, "runhours": runhours}
    else:
        return {"status": -2, "runhours": runhours}

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


@router.get("/getPQStatus/{asset}/{channel}")  # Master Dashboard PQ Status
@gc_after_large_data(threshold_mb=30)
async def getPQStatus(asset, channel, request: Request):
    try:
        # 1. API에서 PQ 데이터 가져오기
        async with httpx.AsyncClient(timeout=api_timeout) as client:
            response = await client.get(f"http://{os_spec.restip}:5000/api/getPQ?name={asset}")
            data = response.json()

        # 2. Redis에서 DashAlarms 설정 가져오기
        redis_state.client.select(0)
        redis_data = redis_state.client.hget("Equipment", "DashAlarms")

        # 설정이 없으면 기존 로직 사용
        if not redis_data:
            return await getPQStatus_legacy(data)

        dash_alarms = json.loads(redis_data)
        channel_config = dash_alarms.get(channel)

        # 해당 채널 설정이 없으면 기존 로직 사용
        if not channel_config:
            return await getPQStatus_legacy(data)

        if not channel_config.get("pq"):
            return await getPQStatus_legacy(data, channel)

    except Exception as e:
        return {"status": -1}

    # 데이터 검증
    if not data or not isinstance(data, dict):  # ✅ 딕셔너리 체크
        return {"status": -1}

    bar_graph = data.get("BarGraph", [])
    if not bar_graph:
        return {"status": -2}

    # 3. AlarmStatusMatcher로 PQ 계산
    try:
        matcher = AlarmStatusMatcher()
        status_info = {
            "diagnosis": [],  # PQ만 계산
            "pq": channel_config.get("pq", [])
        }

        result = matcher.diagnose(status_info, bar_graph)
        final_status = result["final_status"]
        matched_params = result["matched_parameters"]

        # 매칭된 항목이 없으면
        if not matched_params:
            return {"status": 1, "item": "All"}

        # 매칭된 항목들 중 가장 높은 status들만
        max_status = max(p["actual_status"] for p in matched_params)
        top_items = [p for p in matched_params if p["actual_status"] == max_status]

        # item 리턴 포맷 구성
        if len(top_items) == 1:
            item_label = top_items[0]["name"]
        elif len(top_items) == 2:
            item_label = f"{top_items[0]['name']}, {top_items[1]['name']}"
        else:
            item_label = f"{top_items[0]['name']} ... +{len(top_items) - 1}"

        return {"status": final_status, "item": item_label}

    except Exception as e:
        print(f"AlarmStatusMatcher error: {str(e)}")
        # 에러 시 기존 로직으로 fallback
        return await getPQStatus_legacy(data)


async def getPQStatus_legacy(data):
    """기존 로직 (fallback용)"""
    if not data or not isinstance(data, dict):  # ✅ 딕셔너리 체크
        return {"status": -1}

    status_items = [
        {"Title": item["Title"], "Status": item["Status"]}
        for item in data.get("BarGraph", [])
        if "Status" in item and "Title" in item
    ]

    if not status_items:
        return {"status": -2}

    # 모든 값이 0이면 "No Data"
    if all(item["Status"] == 0 for item in status_items):
        return {"status": 0, "item": "All"}

    if all(item["Status"] == 1 for item in status_items):
        return {"status": 1, "item": "All"}

    # 상태가 높은 순으로 정렬 (내림차순)
    sorted_items = sorted(status_items, key=lambda x: x["Status"], reverse=True)
    highest_status = sorted_items[0]["Status"]

    # 가장 높은 status를 가진 항목들 필터링
    top_items = [item for item in sorted_items if item["Status"] == highest_status]

    # item 리턴 포맷 구성
    if len(top_items) == 1:
        item_label = top_items[0]["Title"]
    elif len(top_items) == 2:
        item_label = f"{top_items[0]['Title']}, {top_items[1]['Title']}"
    else:
        item_label = f"{top_items[0]['Title']} ... +{len(top_items) - 1}"

    return {"status": highest_status, "item": item_label}

# @router.get("/getPQStatus/{asset}")  # Master Dashboard Status
# @gc_after_large_data(threshold_mb=30)
# async def getPQStatus(asset, request: Request):
#     try:
#         # response = await  http_state.client.get(f"/getPQ?name={asset}")
#         # data = response.json()
#         async with httpx.AsyncClient(timeout=api_timeout) as client:
#             response = await client.get(f"http://{os_spec.restip}:5000/api/getPQ?name={asset}")
#             data = response.json()  # JSON 데이터 파싱
#         #     if response.status_code in [400, 401, 500]:
#         #         flag = await checkLoginAPI(request)
#         #         if not flag:
#         #             return {"success": False, "error": "Restful API Login Failed"}
#         #         else:
#         #             response = await client.get(f"http://{os_spec.restip}:5000/api/getPQ?name={asset}")
#         #             data = response.json()  # JSON 데이터 파싱
#     except Exception as e:
#         return {"status": -1}
#
#     # success가 True인지 확인
#     if len(data) == 0:
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
#     return {"status": highest_status, "item": item_label}
#

def get_running(channel):
    if channel == 'Main':
        redisKey = 'runhour_main'
    else:
        redisKey = 'runhour_sub'
    if redis_state.client.exists(redisKey):
        total = redis_state.client.hget(redisKey, "tot")
        current = redis_state.client.hget(redisKey, "cur")
        return {"total": total, "current": current}
    else:
        return {"total": 0, "current": 0}


@router.get("/getRealTimeCached/{assettype}/{asset}/{channel}")
@gc_after_large_data(threshold_mb=30)
async def get_asset_cached(assettype, asset, channel):
    if channel == 'main' or channel == 'Main':
        ch = 'Main'
    else:
        ch = 'Sub'
    cache_key = f"SmartAPI:{ch}"
    # cache_key = f"SmartAPI:{channel}"
    cache_field = "AssetData"
    data = None
    redis_state.client.select(1)
    # 1. Redis에서 조회
    try:
        cached_data = redis_state.client.hget(cache_key, cache_field)
        if cached_data:
            data = json.loads(cached_data)
            print(f"[Redis HIT] AssetData found for {ch}")
    except Exception as e:
        print(f"[Redis Error] {e}")

    # 2. Redis에 없으면 API 호출
    if data is None:
        try:
            print(f"[API CALL] Fetching AssetData for {asset}")
            async with httpx.AsyncClient(timeout=api_timeout) as client:
                response = await client.get(f"http://{os_spec.restip}:5000/api/getRealTimeData?name={asset}")
                data = response.json()

            # ✅ Redis에 저장 (누락된 부분!)
            # if data:
            #     try:
            #         redis_state.client.hset(cache_key, cache_field, json.dumps(data, ensure_ascii=False))
            #         print(f"[Redis SAVE] AssetData saved for {ch}")
            #     except Exception as e:
            #         print(f"[Redis Save Error] {e}")

        except Exception as e:
            return {"success": False, "error": f"API call failed: {str(e)}"}

    # 3. 데이터 처리
    if data and len(data["Data"]) > 0:
        datalist = []

        if assettype != 'MotorFeed':
            # Motor 관련 데이터
            for item in data["Data"]:
                if item["Name"] in ["Speed", "Torque"]:
                    datalist.append({
                        "Assembly": item["AssemblyID"],
                        "Title": item["Title"],
                        "Value": item["Value"],
                        "Unit": item["Unit"]
                    })
        else:
            # PowerSupply 관련 데이터
            target_names = ["SwitchingFrequency", "DCLink", "Rectifier"]
            for item in data["Data"]:
                if item["Name"] in target_names:
                    datalist.append({
                        "Assembly": item["AssemblyID"],
                        "Title": item["Title"],
                        "Value": item["Value"],
                        "Unit": item["Unit"]
                    })
        runhours = get_running(ch)

        return {"success": True, "data": datalist, "runhours":runhours["total"]}
        # return {"success": True, "data": datalist}
    else:
        return {"success": False, "error": "No Data"}

@router.get("/getRealTime/{assettype}/{asset}")  # Diagnosis, Report Vue : get Asset info
@gc_after_large_data(threshold_mb=30)
async def get_asset(assettype, asset, request: Request):
    # response = await  http_state.client.get(f"/getRealTimeData?name={asset}")
    # data = response.json()
    async with httpx.AsyncClient(timeout=api_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getRealTimeData?name=" + asset)
        data = response.json()
    #     if response.status_code in [400, 401, 500]:
    #         flag = await checkLoginAPI(request)
    #         if not flag:
    #             return {"success": False, "error": "Restful API Login Failed"}
    #         else:
    #             response = await client.get(f"http://{os_spec.restip}:5000/api/getRealTimeData?name=" + asset)
    #             data = response.json()
    if data:
        datalist = list()
        if assettype != 'MotorFeed' and assettype != 'PSupply':
            # Motor 관련 데이터
            for item in data["Data"]:
                if item["Name"] in ["Speed", "Torque"]:
                    datalist.append({
                        "Assembly": item["AssemblyID"],
                        "Title": item["Title"],
                        "Value": item["Value"],
                        "Unit": item["Unit"]
                    })
        else:
            # PowerSupply 관련 데이터
            if assettype == 'MotorFeed':
                target_names = ["SwitchingFrequency", "DCLink", "Rectifier"]
                for item in data["Data"]:
                    if item["Name"] in target_names:
                        datalist.append({
                            "Assembly": item["AssemblyID"],
                            "Title": item["Title"],
                            "Value": item["Value"],
                            "Unit": item["Unit"]
                        })
        return {"success": True, "data": datalist}
    else:
        return {"success": False, "error": "No Data"}

@router.get("/getRealTimeSingle/{channel}/{assettype}/{asset}")  # Diagnosis, Report Vue : get Asset info
@gc_after_large_data(threshold_mb=30)
async def get_asset(channel,assettype, asset):

    async with httpx.AsyncClient(timeout=api_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getRealTimeData?name=" + asset)
        data = response.json()
    if data:
        datalist = list()
        if assettype != 'MotorFeed' and assettype != 'PSupply':
            # Motor 관련 데이터
            for item in data["Data"]:
                if item["Name"] in ["Speed", "Torque"]:
                    datalist.append({
                        "Assembly": item["AssemblyID"],
                        "Title": item["Title"],
                        "Value": item["Value"],
                        "Unit": item["Unit"]
                    })
        else:
            # PowerSupply 관련 데이터
            if assettype == 'MotorFeed':
                target_names = ["SwitchingFrequency", "DCLink", "Rectifier"]
                for item in data["Data"]:
                    if item["Name"] in target_names:
                        datalist.append({
                            "Assembly": item["AssemblyID"],
                            "Title": item["Title"],
                            "Value": item["Value"],
                            "Unit": item["Unit"]
                        })
        runhours = get_running(channel)["total"]
        return {"success": True, "data": datalist,"runhours":runhours}
    else:
        return {"success": False, "error": "No Data"}


@router.get("/getAsset/{asset}")  # Diagnosis, Report Vue : get Asset info
async def get_asset(asset, request: Request):
    # response = await  http_state.client.get(f"/getNameplate?name={asset}")
    # data = response.json()
    async with httpx.AsyncClient(timeout=api_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getNameplate?name=" + asset)
        data = response.json()
    #     if response.status_code in [400, 401, 500]:
    #         flag = await checkLoginAPI(request)
    #         if not flag:
    #             return {"success": False, "error": "Restful API Login Failed"}
    #         else:
    #             response = await client.get(f"http://{os_spec.restip}:5000/api/getNameplate?name=" + asset)
    #             data = response.json()
    if len(data) > 0:
        datalist = list()
        redis_state.client.execute_command("SELECT", 0)
        setupJson = redis_state.client.hget("System", "setup")
        setting = json.loads(setupJson)
        mac = setting["General"]["deviceInfo"]["mac_address"]
        # main_channel_data = next((ch for ch in setting["channel"] if ch.get("channel") == "Main"), None)
        transformer_channel = next(
            (ch for ch in setting["channel"] if ch.get("assetInfo", {}).get("name") == asset),
            None
        )

        if transformer_channel:
            pt_info = transformer_channel.get("ptInfo")
            assetType = transformer_channel["assetInfo"]["type"]
            n_kva = transformer_channel.get("n_kva")
            datalist.append(
                {"Title": "PT WiringMode", "Name": "PT_WiringMode", "Value": ptInfo[pt_info['wiringmode']], "Unit": ""})
            if int(n_kva) > 0 and assetType == 'Transformer':
                datalist.append({"Title": "Rated KVA", "Name": "RatedKVA", "Value": int(n_kva), "Unit": "kVA"})

        for i in range(0, len(data)):
            if data[i]["Name"] == "RatedVoltage":
                datalist.append({"Title": data[i]["Title"], "Name": data[i]["Name"], "Value": data[i]["Value"],
                                 "Unit": data[i]["Unit"]})
            elif data[i]["Name"] == "RatedFrequency":
                datalist.append({"Title": data[i]["Title"], "Name": data[i]["Name"], "Value": data[i]["Value"],
                                 "Unit": data[i]["Unit"]})
            elif data[i]["Name"] == "RatedCurrent":
                datalist.append({"Title": data[i]["Title"], "Name": data[i]["Name"], "Value": data[i]["Value"],
                                 "Unit": data[i]["Unit"]})
        return {"success": True, "data": datalist, "mac": mac}
    else:
        return {"success": False, "error": "No Data"}


def getAlarmCondition(channel):
    key = get_RedisKey(channel, 'alarm')
    redis_state.client.execute_command("SELECT", 9)
    if redis_state.client.exists(key):
        try:
            harms = redis_state.client.hget(key, "alarm")
            harmdict = json.loads(harms)
            channel_list = [entry["channel"] for entry in harmdict]
            return channel_list
        except Exception as e:
            return []
    else:
        return []


def refactor_alarm(channel, data, output, patStr, type):
    log_dict = {}
    pattern = re.compile(patStr)

    for key, value in data.items():
        match = pattern.match(key)
        if match:
            index = int(match.group(1))
            field = match.group(2)

            if index not in log_dict:
                log_dict[index] = {}

            log_dict[index][field] = value

    # conditions 리스트 얻기
    conditions = getAlarmCondition(channel)

    # 정렬해서 Alarm Log 구성
    for idx in sorted(log_dict.keys()):
        log = log_dict[idx]
        # channel 값이 숫자인 경우 → conditions에서 문자열로 대체
        raw_channel = log.get("channel")
        if isinstance(raw_channel, int):
            if 0 <= raw_channel < len(conditions):
                log["channel"] = conditions[raw_channel]
            else:
                log["channel"] = "Unknown"

        output[type].append(log)
    return output


def iso_to_timestamp(iso_string):
    """
    ISO format string을 Unix timestamp로 변환
    timezone 정보가 없으면 로컬 시간으로 가정
    """
    if iso_string.endswith('Z'):
        # Z로 끝나는 경우 UTC로 처리
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    elif '+' in iso_string or iso_string[-6] == '+' or iso_string[-6] == '-':
        # timezone 정보가 있는 경우 (예: +09:00, -05:00)
        dt = datetime.fromisoformat(iso_string)
    else:
        # timezone 정보가 없는 경우 - 로컬 시간으로 가정
        naive_dt = datetime.fromisoformat(iso_string)
        # 로컬 timezone을 추가
        local_tz = datetime.now().astimezone().tzinfo
        dt = naive_dt.replace(tzinfo=local_tz)

    return int(dt.timestamp())


def get_local_timezone():
    """시스템의 로컬 timezone 객체 반환"""
    return datetime.now().astimezone().tzinfo


def iso_to_utc_string(iso_string):
    """
    ISO format string을 UTC ISO string으로 변환
    timezone 정보가 없으면 로컬 시간으로 가정
    """
    if not iso_string:
        return None

    if iso_string.endswith('Z'):
        # 이미 UTC
        return iso_string
    elif '+' in iso_string or '-' in iso_string[-6:]:
        # timezone 정보가 있는 경우
        dt = datetime.fromisoformat(iso_string)
        utc_dt = dt.astimezone(timezone.utc)
        return utc_dt.isoformat().replace('+00:00', 'Z')
    else:
        # timezone 정보가 없는 경우 - 로컬 시간으로 가정
        naive_dt = datetime.fromisoformat(iso_string)
        local_tz = datetime.now().astimezone().tzinfo
        dt = naive_dt.replace(tzinfo=local_tz)
        utc_dt = dt.astimezone(timezone.utc)
        return utc_dt.isoformat().replace('+00:00', 'Z')


def getITIC_data(measurement: str, channel: str, ):
    local_tz = datetime.now().astimezone().tzinfo
    start_dt = datetime.now(local_tz) - timedelta(days=90)
    start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    startdate = start_dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
    enddate = datetime.now(local_tz).astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
    query = f'''
    from(bucket: "ntek")
      |> range(start: time(v: "{startdate}"), stop: time(v: "{enddate}"))
      |> filter(fn: (r) => r._measurement == "{measurement}")
      |> filter(fn: (r) => r.channel == "{channel}")
      |> filter(fn: (r) => r.event_type == "SAG" or r.event_type == "SWELL" or r.event_type == "SHORT INTERUPT" or r.event_type == "LONG INTERUPT")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> map(fn: (r) => ({{ r with time: r._time }}))
      |> group(columns: ["_measurement", "channel"])
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: 32)
    '''
    result = influx_state.query_api.query(query)

    rows = [record.values for table in result for record in table.records]
    for row in rows:
        if 'time' not in row and '_time' in row:
            row['time'] = row['_time']

    return rows


def count_influx_records_optimized(measurement: str, channel: str, page_size: int = 10):
    """count() 함수를 사용하여 DB에서 직접 카운트"""
    startdate = "1970-01-01T00:00:00Z"

    # 로컬 시간 기준 현재 시간을 UTC로 변환
    local_tz = get_local_timezone()
    enddate = datetime.now(local_tz).astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')

    # 카운트만 가져오는 쿼리
    query = f'''
    from(bucket: "ntek")
      |> range(start: time(v: "{startdate}"), stop: time(v: "{enddate}"))
      |> filter(fn: (r) => r._measurement == "{measurement}")
      |> filter(fn: (r) => r["channel"] == "{channel}")
      |> group(columns: ["_measurement"])
      |> count()
    '''

    result = influx_state.query_api.query(query)

    # 카운트 결과 추출
    total_records = 0
    for table in result:
        for record in table.records:
            # 각 필드별 카운트가 나오므로 가장 큰 값 사용
            count_value = record.get_value()
            if count_value > total_records:
                total_records = count_value

    # 만약 count()가 제대로 동작하지 않으면 대체 방법
    if total_records == 0:
        # distinct time 값만 가져오기
        query_alt = f'''
        from(bucket: "ntek")
          |> range(start: time(v: "{startdate}"), stop: time(v: "{enddate}"))
          |> filter(fn: (r) => r._measurement == "{measurement}")
          |> filter(fn: (r) => r["channel"] == "{channel}")
          |> keep(columns: ["_time"])
          |> group()
          |> distinct(column: "_time")
          |> count()
        '''

        result_alt = influx_state.query_api.query(query_alt)
        for table in result_alt:
            for record in table.records:
                total_records = record.get_value()
                break

    total_pages = (total_records + page_size - 1) // page_size

    return {
        "total_records": total_records,
        "total_pages": total_pages,
        "page_size": page_size
    }


def count_search_records_optimized(measurement: str, channel: str, param: int,
                                   startdate: str, enddate: str, page_size: int = 10):
    """최적화된 검색 카운트 - 사용자 입력도 로컬→UTC 변환"""
    local_tz = datetime.now().astimezone().tzinfo

    # startdate 처리
    if startdate:
        # 사용자 입력을 로컬 시간으로 가정하고 UTC로 변환
        startdate = iso_to_utc_string(startdate)
    else:
        # 로컬 시간 기준 90일 전을 UTC로 변환
        start_dt = datetime.now(local_tz) - timedelta(days=90)
        start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        startdate = start_dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')

    # enddate 처리
    if enddate:
        # 사용자 입력을 로컬 시간으로 가정하고 UTC로 변환
        enddate = iso_to_utc_string(enddate)
    else:
        # 로컬 시간 기준 현재를 UTC로 변환
        enddate = datetime.now(local_tz).astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')

    # 필터 조건 구성
    filter_conditions = [
        f'r._measurement == "{measurement}"',
        f'r.channel == "{channel}"'
    ]

    if param > 0:
        filter_conditions.append(f'r.chan == "{str(param)}"')

    combined_filter = " and ".join(filter_conditions)

    query = f'''
    from(bucket: "ntek")
      |> range(start: time(v: "{startdate}"), stop: time(v: "{enddate}"))
      |> filter(fn: (r) => {combined_filter})
      |> group(columns: ["_measurement"])
      |> count()
    '''

    result = influx_state.query_api.query(query)

    total_records = 0
    for table in result:
        for record in table.records:
            count_value = record.get_value()
            if count_value > total_records:
                total_records = count_value

    total_pages = (total_records + page_size - 1) // page_size

    return {
        "total_records": total_records,
        "total_pages": total_pages,
        "page_size": page_size
    }


def count_search_records_event_optimized(measurement: str, channel: str, param: str,
                                         startdate: str, enddate: str, page_size: int = 10):
    """이벤트 검색 카운트 최적화 - 사용자 입력도 로컬→UTC 변환"""
    local_tz = datetime.now().astimezone().tzinfo

    # startdate 처리
    if startdate:
        # 사용자 입력을 로컬 시간으로 가정하고 UTC로 변환
        startdate = iso_to_utc_string(startdate)
    else:
        # 로컬 시간 기준 90일 전을 UTC로 변환
        start_dt = datetime.now(local_tz) - timedelta(days=90)
        start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        startdate = start_dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')

    # enddate 처리
    if enddate:
        # 사용자 입력을 로컬 시간으로 가정하고 UTC로 변환
        enddate = iso_to_utc_string(enddate)
    else:
        # 로컬 시간 기준 현재를 UTC로 변환
        enddate = datetime.now(local_tz).astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')

    # 필터 조건 구성
    filter_conditions = [
        f'r._measurement == "{measurement}"',
        f'r.channel == "{channel}"'
    ]

    if param:
        filter_conditions.append(f'r.event_type == "{param}"')

    combined_filter = " and ".join(filter_conditions)

    query = f'''
    from(bucket: "ntek")
      |> range(start: time(v: "{startdate}"), stop: time(v: "{enddate}"))
      |> filter(fn: (r) => {combined_filter})
      |> group(columns: ["_measurement"])
      |> count()
    '''

    result = influx_state.query_api.query(query)

    total_records = 0
    for table in result:
        for record in table.records:
            count_value = record.get_value()
            if count_value > total_records:
                total_records = count_value

    total_pages = (total_records + page_size - 1) // page_size

    return {
        "total_records": total_records,
        "total_pages": total_pages,
        "page_size": page_size
    }


def query_paged_search(measurement: str, channel: str, param: int,
                       startdate: str, enddate: str,
                       page: int = 1, page_size: int = 10):
    """
    로컬 시간대 기준으로 검색
    """
    offset = (page - 1) * page_size

    # 로컬 timezone 가져오기
    local_tz = get_local_timezone()

    # startdate 처리
    if startdate:
        startdate_ts = iso_to_timestamp(startdate)
    else:
        # 로컬 시간 기준 90일 전
        start_dt = datetime.now(local_tz) - timedelta(days=90)
        start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        startdate_ts = int(start_dt.timestamp())

    # enddate 처리
    if enddate:
        enddate_ts = iso_to_timestamp(enddate)
    else:
        # 로컬 시간 기준 오늘 23:59:59
        now_local = datetime.now(local_tz)
        end_of_day = datetime.combine(
            now_local.date(),
            time(23, 59, 59, 999999),
            tzinfo=local_tz
        )
        enddate_ts = int(end_of_day.timestamp())

    # 필터 결합
    filter_conditions = [
        f'r._measurement == "{measurement}"',
        f'r.channel == "{channel}"'
    ]
    if param > 0:
        filter_conditions.append(f'r.chan == "{str(param)}"')

    combined_filter = " and ".join(filter_conditions)

    # 쿼리 실행
    query = f'''
    from(bucket: "ntek")
      |> range(start: {startdate_ts}, stop: {enddate_ts})
      |> filter(fn: (r) => {combined_filter})
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: {page_size}, offset: {offset})
      |> map(fn: (r) => ({{ r with time: r._time }}))
    '''

    result = influx_state.query_api.query(query)
    rows = [record.values for table in result for record in table.records]

    return rows


def query_paged_search_event(measurement: str, channel: str, param: str,
                             startdate: str, enddate: str,
                             page: int = 1, page_size: int = 10):
    """
    이벤트 검색 - 로컬 시간대 기준 (수정 필요한 부분)
    """
    offset = (page - 1) * page_size
    local_tz = datetime.now().astimezone().tzinfo

    # startdate 처리
    if startdate:
        # 사용자 입력을 로컬→UTC 변환
        startdate = iso_to_utc_string(startdate)
    else:
        startdate = "1970-01-01T00:00:00Z"

    # enddate 처리
    if enddate:
        # 사용자 입력을 로컬→UTC 변환
        enddate = iso_to_utc_string(enddate)
    else:
        # 로컬 시간 기준 오늘 23:59:59를 UTC로 변환
        end_of_day = datetime.combine(
            datetime.now(local_tz).date(),
            time(23, 59, 59, 999999),
            tzinfo=local_tz
        )
        enddate = end_of_day.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')

    # 파라미터 필터
    if param != 'All':
        filter_clause = f'|> filter(fn: (r) => r.event_type == "{param}")'
    else:
        filter_clause = ''

    query = f'''
    from(bucket: "ntek")
      |> range(start: time(v: "{startdate}"), stop: time(v: "{enddate}"))
      |> filter(fn: (r) => r._measurement == "{measurement}")
      |> filter(fn: (r) => r.channel == "{channel}")
      {filter_clause}
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> map(fn: (r) => ({{ r with time: r._time }}))
      |> group(columns: ["_measurement", "channel"])
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: {page_size}, offset: {offset})
    '''
    print(query)
    result = influx_state.query_api.query(query)
    rows = [record.values for table in result for record in table.records]

    for row in rows:
        if 'time' not in row and '_time' in row:
            row['time'] = row['_time']

    return rows


def query_influx_pages(measurement: str, channel: str, timefield: str,
                       page: int = 1, page_size: int = 10, days_limit: int = 30):
    """
    로컬 시간대 기준 최근 N일 조회
    """
    offset = (page - 1) * page_size

    # 로컬 timezone 가져오기
    local_tz = get_local_timezone()

    # 로컬 시간 기준 날짜 계산
    enddate_local = datetime.now(local_tz)
    startdate_local = enddate_local - timedelta(days=days_limit)

    # 타임스탬프로 변환
    start_ts = int(startdate_local.timestamp())
    end_ts = int(enddate_local.timestamp())

    query = f'''
    from(bucket: "ntek")
      |> range(start: {start_ts}, stop: {end_ts})
      |> filter(fn: (r) => r._measurement == "{measurement}")
      |> filter(fn: (r) => r.channel == "{channel}")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> map(fn: (r) => ({{ r with time: r._time }}))
      |> group(columns: ["_measurement", "channel"])  
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: {page_size}, offset: {offset})
    '''

    result = influx_state.query_api.query(query)
    rows = [record.values for table in result for record in table.records]

    for row in rows:
        if 'time' not in row and '_time' in row:
            row['time'] = row['_time']

    return rows


def format_influx_time(dt: datetime, to_local: bool = True) -> str:
    # 입력 데이터 타입 처리
    if isinstance(dt, float):
        dt = datetime.fromtimestamp(dt)
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))  # ISO 문자열 → datetime 객체

    # timezone이 없으면 UTC로 가정
    # if dt.tzinfo is None:
    #     dt = dt.replace(tzinfo=pytz.UTC)

    # 로컬 시간으로 변환
    if to_local:
        dt = dt.astimezone()  # 시스템의 로컬 시간대로 자동 변환

    # 포맷팅
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_influx_militime(dt: datetime, to_local: bool = True) -> str:
    # 입력 데이터 타입 처리
    if isinstance(dt, float):
        dt = datetime.fromtimestamp(dt)
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))  # ISO 문자열 → datetime 객체

    # 로컬 시간으로 변환
    if to_local:
        dt = dt.astimezone()  # 시스템의 로컬 시간대로 자동 변환

    # 포맷팅 - 밀리초 3자리 포함
    # %f는 마이크로초(6자리)를 반환하므로 처음 3자리만 사용
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


@router.get("/getAlarmParms/{channel}")
def get_almParms(channel):
    redis_state.client.execute_command("SELECT", 0)
    alm_setup = {}
    if redis_state.client.hexists("System", "setup"):
        sets = redis_state.client.hget("System", "setup")
        setting = json.loads(sets)
        for dict in setting["channel"]:
            if dict["channel"] == channel:
                alm_setup = dict["alarm"]
                break
    if len(alm_setup) == 0:
        return {"success": False}
    paramList = []
    for i in range(1, 33):
        idx = alm_setup[str(i)][0]
        if idx != 0:
            entry = {"id": idx, "label": parameter_options[idx]}
            if entry not in paramList:
                paramList.append(entry)

    return {"success": True, "data": paramList}


def convert_inequality_to_text(condition_str):
    # > 를 Over로 변환
    result = condition_str.replace('>', ' Over ')
    result = result.replace('<', ' Under ')

    result = ' '.join(result.split())

    return result


async def run_with_timeout(func, *args, timeout=30, **kwargs):
    """타임아웃이 있는 비동기 실행"""
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(executor, func, *args, **kwargs),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Query timeout - too much data")


@router.get("/getAlarms/{channel}/{page}")
@gc_after_large_data(threshold_mb=30)
async def get_alarms(channel: str, page: int):
    """최적화된 알람 조회 - 단일 쿼리"""
    try:
        page = int(page)

        # 11개 조회 (10개 + 다음 페이지 확인용)
        result = await run_influx_query(
            query_influx_pages,
            "alarms", channel, "time", page, 11,  # page_size=11
            timeout=20
        )

        # 다음 페이지 존재 여부 확인
        has_next = len(result) > 10
        if has_next:
            result = result[:10]  # 10개만 사용

        # 데이터 포맷팅
        for i in range(len(result)):
            if os_spec.os == 'Windows':
                result[i]["condition_str"] = convert_inequality_to_text(result[i]["condition_str"])
                result[i]["alarm_ts"] = format_influx_time(result[i]["alarm_ts"])
            else:
                result[i]["condition_str"] = f"{result[i]['chan_text']} {result[i]['condition']} {result[i]['level']}"
                result[i]["alarm_ts"] = format_influx_time(result[i]["time"])

        return {
            "success": True,
            "data": result,
            "page": page,
            "hasNext": has_next,
            "hasPrev": page > 1,
            # 하위 호환성
            "totalRecord": -1,
            "totalPages": -1
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error in get_alarms: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": [],
            "page": page,
            "hasNext": False,
            "hasPrev": False,
            "totalRecord": 0,
            "totalPages": 0
        }


@router.post("/getAlarmSearch/{channel}/{page}")
async def get_alarmSearch(data: AlarmSearch, channel: str, page: int):
    """최적화된 알람 검색 - 단일 쿼리"""
    try:
        page = int(page)

        # 11개 조회 (10개 + 다음 페이지 확인용)
        result = await run_influx_query(
            query_paged_search,
            "alarms", channel, data.param,
            data.StartDate, data.EndDate, page, 11,  # page_size=11 추가
            timeout=20
        )

        # 다음 페이지 존재 여부 확인
        has_next = len(result) > 10
        if has_next:
            result = result[:10]  # 10개만 사용

        # 포맷팅
        for i in range(len(result)):
            result[i]["condition_str"] = f"{result[i]['chan_text']} {result[i]['condition']} {result[i]['level']}"
            result[i]["alarm_ts"] = format_influx_time(result[i]["time"])

        return {
            "success": True,
            "data": result,
            "page": page,
            "hasNext": has_next,
            "hasPrev": page > 1,
            # 하위 호환성
            "totalRecord": -1,
            "totalPages": -1
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in get_alarmSearch: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": [],
            "page": page,
            "hasNext": False,
            "hasPrev": False,
            "totalRecord": 0,
            "totalPages": 0
        }


@router.get("/getEventlist/{channel}/{page}")
@gc_after_large_data(threshold_mb=30)
async def get_eventlist(channel: str, page: int):
    """최적화된 이벤트 조회 - 단일 쿼리"""
    try:
        page = int(page)

        # 11개 조회 (10개 + 다음 페이지 확인용 1개)
        result = await run_influx_query(
            query_influx_pages,
            "events", channel, "time", page, 11,  # page_size=11
            timeout=20
        )

        # 11개 왔으면 다음 페이지 있음
        has_next = len(result) > 10
        if has_next:
            result = result[:10]  # 10개만 사용

        # 데이터 포맷팅
        for i in range(len(result)):
            if isinstance(result[i]["time"], datetime):
                timestamp = result[i]["time"].timestamp()
            else:
                timestamp = float(result[i]["time"])

            duration_seconds = float(result[i].get("duration", 0)) / 1000.0
            end_timestamp = timestamp + duration_seconds
            end_datetime = datetime.fromtimestamp(end_timestamp)

            result[i]["end_ts"] = format_influx_militime(end_datetime)
            result[i]["start_ts"] = format_influx_militime(result[i]["time"])

        return {
            "success": True,
            "data": result,
            "page": page,
            "hasNext": has_next,
            "hasPrev": page > 1,
            "totalRecord": -1,
            "totalPages": -1
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in get_eventlist: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": [],
            "page": page,
            "hasNext": False,
            "hasPrev": False,
            "totalRecord": 0,
            "totalPages": 0
        }


@router.post("/getEventSearch/{channel}/{page}")
async def get_eventSearch(data: EventSearch, channel: str, page: int):
    """최적화된 이벤트 검색 - 11개 조회 방식"""
    try:
        page = int(page)
        page_size = 10
        startdate = data.StartDate
        paramIdx = int(data.param)
        if paramIdx < 0:
            paramIdx = 0
        param = eventType[paramIdx]
        enddate = data.EndDate

        # 11개를 가져와서 다음 페이지 확인
        result = await run_influx_query(
            query_paged_search_event,
            "events", channel, param,
            startdate, enddate, page,
            page_size + 1,  # 11개 조회
            timeout=20
        )

        # 다음 페이지 존재 여부 확인
        has_next = len(result) > page_size
        if has_next:
            result = result[:page_size]  # 10개만 사용

        # 데이터 포맷팅
        for i in range(len(result)):
            if isinstance(result[i]["time"], datetime):
                timestamp = result[i]["time"].timestamp()
            else:
                timestamp = float(result[i]["time"])

            duration_seconds = float(result[i].get("duration", 0)) / 1000.0
            end_timestamp = timestamp + duration_seconds
            end_datetime = datetime.fromtimestamp(end_timestamp)

            result[i]["end_ts"] = format_influx_militime(end_datetime)
            result[i]["start_ts"] = format_influx_militime(result[i]["time"])

        return {
            "success": True,
            "data": result,
            "page": page,
            "hasNext": has_next,
            "hasPrev": page > 1,
            # 하위 호환성
            "totalRecord": -1,
            "totalPages": -1
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in get_eventSearch: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": [],
            "page": page,
            "hasNext": False,
            "hasPrev": False,
            "totalRecord": 0,
            "totalPages": 0
        }


@router.get("/getAlarmStatus/{channel}")  # get alarm status with redis
def getAlarmStatus(channel):
    redis_state.client.select(1)
    key = f"alarm_status:{channel}"
    if redis_state.client.exists(key):
        try:
            harms = redis_state.client.hgetall(key)
            #            harmdict = json.loads(harms)
            #            print(harms)
            return {"success": True, "data": harms}
        except Exception as e:
            print('error', str(e))
            return {"success": False, "error": "Redis Read Error"}
    else:
        return {"success": False, "error": "No Data"}


@router.get("/getEn50160/{channel}")  # get alarm log with redis
def getEn50160(channel):
    if os_spec.os == 'Windows':
        key = get_RedisKey(channel, 'en50160')
        redis_state.client.execute_command("SELECT", 9)
        if redis_state.client.exists(key):
            try:
                harms = redis_state.client.hget(key, "en50160")
                harmdict = json.loads(harms)
                # 데이터 변환
                # transformed_data = transform_en50160_data(harmdict)
                return {"success": True, "data": harmdict}
            except Exception as e:
                return {"success": False, "error": "Redis Read Error"}
        else:
            return {"success": False, "error": "No Data"}
    else:
        redis_state.client.select(1)
        if redis_state.client.exists("en50160_status"):
            try:
                harms = redis_state.client.hget("en50160_status", channel)
                harmdict = json.loads(harms)
                # 데이터 변환
                transformed_data = transform_en50160_data(harmdict)
                return {"success": True, "data": transformed_data}
            except Exception as e:
                return {"success": False, "error": "Redis Read Error"}
        else:
            return {"success": False, "error": "No Data"}


def get_setupContext():
    redis_state.client.select(0)
    if redis_state.client.hexists("System", "setup"):
        redisContext = redis_state.client.hget("System", "setup")
        setting = json.loads(redisContext)
    else:
        file_path = os.path.join(SETTING_FOLDER, 'setup.json')
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                setting = json.load(f)
        except Exception as e:
            return None

    setup_dict = {
        "mode": setting.get("mode", ""),
        "General": setting.get("General", {}),
        "main": {},
        "sub": {}
    }

    for ch in setting.get("channel", []):
        name = ch.get("channel", "")
        if name == "Main":
            setup_dict["main"] = ch
        elif name == "Sub":
            setup_dict["sub"] = ch

    return setup_dict


@router.get("/getITIC/{channel}")
def get_itic(channel):
    data = getITIC_data("events", channel)
    if channel == 'Main':
        ch = 'main'
    else:
        ch = 'sub'
    setupdict = get_setupContext()
    if setupdict:
        rated_itic = setupdict[ch]
        ch_ratedvoltage = rated_itic["ptInfo"]["vnorminal"]
    else:
        return {"success": False, "error": "No Data"}
    for i in range(len(data)):
        data[i]["event_time"] = format_influx_time(data[i]["time"])
    if len(data) > 0:
        return {"success": True, "data": data, "ratedV": ch_ratedvoltage}
    else:
        return {"success": False, "error": "No Data"}


def transform_en50160_data(redis_data):
    """Redis 데이터를 Vue 컴포넌트가 기대하는 형식으로 변환"""

    # 변환된 데이터 딕셔너리
    transformed = {}

    # 날짜 정보
    transformed["start date"] = redis_data.get("start_time", "")
    transformed["end date"] = redis_data.get("last_report_time", "")

    # status와 compliance - 기존 형식 유지
    transformed["status"] = redis_data.get("complete", 0) * 256  # 예시 값
    transformed["compilance"] = redis_data.get("compliance", 0)  # 오타도 기존대로 유지

    # Frequency Variations - 단일 값 (L1만 표시)
    transformed["Frequency Variation 1"] = round(redis_data.get("freq1_var", 0) * 100, 2)
    transformed["Frequency Variation 2"] = round(redis_data.get("freq2_var", 0) * 100, 2)

    # Voltage Variations - 3상 배열
    volt1_var = redis_data.get("volt1_var", [0, 0, 0])
    volt2_var = redis_data.get("volt2_var", [0, 0, 0])
    transformed["Voltage Variation 1 L1(%)"] = round(volt1_var[0] * 100, 2)
    transformed["Voltage Variation 1 L2(%)"] = round(volt1_var[1] * 100, 2)
    transformed["Voltage Variation 1 L3(%)"] = round(volt1_var[2] * 100, 2)
    transformed["Voltage Variation 2 L1(%)"] = round(volt2_var[0] * 100, 2)
    transformed["Voltage Variation 2 L2(%)"] = round(volt2_var[1] * 100, 2)
    transformed["Voltage Variation 2 L3(%)"] = round(volt2_var[2] * 100, 2)

    # Voltage Unbalance - 단일 값
    transformed["Voltage Unbalance"] = round(redis_data.get("voltbal_var", 0) * 100, 2)

    # THD Variations - 3상 배열
    thd_var = redis_data.get("volt_thd_var", [0, 0, 0])
    transformed["THDs Variation L1(%)"] = round(thd_var[0] * 100, 2)
    transformed["THDs Variation L2(%)"] = round(thd_var[1] * 100, 2)
    transformed["THDs Variation L3(%)"] = round(thd_var[2] * 100, 2)

    # Harmonics Variations - 3상 배열
    hd_var = redis_data.get("volt_hd_var", [0, 0, 0])
    transformed["Harmonics Variatiopn L1(%)"] = round(hd_var[0] * 100, 2)  # 오타도 기존대로
    transformed["Harmonics Variatiopn L2(%)"] = round(hd_var[1] * 100, 2)
    transformed["Harmonics Variatiopn L3(%)"] = round(hd_var[2] * 100, 2)

    # Flicker Pst - 3상 배열
    pst_var = redis_data.get("pst_var", [0, 0, 0])
    transformed["Flickers Pst L1(%)"] = round(pst_var[0] * 100, 2)
    transformed["Flickers Pst L2(%)"] = round(pst_var[1] * 100, 2)
    transformed["Flickers Pst L3(%)"] = round(pst_var[2] * 100, 2)

    # Flicker Plt - 3상 배열
    plt_var = redis_data.get("plt_var", [0, 0, 0])
    transformed["Flickers Plt L1(%)"] = round(plt_var[0] * 100, 2)
    transformed["Flickers Plt L2(%)"] = round(plt_var[1] * 100, 2)
    transformed["Flickers Plt L3(%)"] = round(plt_var[2] * 100, 2)

    # Signal Voltage - 3상 배열
    svolt_var = redis_data.get("svolt_var", [0, 0, 0])
    transformed["Signaling Voltage L1(%)"] = round(svolt_var[0] * 100, 2)
    transformed["Signaling Voltage L2(%)"] = round(svolt_var[1] * 100, 2)
    transformed["Signaling Voltage L3(%)"] = round(svolt_var[2] * 100, 2)

    # 이벤트 카운트 - 4개 배열의 각 요소
    sag = redis_data.get("sag", [0, 0, 0, 0])
    swell = redis_data.get("swell", [0, 0, 0, 0])
    short_int = redis_data.get("short_interruption", [0, 0, 0, 0])
    long_int = redis_data.get("long_interruption", [0, 0, 0, 0])
    rvc = redis_data.get("rvc", [0, 0, 0, 0])

    # Voltage Dips (Sag)
    transformed["Voltage Dips L1"] = sag[0]
    transformed["Voltage Dips L2"] = sag[1]
    transformed["Voltage Dips L3"] = sag[2]
    transformed["Voltage Dips Multi Phase"] = sag[3]

    # Voltage Swells
    transformed["Voltage Swells L1"] = swell[0]
    transformed["Voltage Swells L2"] = swell[1]
    transformed["Voltage Swells L3"] = swell[2]
    transformed["Voltage Swells Multi Phase"] = swell[3]

    # Short Interruptions
    transformed["Short Interruptions L1"] = short_int[0]
    transformed["Short Interruptions L2"] = short_int[1]
    transformed["Short Interruptions L3"] = short_int[2]
    transformed["Short Interruptions Multi Phase"] = short_int[3]

    # Long Interruptions
    transformed["Long Interruptions L1"] = long_int[0]
    transformed["Long Interruptions L2"] = long_int[1]
    transformed["Long Interruptions L3"] = long_int[2]
    transformed["Long Interruptions Multi Phase"] = long_int[3]

    # Rapid Voltage Changes (RVC)
    transformed["Rapid Voltage Changes L1"] = rvc[0]
    transformed["Rapid Voltage Changes L2"] = rvc[1]
    transformed["Rapid Voltage Changes L3"] = rvc[2]
    transformed["Rapid Voltage Changes Multi Phase"] = rvc[3]

    # status&compliance 추가 (getComp 함수용)
    transformed["status&compliance"] = redis_data.get("compliance", 0)

    # status&compliance 추가 (getComp 함수용)
    # status는 complete 값 사용
    transformed["status"] = redis_data.get("complete", 0)

    # 각 항목의 err 값을 확인하여 compliance 비트 설정
    # err 값이 0이 아니면 해당 비트를 1로 설정 (Failed)
    # compliance_bits = 0
    #
    # # Frequency Variation 1 - bit 0
    # if redis_data.get("freq1_err", 0) > 0:
    #     compliance_bits |= (1 << 0)
    #
    # # Frequency Variation 2 - bit 1
    # if redis_data.get("freq2_err", 0) > 0:
    #     compliance_bits |= (1 << 1)
    #
    # # Voltage Variation 1 - bits 2, 3, 4
    # volt1_err = redis_data.get("volt1_err", [0, 0, 0])
    # for i in range(3):
    #     if volt1_err[i] > 0:
    #         compliance_bits |= (1 << (2 + i))
    #
    # # Voltage Variation 2 - bits 5, 6, 7
    # volt2_err = redis_data.get("volt2_err", [0, 0, 0])
    # for i in range(3):
    #     if volt2_err[i] > 0:
    #         compliance_bits |= (1 << (5 + i))
    #
    # # Voltage Unbalance - bit 8
    # if redis_data.get("voltbal_err", 0) > 0:
    #     compliance_bits |= (1 << 8)
    #
    # # THD - bits 9, 10, 11
    # thd_err = redis_data.get("volt_thd_err", [0, 0, 0])
    # for i in range(3):
    #     if thd_err[i] > 0:
    #         compliance_bits |= (1 << (9 + i))
    #
    # # Harmonics - bits 12, 13, 14
    # hd_err = redis_data.get("volt_hd_err", [0, 0, 0])
    # for i in range(3):
    #     if hd_err[i] > 0:
    #         compliance_bits |= (1 << (12 + i))
    #
    # # Pst - bits 15, 16, 17
    # pst_err = redis_data.get("pst_err", [0, 0, 0])
    # for i in range(3):
    #     if pst_err[i] > 0:
    #         compliance_bits |= (1 << (15 + i))
    #
    # # Plt - bits 18, 19, 20
    # plt_err = redis_data.get("plt_err", [0, 0, 0])
    # for i in range(3):
    #     if plt_err[i] > 0:
    #         compliance_bits |= (1 << (18 + i))
    #
    # # Signal Vol. - bits 21, 22, 23
    # svolt_err = redis_data.get("svolt_err", [0, 0, 0])
    # for i in range(3):
    #     if svolt_err[i] > 0:
    #         compliance_bits |= (1 << (21 + i))
    #
    # transformed["status&compliance"] = compliance_bits

    return transformed


def try_float(v):
    if v is None:
        return 0.0
    try:
        v = str(v).strip()  # 문자열로 바꾼 후 앞뒤 공백 제거
        newv = float(v)

        if math.isnan(newv):
            return 0.0
        return round(newv, 2)
    except (ValueError, TypeError):
        print(f"⚠️ float 변환 실패: '{v}'")
        return 0.0


def try_parse(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def loaditem_from_flat_redis(channel, item, mode):
    """
    Redis 1번 DB에서 분해된 필드를 dashboard_meter 기준으로 복원
    """
    redis_state.client.execute_command("SELECT", 1)
    keyname = get_RedisKey(channel, item)
    flat_data = redis_state.client.hgetall(keyname)

    result = {}
    # normalized_data = {k.strip(): v for k, v in flat_data.items()}
    # "meter", "power", "energy", "thd"만 대상으로 함
    if mode == 0:
        for category, item_keys in RedisMapped.dashboard_meter.items():
            category_data = {}
            for key in item_keys:
                raw_value = flat_data.get(key)
                category_data[key] = try_float(raw_value)
            result[category] = category_data
    else:
        for category, item_keys in RedisMapped.dashboard_trans.items():
            category_data = {}
            for key in item_keys:
                raw_value = flat_data.get(key)
                category_data[key] = try_float(raw_value)
            result[category] = category_data

    return result


@router.get("/getTransRedis/{channel}")
def getTransRedis(channel):
    try:
        redis_data = loaditem_from_flat_redis(channel, "meter", 1)
        meterdata = {}
        # print(redis_data)
        for category, item_keys in RedisMapped.dashboard_trans.items():
            data = redis_data.get(category, {})
            for key in item_keys:
                meterdata[key] = data.get(key)

        return {"success": True, "data": meterdata}
    except Exception as e:
        print(str(e))
        return {"success": False, "error": f"Redis Read Error: {str(e)}"}

@router.get("/getEquipStatus/{channel}")
def get_eqStatus(channel):
    redis_state.client.select(0)
    if not redis_state.client.hexists("Equipment", "StartingCurrent"):
        status = False
        return {"success": False, "status": status}

    stCrDict = json.loads(redis_state.client.hget("Equipment", "StartingCurrent"))
    redis_state.client.select(1)
    if channel == 'Main':
        itot = redis_state.client.hget("meter_main", "Itot")
        status = float(itot) > (float(stCrDict["main"]) * 3)
    else:
        itot = redis_state.client.hget("meter_sub", "Itot")
        status = float(itot) > (float(stCrDict["sub"]) * 3)
    return {"success": True, "status": status}

@router.get("/getMeterRedisNew/{channel}/{mode}")
def getMeterRedis2(channel, mode):
    try:
        redis_data = loaditem_from_flat_redis(channel, "meter", 0)
        meterdata = {}
        # print(redis_data)
        for category, item_keys in RedisMapped.dashboard_meter.items():
            data = redis_data.get(category, {})
            for key in item_keys:
                meterdata[key] = data.get(key)

        # thd 계산도 그대로
        thd = redis_data.get("thd", {})
        meterdata["thdu total"] = sum([try_float(thd.get(k)) for k in ["THD_U1", "THD_U2", "THD_U3"]])
        meterdata["thdi total"] = sum([try_float(thd.get(k)) for k in ["THD_I1", "THD_I2", "THD_I3"]])
        meterdata["tddi total"] = sum([try_float(thd.get(k)) for k in ["TDD_I1", "TDD_I2", "TDD_I3"]])

        return {"success": True, "data": meterdata}

    except Exception as e:
        print(str(e))
        return {"success": False, "error": f"Redis Read Error: {str(e)}"}
    # if mode == 'device2':
    #     try:
    #         redis_main = loaditem_from_flat_redis('Main', "meter", 0)
    #         metermain = {}
    #         for category, item_keys in RedisMapped.dashboard_meter.items():
    #             data = redis_main.get(category, {})
    #             for key in item_keys:
    #                 metermain[key] = data.get(key)
    #         redis_sub = loaditem_from_flat_redis('Sub', "meter", 0)
    #         metersub = {}
    #         for category, item_keys in RedisMapped.dashboard_meter.items():
    #             data = redis_sub.get(category, {})
    #             for key in item_keys:
    #                 metersub[key] = data.get(key)
    #
    #         if metermain.get("S4", 0) > metersub.get("S4", 0):
    #             meterdata = metermain
    #             redis_data = redis_main
    #             channel = 'Main'
    #         else:
    #             meterdata = metersub
    #             redis_data = redis_sub
    #             channel = 'Sub'
    #
    #         # thd 계산도 그대로
    #         thd = redis_data.get("thd", {})
    #         meterdata["thdu total"] = sum([try_float(thd.get(k)) for k in ["THD_U1", "THD_U2", "THD_U3"]])
    #         meterdata["thdi total"] = sum([try_float(thd.get(k)) for k in ["THD_I1", "THD_I2", "THD_I3"]])
    #         meterdata["tddi total"] = sum([try_float(thd.get(k)) for k in ["TDD_I1", "TDD_I2", "TDD_I3"]])
    #
    #         return {"success": True, "data": meterdata, "channel": channel}
    #     except Exception as e:
    #         print(str(e))
    #         return {"success": False, "error": f"Redis Read Error: {str(e)}"}
    # else:
    #     try:
    #         redis_data = loaditem_from_flat_redis(channel, "meter", 0)
    #         meterdata = {}
    #         # print(redis_data)
    #         for category, item_keys in RedisMapped.dashboard_meter.items():
    #             data = redis_data.get(category, {})
    #             for key in item_keys:
    #                 meterdata[key] = data.get(key)
    #
    #         # thd 계산도 그대로
    #         thd = redis_data.get("thd", {})
    #         meterdata["thdu total"] = sum([try_float(thd.get(k)) for k in ["THD_U1", "THD_U2", "THD_U3"]])
    #         meterdata["thdi total"] = sum([try_float(thd.get(k)) for k in ["THD_I1", "THD_I2", "THD_I3"]])
    #         meterdata["tddi total"] = sum([try_float(thd.get(k)) for k in ["TDD_I1", "TDD_I2", "TDD_I3"]])
    #
    #         return {"success": True, "data": meterdata}
    #     except Exception as e:
    #         print(str(e))
    #         return {"success": False, "error": f"Redis Read Error: {str(e)}"}


def load_json_from_redisString(key: str):
    redis_state.client.execute_command("SELECT", 9)
    raw = redis_state.client.get(key)
    return json.loads(raw) if raw else {}


def load_json_from_redisHash(key: str, field):
    redis_state.client.execute_command("SELECT", 1)
    raw = redis_state.client.hget(key, field)
    return json.loads(raw) if raw else {}


def loadall_json_from_redis(channel):
    redis_state.client.execute_command("SELECT", 9)
    resultmap = dict()
    keylist = get_allRedisKey(channel)  # 예: {'meter_main': ['meter', 'thd', ...], ...}

    for keyname, itemlist in keylist.items():
        resultmap[keyname] = dict()
        for item in itemlist:
            resultmap[keyname][item] = load_json_from_redisHash(keyname, item)
    return resultmap


def loaditem_json_from_redis(channel, item):
    resultmap = dict()
    keylist = RedisMapped.mapdict.get(item)  # 예: {'meter_main': ['meter', 'thd', ...], ...}
    keyName = get_RedisKey(channel, item)
    for fieldname in keylist:
        resultmap[fieldname] = load_json_from_redisHash(keyName, fieldname)
    return resultmap


def loaditems_json_from_redis(channel, item):
    """
    RedisMapped.mapdict 기준으로 Redis 1번 DB에서 분해된 해시 데이터를 category별로 복원
    """
    redis_state.client.execute_command("SELECT", 1)
    keyname = get_RedisKey(channel, item)
    flat_data = redis_state.client.hgetall(keyname)

    # 공백 제거, 문자열 처리
    normalized_data = {k.strip(): v for k, v in flat_data.items()}

    resultmap = {}
    category_list = RedisMapped.mapdict.get(item, [])  # 예: ['meter', 'thd', ...]

    for category in category_list:
        item_keys = RedisMapped.dashboard_meter.get(category)
        category_data = {}

        if item_keys:
            for key in item_keys:
                raw = normalized_data.get(key)
                category_data[key] = try_float(raw)
            resultmap[category] = category_data
        else:
            # dashboard_meter에 정의되지 않은 경우는 prefix 기반으로 묶기 (예: 'maxmin')
            category_data = {
                k: try_float(v) for k, v in normalized_data.items() if k.startswith(category)
            }
            resultmap[category] = category_data

    return resultmap


def extract_key_list(key_dict_list):
    return [item["key"] for item in key_dict_list]

def get_Calibrate(channel):
    try:
        redis_state.client.select(0)
        refdict = None
        if redis_state.client.hexists("calibration","ref"):
            refStr = redis_state.client.hget("calibration","ref")
            refdict = json.loads(refStr)
        redis_state.client.execute_command("SELECT", 1)
        keyname = get_RedisKey(channel, "meter")
        if not redis_state.client.exists(keyname):
            return {"success": False, "error": f"No exist key"}

        field_keys = (
                extract_key_list(RedisMapCalibrate.p_voltage_keys) +
                # extract_key_list(RedisMapCalibrate.freq_keys) +
                # extract_key_list(RedisMapCalibrate.l_voltage_keys) +
                extract_key_list(RedisMapCalibrate.current_keys) +
                extract_key_list(RedisMapCalibrate.p_angle_keys) +
                extract_key_list(RedisMapCalibrate.a_powers_keys) +
                extract_key_list(RedisMapCalibrate.r_powers_keys) +
                extract_key_list(RedisMapCalibrate.ap_powers_keys)
        )
        field_keys = list(set(field_keys))


        # Redis에서 가져오기
        values = redis_state.client.hmget(keyname, field_keys)
        flat_fields = {k: try_float(v) for k, v in zip(field_keys, values)}
        # 그룹핑
        meters = {k["key"]: flat_fields.get(k["key"]) for k in (
                RedisMapCalibrate.p_voltage_keys +
                # RedisMapCalibrate.freq_keys +
                # RedisMapCalibrate.l_voltage_keys +
                RedisMapCalibrate.current_keys +
                RedisMapCalibrate.p_angle_keys +
                RedisMapCalibrate.a_powers_keys +
                RedisMapCalibrate.r_powers_keys +
                RedisMapCalibrate.ap_powers_keys
        )}
        full_data = redis_state.client.hgetall(keyname)
        if channel == 'Main':
            ch = 'main'
        else:
            ch = 'sub'

        processor = redis_state.processor
        handler = redis_state.handler
        parsed = processor.get_and_parse(
            config_name="maxmin_1sec",
            key=f"MAXMIN_{ch}",
            data_type=RedisDataType.HASH,
            field="1sec"  # 필수
        )
        p_voltage_data = handler.get_data_dict(meters, parsed, RedisMapCalibrate.p_voltage_keys, 'V')
        # freq_data = handler.get_data_dict(meters, parsed, RedisMapCalibrate.freq_keys, 'Hz')
        # l_voltage_data = handler.get_data_dict(meters, parsed, RedisMapCalibrate.l_voltage_keys, 'V')
        current_data = handler.get_data_dict(meters, parsed, RedisMapCalibrate.current_keys, 'A')
        angle_data = handler.get_data_dict(meters, parsed, RedisMapCalibrate.p_angle_keys, '%')
        p_data = handler.get_data_dict(meters, parsed, RedisMapCalibrate.a_powers_keys, 'kw')
        q_data = handler.get_data_dict(meters, parsed, RedisMapCalibrate.r_powers_keys, 'kvar')
        s_data = handler.get_data_dict(meters, parsed, RedisMapCalibrate.ap_powers_keys, 'kVA')


        result = {
            "success": True,
            "meterData": [
                    {"subTitle": "Phase Voltage", "data": p_voltage_data},
                    # {"subTitle": "Line Voltage", "data": l_voltage_data},
                    {"subTitle": "Current", "data": current_data},
                    # {"subTitle": "Frequency", "data": freq_data},
                    {"subTitle": "PowerAngle", "data": angle_data},
                    {"subTitle": "ActivePower", "data": p_data},
                    {"subTitle": "ReactivePower", "data": q_data},
                    {"subTitle": "ApparentPower", "data": s_data},
                ],
            "refData": refdict
        }

        return {"success": True, "retData": result}
    except Exception as e:
        print(str(e))
        return {"success": False, "error": str(e)}

@router.get("/getOnesfromRedis/{channel}/{unbal}")
def get_OneSecond(channel, unbal):
    try:
        redis_state.client.execute_command("SELECT", 1)
        keyname = get_RedisKey(channel, "meter")
        if not redis_state.client.exists(keyname):
            return {"success": False, "error": f"No exist key"}
        if int(unbal) == 1:
            field_keys = (
                    extract_key_list(RedisMapDetail2.p_voltage_keys) +
                    extract_key_list(RedisMapDetail2.freq_keys) +
                    extract_key_list(RedisMapDetail2.l_voltage_keys) +
                    extract_key_list(RedisMapDetail2.current_keys) +
                    extract_key_list(RedisMapDetail2.unbal_keys) +
                    extract_key_list(RedisMapDetail2.pf_keys)
            )
        else:
            field_keys = (
                    extract_key_list(RedisMapDetail2.p_voltage_keys) +
                    extract_key_list(RedisMapDetail2.freq_keys) +
                    extract_key_list(RedisMapDetail2.l_voltage_keys) +
                    extract_key_list(RedisMapDetail2.current_keys) +
                    extract_key_list(RedisMapDetail2.unbal_keys2) +
                    extract_key_list(RedisMapDetail2.pf_keys)
            )
        field_keys = list(set(field_keys))

        # Redis에서 가져오기
        values = redis_state.client.hmget(keyname, field_keys)
        flat_fields = {k: try_float(v) for k, v in zip(field_keys, values)}
        # 그룹핑
        if int(unbal) == 1:
            meters = {k["key"]: flat_fields.get(k["key"]) for k in (
                    RedisMapDetail2.p_voltage_keys +
                    RedisMapDetail2.freq_keys +
                    RedisMapDetail2.l_voltage_keys +
                    RedisMapDetail2.current_keys +
                    RedisMapDetail2.unbal_keys +
                    RedisMapDetail2.pf_keys
            )}
        else:
            meters = {k["key"]: flat_fields.get(k["key"]) for k in (
                    RedisMapDetail2.p_voltage_keys +
                    RedisMapDetail2.freq_keys +
                    RedisMapDetail2.l_voltage_keys +
                    RedisMapDetail2.current_keys +
                    RedisMapDetail2.unbal_keys2 +
                    RedisMapDetail2.pf_keys
            )}
        full_data = redis_state.client.hgetall(keyname)
        if channel == 'Main':
            ch = 'main'
        else:
            ch = 'sub'

        if os_spec.os == 'Windows':
            maxmin = {
                k: v if k.endswith("_maxTime") or k.endswith("_minTime") else try_float(v)
                for k, v in full_data.items()
                if k.endswith("_max") or k.endswith("_min") or k.endswith("_maxTime") or k.endswith("_minTime")
            }
            p_voltage_data = RedisMapDetail2.get_Datadict(meters, maxmin, RedisMapDetail2.p_voltage_keys, 'V')
            freq_data = RedisMapDetail2.get_Datadict(meters, maxmin, RedisMapDetail2.freq_keys, 'Hz')
            l_voltage_data = RedisMapDetail2.get_Datadict(meters, maxmin, RedisMapDetail2.l_voltage_keys, 'V')
            current_data = RedisMapDetail2.get_Datadict(meters, maxmin, RedisMapDetail2.current_keys, 'A')
            pf_data = RedisMapDetail2.get_Datadict(meters, maxmin, RedisMapDetail2.pf_keys, '%')
            unbal_data = RedisMapDetail2.get_Datadict(meters, maxmin, RedisMapDetail2.unbal_keys, '%')
        else:
            processor = redis_state.processor
            handler = redis_state.handler
            parsed = processor.get_and_parse(
                config_name="maxmin_1sec",
                key=f"MAXMIN_{ch}",
                data_type=RedisDataType.HASH,
                field="1sec"  # 필수
            )
            if parsed is None:
                logging.error('OneS Maxmin is None')
            p_voltage_data = handler.get_data_dict(meters, parsed, RedisMapDetail2.p_voltage_keys, 'V')
            freq_data = handler.get_data_dict(meters, parsed, RedisMapDetail2.freq_keys, 'Hz')
            l_voltage_data = handler.get_data_dict(meters, parsed, RedisMapDetail2.l_voltage_keys, 'V')
            current_data = handler.get_data_dict(meters, parsed, RedisMapDetail2.current_keys, 'A')
            pf_data = handler.get_data_dict(meters, parsed, RedisMapDetail2.pf_keys, '%')
            if int(unbal) == 1:
                unbal_data = handler.get_data_dict(meters, parsed, RedisMapDetail2.unbal_keys, '%')
            else:
                unbal_data = handler.get_data_dict(meters, parsed, RedisMapDetail2.unbal_keys2, '%')

        result = {
            "success": True,
            "retData": {
                "unbalData": [
                    {"subTitle": "Voltage", "data": [
                        {"id": 0, "subTitle": "-", "value": flat_fields.get("Ubal1"), "max": "-", "min": "-",
                         "unit": "%"}]},
                    {"subTitle": "Current", "data": [
                        {"id": 0, "subTitle": "-", "value": flat_fields.get("Ibal1"), "max": "-", "min": "-",
                         "unit": "%"}]}
                ],
                "meterData": [
                    {"subTitle": "Phase Voltage", "data": p_voltage_data},
                    {"subTitle": "Line Voltage", "data": l_voltage_data},
                    {"subTitle": "Current", "data": current_data},
                    {"subTitle": "Frequency", "data": freq_data},
                    {"subTitle": "PF", "data": pf_data},
                    {"subTitle": "Unbalance", "data": unbal_data},
                ]
            }
        }

        return {"success": True, "retData": result}
    except Exception as e:
        print(str(e))
        return {"success": False, "error": str(e)}


@router.get("/getonemfromRedis/{channel}")
def get_onemfromRedis(channel):
    try:
        redis_state.client.execute_command("SELECT", 1)
        keyname = get_RedisKey(channel, "meter")

        if not redis_state.client.exists(keyname):
            return {"success": False, "error": f"No exist key"}

        # 모든 필요한 필드 키 모으기
        field_keys = (
                extract_key_list(RedisMapDetail2.p_voltage_keys) +
                extract_key_list(RedisMapDetail2.current_keys) +
                extract_key_list(RedisMapDetail2.p_volt_angle_keys) +
                extract_key_list(RedisMapDetail2.current_angle_keys)
        )
        field_keys = list(set(field_keys))

        # Redis에서 가져오기
        values = redis_state.client.hmget(keyname, field_keys)

        flat_fields = {k: try_float(v) for k, v in zip(field_keys, values)}

        full_data = redis_state.client.hgetall(keyname)
        maxmin = {
            k: try_float(v)
            for k, v in full_data.items()
            if k.endswith("_max") or k.endswith("_min")
        }

        max = []
        for key in ["U1", "U2", "U3", "I1", "I2", "I3"]:
            value = maxmin.get(f"{key}_max") or flat_fields.get(key)
            max.append(value)

        result = {
            "success": True,
            "retData": {
                "angleData": {
                    "magnitude": [
                        flat_fields.get("U1"), flat_fields.get("U2"), flat_fields.get("U3"),
                        flat_fields.get("I1"), flat_fields.get("I2"), flat_fields.get("I3")
                    ],
                    "degree": [
                        flat_fields.get("Uangle1"), flat_fields.get("Uangle2"), flat_fields.get("Uangle3"),
                        flat_fields.get("Iangle1"), flat_fields.get("Iangle2"), flat_fields.get("Iangle3")
                    ],
                    "texts": ["V1", "V2", "V3", "I1", "I2", "I3"],
                    "max": max,
                }
            }
        }
        # print(result)
        return {"success": True, "retData": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/getFifthMfromRedis/{channel}")
def get_FifthMfromRedis(channel):
    try:
        redis_state.client.execute_command("SELECT", 1)
        keyname = get_RedisKey(channel, "meter")

        if not redis_state.client.exists(keyname):
            return {"success": False, "error": f"No exist key"}

        # 모든 필요한 필드 키 모으기
        field_keys = (
                extract_key_list(RedisMapDetail2.a_powers_keys) +
                extract_key_list(RedisMapDetail2.r_powers_keys) +
                extract_key_list(RedisMapDetail2.ap_powers_keys) +
                extract_key_list(RedisMapDetail2.thdu_keys) +
                extract_key_list(RedisMapDetail2.thdi_keys) +
                extract_key_list(RedisMapDetail2.tddi_keys)
        )
        field_keys = list(set(field_keys))

        # Redis에서 가져오기
        values = redis_state.client.hmget(keyname, field_keys)
        flat_fields = {k: try_float(v) for k, v in zip(field_keys, values)}
        # 그룹핑

        powers = {k["key"]: flat_fields.get(k["key"]) for k in (
                RedisMapDetail2.a_powers_keys +
                RedisMapDetail2.r_powers_keys +
                RedisMapDetail2.ap_powers_keys
        )}

        thd = {k["key"]: flat_fields.get(k["key"]) for k in (
                RedisMapDetail2.thdu_keys +
                RedisMapDetail2.thdi_keys +
                RedisMapDetail2.tddi_keys
        )}

        # maxmin은 접두어 기반으로 따로 추출
        full_data = redis_state.client.hgetall(keyname)
        if channel == 'Main':
            ch = 'main'
        else:
            ch = 'sub'
        if os_spec.os == 'Windows':
            maxmin = {
                k: try_float(v)
                for k, v in full_data.items()
                if k.endswith("_max") or k.endswith("_min")
            }

            a_power_data = RedisMapDetail2.get_Datadict(powers, maxmin, RedisMapDetail2.a_powers_keys, 'kW')
            r_power_data = RedisMapDetail2.get_Datadict(powers, maxmin, RedisMapDetail2.r_powers_keys, 'kVar')
            ap_power_data = RedisMapDetail2.get_Datadict(powers, maxmin, RedisMapDetail2.ap_powers_keys, 'kVA')

            thdu_data = RedisMapDetail2.get_Datadict(thd, maxmin, RedisMapDetail2.thdu_keys, '%')
            thdi_data = RedisMapDetail2.get_Datadict(thd, maxmin, RedisMapDetail2.thdi_keys, '%')
            tddi_data = RedisMapDetail2.get_Datadict(thd, maxmin, RedisMapDetail2.tddi_keys, '%')

            result = {
                "success": True,
                "retData": {
                    "powerData": [
                        {"subTitle": "Active Power", "data": a_power_data},
                        {"subTitle": "Reactive Power", "data": r_power_data},
                        {"subTitle": "Apparent Power", "data": ap_power_data}
                    ],
                    "thdData": [
                        {"subTitle": "THD-U", "data": thdu_data},
                        {"subTitle": "THD-I", "data": thdi_data},
                        {"subTitle": "TDD-I", "data": tddi_data}
                    ]
                }
            }
        else:
            processor = redis_state.processor
            handler = redis_state.handler
            parsed = processor.get_and_parse(
                config_name="maxmin_15min",
                key=f"MAXMIN_{ch}",
                data_type=RedisDataType.HASH,
                field="15min"  # 필수
            )
            if parsed is None:
                logging.error('Fifth Maxmin is None')
            a_power_data = handler.get_data_dict(powers, parsed, RedisMapDetail2.a_powers_keys, 'kW')
            r_power_data = handler.get_data_dict(powers, parsed, RedisMapDetail2.r_powers_keys, 'kVar')
            ap_power_data = handler.get_data_dict(powers, parsed, RedisMapDetail2.ap_powers_keys, 'kVA')

            thdu_data = handler.get_data_dict(thd, parsed, RedisMapDetail2.thdu_keys, '%')
            thdi_data = handler.get_data_dict(thd, parsed, RedisMapDetail2.thdi_keys, '%')
            tddi_data = handler.get_data_dict(thd, parsed, RedisMapDetail2.tddi_keys, '%')

            processor = redis_state.processor

            parsed_demand = processor.get_and_parse(
                config_name="demand",
                key="Demand",  # ← Redis Hash 키
                data_type=RedisDataType.HASH,  # ← Hash 타입 지정
                field=channel  # ← Hash 필드명
            )

            formatted_data = DemandDataFormatter.format_demand_data(parsed_demand)

            result = {
                "success": True,
                "retData": {
                    "powerData": [
                        {"subTitle": "Active Power", "data": a_power_data},
                        {"subTitle": "Reactive Power", "data": r_power_data},
                        {"subTitle": "Apparent Power", "data": ap_power_data}
                    ],
                    "thdData": [
                        {"subTitle": "THD-U", "data": thdu_data},
                        {"subTitle": "THD-I", "data": thdi_data},
                        {"subTitle": "TDD-I", "data": tddi_data}
                    ],
                    "demandDataP": [
                        {"subTitle": "Active", "data": formatted_data['power_demand']},
                        {"subTitle": "Reactive", "data": formatted_data['reactive_demand']},
                        {"subTitle": "Apparent", "data": formatted_data['apparent_demand']},
                    ],
                    "demandDataI": [
                        {"subTitle": "Current", "data": formatted_data['current_demand']},
                    ]
                }
            }
        return {"success": True, "retData": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/getOnehfromRedis/{channel}")
def get_onehRedis(channel):
    try:
        redis_state.client.execute_command("SELECT", 1)
        keyname = get_RedisKey(channel, "energy")

        if not redis_state.client.exists(keyname):
            result = {
                "success": False,
                "retData": {
                    "energyData": [
                        {"subTitle": "Import",
                         "data": [{"id": 0, "subTitle": "-", "value": 0, "max": "-", "min": "-", "unit": "kWh"}]},
                        {"subTitle": "Export",
                         "data": [{"id": 0, "subTitle": "-", "value": 0, "max": "-", "min": "-", "unit": "kWh"}]}
                    ]
                }
            }
            return {"success": False, "error": f"No exist key", "retData": result}

        # 모든 필요한 필드 키 모으기
        field_keys = (
            extract_key_list(RedisMapDetail2.kwh_keys)
        )
        field_keys = list(set(field_keys))

        # Redis에서 가져오기
        values = redis_state.client.hmget(keyname, field_keys)
        flat_fields = {k: try_float(v) for k, v in zip(field_keys, values)}

        result = {
            "success": True,
            "retData": {
                "energyData": [
                    {"subTitle": "Import", "data": [
                        {"id": 0, "subTitle": "-", "value": flat_fields.get("total_kwh_import"), "max": "-", "min": "-",
                         "unit": "kWh"},
                        {"id": 1, "subTitle": "-", "value": flat_fields.get("thismonth_kwh_import"), "max": "-",
                         "min": "-", "unit": "kWh"}]},
                    {"subTitle": "Export", "data": [
                        {"id": 0, "subTitle": "-", "value": flat_fields.get("total_kwh_export"), "max": "-", "min": "-",
                         "unit": "kWh"},
                        {"id": 1, "subTitle": "-", "value": flat_fields.get("thismonth_kwh_export"), "max": "-",
                         "min": "-", "unit": "kWh"}]}
                ]
            }
        }
        return {"success": True, "retData": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/getEnergyRedis/{channel}")
def get_consumption_energy(channel):
    try:
        redis_state.client.select(1)
        if not redis_state.client.exists("energy_summary"):
            return {"success": False, "error": f"No exist key"}
        else:
            data = redis_state.client.hget("energy_summary", channel)
            con_data = json.loads(data)
            retData = {
                "today": con_data.get("consumption", {}).get("kwh_import_consumption", 0),
                "daily": con_data.get("daily_kwh_import", 0),
                "weekly": con_data.get("weekly_kwh_import", 0),
                "monthly": con_data.get("monthly_kwh_import", 0),
                "yearly": con_data.get("yearly_kwh_import", 0),
                "daily_comparison": con_data.get("daily_comparison", {}).get("change_percent", 0),
                "weekly_comparison": con_data.get("weekly_comparison", {}).get("change_percent", 0),
                "monthly_comparison": con_data.get("monthly_comparison", {}).get("change_percent", 0),
                "yearly_comparison": con_data.get("yearly_comparison", {}).get("change_percent", 0)
            }
            return {"success": True, "data": retData}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/getAllMeterRedisNew/{channel}")
def get_all_meter_redis(channel):
    try:
        redis_state.client.execute_command("SELECT", 1)
        keyname = get_RedisKey(channel, "meter")

        if not redis_state.client.exists(keyname):
            return {"success": False, "error": f"No exist key"}

        # 모든 필요한 필드 키 모으기
        field_keys = (
                extract_key_list(RedisMapDetail2.p_voltage_keys) +
                extract_key_list(RedisMapDetail2.freq_keys) +
                extract_key_list(RedisMapDetail2.l_voltage_keys) +
                extract_key_list(RedisMapDetail2.current_keys) +
                extract_key_list(RedisMapDetail2.a_powers_keys) +
                extract_key_list(RedisMapDetail2.r_powers_keys) +
                extract_key_list(RedisMapDetail2.ap_powers_keys) +
                extract_key_list(RedisMapDetail2.thdu_keys) +
                extract_key_list(RedisMapDetail2.thdi_keys) +
                extract_key_list(RedisMapDetail2.tddi_keys) +
                extract_key_list(RedisMapDetail2.p_volt_angle_keys) +
                extract_key_list(RedisMapDetail2.current_angle_keys) +
                extract_key_list(RedisMapDetail2.kwh_keys) +
                extract_key_list(RedisMapDetail2.unbal_keys) +
                extract_key_list(RedisMapDetail2.pf_keys)
        )
        field_keys = list(set(field_keys))

        # Redis에서 가져오기
        values = redis_state.client.hmget(keyname, field_keys)
        flat_fields = {k: try_float(v) for k, v in zip(field_keys, values)}
        # 그룹핑
        meters = {k["key"]: flat_fields.get(k["key"]) for k in (
                RedisMapDetail2.p_voltage_keys +
                RedisMapDetail2.freq_keys +
                RedisMapDetail2.l_voltage_keys +
                RedisMapDetail2.current_keys +
                RedisMapDetail2.p_volt_angle_keys +
                RedisMapDetail2.current_angle_keys +
                RedisMapDetail2.kwh_keys +
                RedisMapDetail2.unbal_keys +
                RedisMapDetail2.pf_keys
        )}

        powers = {k["key"]: flat_fields.get(k["key"]) for k in (
                RedisMapDetail2.a_powers_keys +
                RedisMapDetail2.r_powers_keys +
                RedisMapDetail2.ap_powers_keys
        )}

        thd = {k["key"]: flat_fields.get(k["key"]) for k in (
                RedisMapDetail2.thdu_keys +
                RedisMapDetail2.thdi_keys +
                RedisMapDetail2.tddi_keys
        )}

        # maxmin은 접두어 기반으로 따로 추출
        full_data = redis_state.client.hgetall(keyname)
        maxmin = {
            k: try_float(v)
            for k, v in full_data.items()
            if k.endswith("_max") or k.endswith("_min")
        }

        # 데이터 처리
        p_voltage_data = RedisMapDetail2.get_Datadict(meters, maxmin, RedisMapDetail2.p_voltage_keys, 'V')
        freq_data = RedisMapDetail2.get_Datadict(meters, maxmin, RedisMapDetail2.freq_keys, 'Hz')
        l_voltage_data = RedisMapDetail2.get_Datadict(meters, maxmin, RedisMapDetail2.l_voltage_keys, 'V')
        current_data = RedisMapDetail2.get_Datadict(meters, maxmin, RedisMapDetail2.current_keys, 'A')
        pf_data = RedisMapDetail2.get_Datadict(meters, maxmin, RedisMapDetail2.pf_keys, '%')

        a_power_data = RedisMapDetail2.get_Datadict(powers, maxmin, RedisMapDetail2.a_powers_keys, 'kW')
        r_power_data = RedisMapDetail2.get_Datadict(powers, maxmin, RedisMapDetail2.r_powers_keys, 'kVar')
        ap_power_data = RedisMapDetail2.get_Datadict(powers, maxmin, RedisMapDetail2.ap_powers_keys, 'kVA')

        thdu_data = RedisMapDetail2.get_Datadict(thd, maxmin, RedisMapDetail2.thdu_keys, '%')
        thdi_data = RedisMapDetail2.get_Datadict(thd, maxmin, RedisMapDetail2.thdi_keys, '%')
        tddi_data = RedisMapDetail2.get_Datadict(thd, maxmin, RedisMapDetail2.tddi_keys, '%')

        max = [
            maxmin.get("U1_max"), maxmin.get("U2_max"), maxmin.get("U3_max"),
            maxmin.get("I1_max"), maxmin.get("I2_max"), maxmin.get("I3_max")
        ] if channel == 'Main' else [
            flat_fields.get("U1"), flat_fields.get("U2"), flat_fields.get("U3"),
            flat_fields.get("I1"), flat_fields.get("I2"), flat_fields.get("I3")
        ]

        result = {
            "success": True,
            "retData": {
                "angleData": {
                    "magnitude": [
                        flat_fields.get("U1"), flat_fields.get("U2"), flat_fields.get("U3"),
                        flat_fields.get("I1"), flat_fields.get("I2"), flat_fields.get("I3")
                    ],
                    "degree": [
                        flat_fields.get("Uangle1"), flat_fields.get("Uangle2"), flat_fields.get("Uangle3"),
                        flat_fields.get("Iangle1"), flat_fields.get("Iangle2"), flat_fields.get("Iangle3")
                    ],
                    "texts": ["U1", "U2", "U3", "I1", "I2", "I3"],
                    "max": max,
                },
                "unbalData": [
                    {"subTitle": "Voltage", "data": [
                        {"id": 0, "subTitle": "-", "value": flat_fields.get("Ubal1"), "max": "-", "min": "-",
                         "unit": "%"}]},
                    {"subTitle": "Current", "data": [
                        {"id": 0, "subTitle": "-", "value": flat_fields.get("Ibal1"), "max": "-", "min": "-",
                         "unit": "%"}]}
                ],
                "energyData": [
                    {"subTitle": "Import", "data": [
                        {"id": 0, "subTitle": "-", "value": flat_fields.get("import kwh"), "max": "-", "min": "-",
                         "unit": "kWh"}]},
                    {"subTitle": "Export", "data": [
                        {"id": 0, "subTitle": "-", "value": flat_fields.get("export kwh"), "max": "-", "min": "-",
                         "unit": "kWh"}]}
                ],
                "meterData": [
                    {"subTitle": "Phase Voltage", "data": p_voltage_data},
                    {"subTitle": "Line Voltage", "data": l_voltage_data},
                    {"subTitle": "Current", "data": current_data},
                    {"subTitle": "Frequency", "data": freq_data},
                    {"subTitle": "PF", "data": pf_data},
                ],
                "powerData": [
                    {"subTitle": "Active Power", "data": a_power_data},
                    {"subTitle": "Reactive Power", "data": r_power_data},
                    {"subTitle": "Apparent Power", "data": ap_power_data}
                ],
                "thdData": [
                    {"subTitle": "THD-U", "data": thdu_data},
                    {"subTitle": "THD-I", "data": thdi_data},
                    {"subTitle": "TDD-I", "data": tddi_data}
                ]
            }
        }
        return {"success": True, "retData": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/getEnergyRedis/{channel}")
def get_energyReport(channel):
    flag = False
    filtered_data = dict()
    try:
        # Redis 데이터 한 번에 로딩

        rdkey = get_RedisKey(channel, "meter")

        redis_data = load_json_from_redisHash(rdkey, "energy")
        # 디코딩
        # print(redis_data)
        if redis_data:
            try:
                filtered_data = {
                    key: redis_data.get(key, None)
                    for key in (RedisMapped.energy_report or [])
                }
                flag = True

            except json.JSONDecodeError:
                flag = False
        else:
            flag = False
        print(filtered_data)
        if flag:
            return {"success": flag, "data": filtered_data}
        else:
            return {"success": flag, "error": f"Json Parsing Error"}
    except Exception as e:
        print(str(e))
        return {"success": flag, "error": f"Redis Read Error: {str(e)}"}


@router.get("/getEnergy/{channel}")
def get_energy(channel):
    try:
        rdkey = get_RedisKey(channel, "meter")

        redis_state.client.execute_command("SELECT", 1)
        redis_data = redis_state.client.hget(rdkey, "export kwh")
        return {"success": True, "data": redis_data}

    except Exception as e:
        print(str(e))
        return {"success": False, "error": f"Redis Read Error: {str(e)}"}


# @router.get('/setImdAPI')
# def setImdAPI():
#     redis_state.client.select(0)
#     redis_state.client.hset("Service","update", 1)
#     return {"success": True}

@router.get('/getSystemStatus')
def get_service():
    redis_state.client.select(0)
    setupdict = json.loads(redis_state.client.hget("System", "setup"))
    if setupdict['mode'] == 'device0':
        itemdict = {
            "Redis": "redis",
            "InfluxDB": "influxdb",
            "Core": "core",
            "WebServer": "webserver",
            "A35": "sv500A35",
        }
    else:
        if setupdict['General']['useFuction']['diagnosis_main'] or setupdict['General']['useFuction']['diagnosis_sub']:
            itemdict = {
                "Redis": "redis",
                "InfluxDB": "influxdb",
                "SmartSystems": "smartsystemsservice",
                "SmartAPI": "smartsystemsrestapiservice",
                "Core": "core",
                "WebServer": "webserver",
                "A35": "sv500A35",
            }
        else:
            itemdict = {
                "Redis": "redis",
                "InfluxDB": "influxdb",
                "Core": "core",
                "WebServer": "webserver",
                "A35": "sv500A35",
            }

    statusDict = {}
    status = True
    for key, value in itemdict.items():
        statusDict[key] = is_service_active(value)
        if not statusDict[key]:
            status = False
    return {"status": status, "services":statusDict}

@router.post('/getMeterTrend/{channel}')
def getMeterTrendPost(channel: str, request: TrendRequest):
    """
    POST 방식으로 필드를 선택하여 트렌드 데이터 조회

    Body 예시:
    {
        "startDate": "2025-11-15T00:00:00+09:00",
        "endDate": "2025-11-17T23:59:59+09:00",
        "fields": ["U1", "U2", "U3", "I1", "I2", "I3", "PF1", "Freq"]
    }
    """
    start_time = datetime.now()

    if influx_state.client is None:
        return {"result": False, "error": "InfluxDB client not initialized"}

    if influx_state.error:
        print("error: InfluxDB error state")
        return {"result": False, "data": []}

    query_api = influx_state.query_api
    if not query_api:
        print("error: query_api not available")
        return {"result": False, "data": []}

    # 날짜 범위 설정
    if request.startDate and request.endDate:
        range_filter = f'from(bucket: "ntek") |> range(start: {request.startDate}, stop: {request.endDate})'
        print(f"📅 날짜 범위: {request.startDate} ~ {request.endDate}")
    else:
        range_filter = 'from(bucket: "ntek") |> range(start: -2d)'
        print(f"📅 기본 범위: -2d")

    # 필드 필터 생성
    if request.fields and len(request.fields) > 0:
        # 사용자가 지정한 필드만
        fields_filter = ' or '.join([f'r["_field"] == "{field}"' for field in request.fields])
        field_filter_query = f'|> filter(fn: (r) => {fields_filter})'
        print(f"📋 선택된 필드 ({len(request.fields)}개): {request.fields}")
    else:
        # 필드 지정 없으면 기본 주요 필드
        default_fields = ["U1", "U2", "U3", "I1", "I2", "I3", "PF1", "PF2", "PF3", "Freq", "THD_U1", "THD_I1"]
        fields_filter = ' or '.join([f'r["_field"] == "{field}"' for field in default_fields])
        field_filter_query = f'|> filter(fn: (r) => {fields_filter})'
        print(f"📋 기본 필드 사용 ({len(default_fields)}개)")

    # 쿼리 생성 (pivot 제거 - 더 빠름)
    query = (
        f'{range_filter} '
        f'|> filter(fn: (r) => r["_measurement"] == "trend" and r["channel"] == "{channel}") '
        f'{field_filter_query}'
    )

    # 쿼리 실행
    query_start = datetime.now()
    print(f"🔍 쿼리 실행 시작...")

    try:
        tables = query_api.query(org='ntek', query=query)
        query_duration = (datetime.now() - query_start).total_seconds()
        print(f"⏱️  쿼리 실행 시간: {query_duration:.3f}초")
    except Exception as e:
        print(f"❌ 쿼리 실패: {e}")
        return {"result": False, "error": str(e)}

    # 데이터 처리 (pivot을 Python에서 수행)
    process_start = datetime.now()
    data_dict = {}

    for table in tables:
        for record in table.records:
            timestamp = record.get_time()
            field = record.get_field()
            value = record.get_value()

            ts_str = timestamp.isoformat()
            if ts_str not in data_dict:
                data_dict[ts_str] = {
                    '_time': timestamp.astimezone().strftime('%Y-%m-%d %H:%M:%S'),
                    'channel': channel
                }

            data_dict[ts_str][field] = value

    # 시간순 정렬
    results = [data_dict[ts] for ts in sorted(data_dict.keys())]

    process_duration = (datetime.now() - process_start).total_seconds()
    print(f"📊 데이터 처리 시간: {process_duration:.3f}초 (레코드 수: {len(results)})")

    # 마지막 날짜
    last_date = results[-1]['_time'] if results else None

    # 전체 시간
    total_duration = (datetime.now() - start_time).total_seconds()
    print(f"🎯 전체 실행 시간: {total_duration:.3f}초")
    print(f"=" * 60)

    return {
        "result": True,
        "data": results,
        "date": last_date,
        "count": len(results),
        "fields": request.fields if request.fields else "default"
    }

@router.get('/getMeterTrend/{channel}')
def getMeterTrend(channel, startDate: str = None, endDate: str = None):
    if influx_state.client is None:
        return {"result": False}

    if influx_state.error:
        print("error1")
        return {"result": False, "data": []}
    query_api = influx_state.query_api
    if not query_api:
        print("error1")
        return {"result": False, "data": []}

    # 쿼리 범위 설정: 날짜 값이 제공되면 해당 날짜로 필터링
    range_filter = 'from(bucket: "ntek") |> range(start: -5y)'  # 기본 5년

    if startDate and endDate:
        range_filter = f'from(bucket: "ntek") |> range(start:time(v:"{startDate}"), stop:time(v:"{endDate}"))'
    query = (
        f'{range_filter} '
        f'|> filter(fn: (r) => r["_measurement"] == "trend" and r["channel"] == "{channel}") '
        f'|> sort(columns: ["_time"], desc: false) '
        f'|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'
    )

    # 쿼리 실행
    tables = query_api.query(org='ntek', query=query)

    results = []
    for table in tables:
        for record in table.records:
            record_data = record.values
            results.append(record_data)
    # print(f"Got {len(results)} records from Influx")
    last_date_query = (
        f'from(bucket: "ntek") '
        f'|> range(start: -5y) '
        f'|> filter(fn: (r) => r["_measurement"] == "trend" and r["channel"] == "{channel}") '
        f'|> last()'  # keep() 없이 사용
    )

    last_date = None
    try:
        last_date_tables = query_api.query(org='ntek', query=last_date_query)
        for table in last_date_tables:
            for record in table.records:
                # last_date = record.get_time()
                utc_time = record.get_time()  # UTC datetime 객체
                local_time = utc_time.astimezone()
                last_date = local_time.strftime('%Y-%m-%d %H:%M:%S')
                break
    except Exception as e:
        print(f"마지막 날짜 조회 오류: {e}")
    # last_date = results[-1].get('_time') if results else None

    return {"result": True, "data": results, "date":last_date}


@router.get('/getEnergyTrend/{channel}')
def getEnergyTrend(channel, startDate: str = None, endDate: str = None):
    if influx_state.client is None:
        return {"result": False}

    if influx_state.error:
        print("error1")
        return {"result": False, "data": []}
    query_api = influx_state.query_api
    if not query_api:
        print("error1")
        return {"result": False, "data": []}

    # 쿼리 범위 설정: 날짜 값이 제공되면 해당 날짜로 필터링
    range_filter = 'from(bucket: "ntek") |> range(start: -5y)'  # 기본 5년

    if startDate and endDate:
        range_filter = f'from(bucket: "ntek") |> range(start:time(v:"{startDate}"), stop:time(v:"{endDate}"))'
    query = (
        f'{range_filter} '
        f'|> filter(fn: (r) => r["_measurement"] == "energy_consumption" and r["channel"] == "{channel}") '
        f'|> sort(columns: ["_time"], desc: false) '
        f'|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'
    )

    # 쿼리 실행
    tables = query_api.query(org='ntek', query=query)
    results = []
    for table in tables:
        for record in table.records:
            record_data = record.values
            results.append(record_data)
    print(f"Got {len(results)} records from Influx")

    last_date_query = (
        f'from(bucket: "ntek") '
        f'|> range(start: -5y) '
        f'|> filter(fn: (r) => r["_measurement"] == "energy_consumption" and r["channel"] == "{channel}") '
        f'|> last()'  # keep() 없이 사용
    )

    last_date = None
    try:
        last_date_tables = query_api.query(org='ntek', query=last_date_query)
        for table in last_date_tables:
            for record in table.records:
                utc_time = record.get_time()  # UTC datetime 객체
                local_time = utc_time.astimezone()
                last_date = local_time.strftime('%Y-%m-%d %H:%M:%S')
                break
    except Exception as e:
        print(f"마지막 날짜 조회 오류: {e}")

    return {"result": True, "data": results, "date":last_date}


def fill_missing_hours_safe(hourly_data, start_time, end_time):
    """
    누락된 시간을 0으로 채우는 헬퍼 함수 (안전 버전)
    """
    # 현재 시간 (타임존 포함)
    now_with_tz = datetime.now().astimezone()

    # end_time이 현재 시간보다 크면 현재 시간으로 조정
    actual_end_time = min(end_time, now_with_tz)

    # 시간을 키로 하는 딕셔너리 생성
    data_dict = {item['hour']: item for item in hourly_data}

    filled_data = []
    current_time = start_time

    while current_time <= actual_end_time:
        hour = current_time.hour

        if hour in data_dict:
            # 기존 데이터 사용
            filled_data.append(data_dict[hour])
        else:
            # 누락된 시간은 0으로 채우기
            filled_data.append({
                'timestamp': current_time.isoformat(),
                'hour': hour,
                'value': 0,
                'date': current_time.strftime("%Y-%m-%d")
            })

        # 다음 시간으로 이동
        current_time += timedelta(hours=1)

    return filled_data


@router.get('/getHourlyEnergyData/{channel}')
def get_hourEnergy(channel: str, date: str = None):
    """
    시간별 에너지 데이터 조회 (로컬 시간 사용)
    서버의 로컬 타임존을 자동으로 사용합니다.
    """
    if influx_state.client is None:
        return {"success": False, "message": "InfluxDB client not initialized"}

    if influx_state.error:
        print("InfluxDB error detected")
        return {"success": False, "message": "InfluxDB error", "hourlyData": []}

    query_api = influx_state.query_api
    if not query_api:
        print("Query API not available")
        return {"success": False, "message": "Query API not available", "hourlyData": []}

    try:
        # 현재 로컬 시간대 오프셋 가져오기
        local_now = datetime.now()
        local_utc_offset = local_now.astimezone().utcoffset()
        local_tz = timezone(local_utc_offset)

        # 날짜 파싱 (제공되지 않으면 오늘 날짜 사용) - 로컬 시간 기준
        if date:
            # 입력된 날짜를 로컬 시간으로 파싱
            target_date = datetime.strptime(date, "%Y-%m-%d")
            # 로컬 타임존 추가
            target_date = target_date.replace(tzinfo=local_tz)
        else:
            # 현재 로컬 시간
            target_date = datetime.now(local_tz)

        # 로컬 기준 시작 시간 (00:00:00)
        start_time_local = target_date.replace(hour=0, minute=0, second=0, microsecond=0)

        # 로컬 기준 종료 시간
        if target_date.date() == datetime.now().date():
            # 오늘이면 현재 시간까지
            end_time_local = datetime.now(local_tz)
        else:
            # 과거 날짜면 그날 23:59:59까지
            end_time_local = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        # UTC로 변환 (InfluxDB 쿼리용)
        start_time_utc = start_time_local.astimezone(timezone.utc)
        end_time_utc = end_time_local.astimezone(timezone.utc)

        # RFC3339 형식으로 변환
        start_iso = start_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_iso = end_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        print(f"Local timezone offset: {local_utc_offset}")
        print(f"Query range (Local): {start_time_local} to {end_time_local}")
        print(f"Query range (UTC): {start_iso} to {end_iso}")

        # InfluxDB 쿼리: 시간별 평균값 계산
        query = f'''
            from(bucket: "ntek")
            |> range(start: {start_iso}, stop: {end_iso})
            |> filter(fn: (r) => r["_measurement"] == "energy_consumption")
            |> filter(fn: (r) => r.channel == "{channel}")
            |> filter(fn: (r) => r["_field"] == "kwh_import_consumption")
            |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
            |> sort(columns: ["_time"], desc: false)
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''

        # 쿼리 실행
        tables = query_api.query(org='ntek', query=query)

        hourly_data = []
        for table in tables:
            for record in table.records:
                # UTC 시간 가져오기
                timestamp_utc = record.get_time()

                # timezone 정보가 없으면 UTC로 설정
                if timestamp_utc.tzinfo is None:
                    timestamp_utc = timestamp_utc.replace(tzinfo=timezone.utc)

                # 로컬 시간으로 변환
                timestamp_local = timestamp_utc.astimezone(local_tz)

                # 값 추출
                value = None
                if hasattr(record, 'kwh_import_consumption') and record.kwh_import_consumption is not None:
                    value = record.kwh_import_consumption
                else:
                    # record.values 딕셔너리에서 직접 찾기
                    record_values = record.values
                    value = (record_values.get('kwh_import_consumption') or
                             record_values.get('kwh') or
                             record_values.get('power') or
                             record_values.get('consumption') or
                             0)

                # 로컬 시간 기준으로 데이터 저장
                hourly_data.append({
                    'timestamp': timestamp_local.isoformat(),  # 로컬 시간
                    'hour': timestamp_local.hour,  # 로컬 기준 시간 (0-23)
                    'value': float(value) if value is not None else 0,
                    'date': timestamp_local.strftime("%Y-%m-%d"),  # 날짜 확인용
                })

        print(f"Got {len(hourly_data)} hourly records from InfluxDB for {target_date.date()}")

        # 디버깅: 첫 몇 개 레코드 출력
        if hourly_data:
            print(f"Sample data: {hourly_data[:3]}")

        # 로컬 시간 기준으로 누락된 시간 채우기
        if len(hourly_data) > 0:
            filled_data = fill_missing_hours_safe(hourly_data, start_time_local, end_time_local)
        else:
            # 데이터가 없으면 빈 시간대 생성
            filled_data = []
            current = start_time_local
            now_local = datetime.now(local_tz)

            while current <= end_time_local and current <= now_local:
                filled_data.append({
                    'timestamp': current.isoformat(),
                    'hour': current.hour,
                    'value': 0,
                    'date': current.strftime("%Y-%m-%d")
                })
                current += timedelta(hours=1)

        # 타임존 정보 추가
        timezone_info = {
            "offset": str(local_utc_offset),
            "hours_from_utc": int(local_utc_offset.total_seconds() / 3600)
        }

        return {
            "success": True,
            "channel": channel,
            "date": target_date.strftime("%Y-%m-%d"),
            "timezone": timezone_info,
            "hourlyData": filled_data,
            "query_range": {
                "start_local": start_time_local.isoformat(),
                "end_local": end_time_local.isoformat(),
                "start_utc": start_iso,
                "end_utc": end_iso
            }
        }

    except Exception as e:
        print(f"Error fetching hourly data: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": str(e),
            "hourlyData": []
        }


@router.get('/getDailyEnergyData/{channel}')
def get_dailyEnergy(channel: str, year_month: str = None):
    """
    일별 에너지 데이터 조회 (로컬 시간 사용)
    year_month: YYYY-MM 형식 (예: 2024-03), 제공되지 않으면 현재 월
    이번 달 1일부터 오늘까지의 일별 데이터를 반환
    """
    if influx_state.client is None:
        return {"success": False, "message": "InfluxDB client not initialized"}

    if influx_state.error:
        print("InfluxDB error detected")
        return {"success": False, "message": "InfluxDB error", "dailyData": []}

    query_api = influx_state.query_api
    if not query_api:
        print("Query API not available")
        return {"success": False, "message": "Query API not available", "dailyData": []}

    try:
        # 현재 로컬 시간대 오프셋 가져오기
        local_now = datetime.now()
        local_utc_offset = local_now.astimezone().utcoffset()
        local_tz = timezone(local_utc_offset)

        # 년월 파싱 (제공되지 않으면 현재 월 사용)
        if year_month:
            year, month = map(int, year_month.split('-'))
            target_date = datetime(year, month, 1, tzinfo=local_tz)
        else:
            # 현재 월의 1일
            now_local = datetime.now(local_tz)
            target_date = datetime(now_local.year, now_local.month, 1, tzinfo=local_tz)

        # 시작 시간: 해당 월 1일 00:00:00
        start_time_local = target_date

        # 종료 시간: 현재 월이면 오늘까지, 과거 월이면 해당 월 마지막 날까지
        now_local = datetime.now(local_tz)
        if target_date.year == now_local.year and target_date.month == now_local.month:
            # 현재 월이면 오늘 23:59:59까지
            end_time_local = now_local.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            # 과거 월이면 해당 월 마지막 날까지
            if target_date.month == 12:
                next_month = datetime(target_date.year + 1, 1, 1, tzinfo=local_tz)
            else:
                next_month = datetime(target_date.year, target_date.month + 1, 1, tzinfo=local_tz)
            end_time_local = next_month - timedelta(seconds=1)

        # UTC로 변환
        start_time_utc = start_time_local.astimezone(timezone.utc)
        end_time_utc = end_time_local.astimezone(timezone.utc)

        # RFC3339 형식으로 변환
        start_iso = start_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_iso = end_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        print(f"Daily query range (Local): {start_time_local} to {end_time_local}")
        print(f"Daily query range (UTC): {start_iso} to {end_iso}")

        # InfluxDB 쿼리: 일별 합계값 계산
        query = f'''
            from(bucket: "ntek")
            |> range(start: {start_iso}, stop: {end_iso})
            |> filter(fn: (r) => r["_measurement"] == "energy_consumption")
            |> filter(fn: (r) => r.channel == "{channel}")
            |> filter(fn: (r) => r["_field"] == "kwh_import_consumption")
            |> aggregateWindow(every: 1d, fn: sum, createEmpty: false)
            |> sort(columns: ["_time"], desc: false)
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''

        # 쿼리 실행
        tables = query_api.query(org='ntek', query=query)

        daily_data = []
        for table in tables:
            for record in table.records:
                # UTC 시간 가져오기
                timestamp_utc = record.get_time()

                # timezone 정보가 없으면 UTC로 설정
                if timestamp_utc.tzinfo is None:
                    timestamp_utc = timestamp_utc.replace(tzinfo=timezone.utc)

                # 로컬 시간으로 변환
                timestamp_local = timestamp_utc.astimezone(local_tz)

                # 값 추출
                value = None
                if hasattr(record, 'kwh_import_consumption') and record.kwh_import_consumption is not None:
                    value = record.kwh_import_consumption
                else:
                    record_values = record.values
                    value = (record_values.get('kwh_import_consumption') or
                             record_values.get('kwh') or
                             record_values.get('power') or
                             record_values.get('consumption') or
                             0)

                daily_data.append({
                    'timestamp': timestamp_local.isoformat(),
                    'date': timestamp_local.strftime("%Y-%m-%d"),
                    'day': timestamp_local.day,
                    'value': float(value) if value is not None else 0,
                })

        print(f"Got {len(daily_data)} daily records from InfluxDB for {target_date.strftime('%Y-%m')}")

        # 누락된 날짜 채우기
        filled_data = fill_missing_days(daily_data, start_time_local, end_time_local)

        # 타임존 정보 추가
        timezone_info = {
            "offset": str(local_utc_offset),
            "hours_from_utc": int(local_utc_offset.total_seconds() / 3600)
        }

        return {
            "success": True,
            "channel": channel,
            "year_month": target_date.strftime("%Y-%m"),
            "timezone": timezone_info,
            "dailyData": filled_data,
            "query_range": {
                "start_local": start_time_local.isoformat(),
                "end_local": end_time_local.isoformat(),
                "start_utc": start_iso,
                "end_utc": end_iso
            }
        }

    except Exception as e:
        print(f"Error fetching daily data: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": str(e),
            "dailyData": []
        }


@router.get('/getMonthlyEnergyData/{channel}')
def get_monthlyEnergy(channel: str, year: str = None):
    """
    월별 에너지 데이터 조회 (로컬 시간 사용)
    year: YYYY 형식 (예: 2024), 제공되지 않으면 현재 년도
    올해 1월부터 이번 달까지의 월별 데이터를 반환
    """
    if influx_state.client is None:
        return {"success": False, "message": "InfluxDB client not initialized"}

    if influx_state.error:
        print("InfluxDB error detected")
        return {"success": False, "message": "InfluxDB error", "monthlyData": []}

    query_api = influx_state.query_api
    if not query_api:
        print("Query API not available")
        return {"success": False, "message": "Query API not available", "monthlyData": []}

    try:
        # 현재 로컬 시간대 오프셋 가져오기
        local_now = datetime.now()
        local_utc_offset = local_now.astimezone().utcoffset()
        local_tz = timezone(local_utc_offset)

        # 년도 파싱 (제공되지 않으면 현재 년도 사용)
        if year:
            target_year = int(year)
        else:
            target_year = datetime.now(local_tz).year

        # 시작 시간: 해당 년도 1월 1일 00:00:00
        start_time_local = datetime(target_year, 1, 1, tzinfo=local_tz)

        # 종료 시간: 현재 년도면 이번 달까지, 과거 년도면 12월까지
        now_local = datetime.now(local_tz)
        if target_year == now_local.year:
            # 현재 년도면 이번 달 마지막 날까지
            if now_local.month == 12:
                next_month = datetime(target_year + 1, 1, 1, tzinfo=local_tz)
            else:
                next_month = datetime(target_year, now_local.month + 1, 1, tzinfo=local_tz)
            end_time_local = next_month - timedelta(seconds=1)
        else:
            # 과거 년도면 12월 31일까지
            end_time_local = datetime(target_year + 1, 1, 1, tzinfo=local_tz) - timedelta(seconds=1)

        # UTC로 변환
        start_time_utc = start_time_local.astimezone(timezone.utc)
        end_time_utc = end_time_local.astimezone(timezone.utc)

        # RFC3339 형식으로 변환
        start_iso = start_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_iso = end_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        print(f"Monthly query range (Local): {start_time_local} to {end_time_local}")
        print(f"Monthly query range (UTC): {start_iso} to {end_iso}")

        # InfluxDB 쿼리: 월별 합계값 계산
        query = f'''
            from(bucket: "ntek")
            |> range(start: {start_iso}, stop: {end_iso})
            |> filter(fn: (r) => r["_measurement"] == "energy_consumption")
            |> filter(fn: (r) => r.channel == "{channel}")
            |> filter(fn: (r) => r["_field"] == "kwh_import_consumption")
            |> aggregateWindow(every: 1mo, fn: sum, createEmpty: false)
            |> sort(columns: ["_time"], desc: false)
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''

        # 쿼리 실행
        tables = query_api.query(org='ntek', query=query)

        monthly_data = []
        for table in tables:
            for record in table.records:
                # UTC 시간 가져오기
                timestamp_utc = record.get_time()

                # timezone 정보가 없으면 UTC로 설정
                if timestamp_utc.tzinfo is None:
                    timestamp_utc = timestamp_utc.replace(tzinfo=timezone.utc)

                # 로컬 시간으로 변환
                timestamp_local = timestamp_utc.astimezone(local_tz)

                # 값 추출
                value = None
                if hasattr(record, 'kwh_import_consumption') and record.kwh_import_consumption is not None:
                    value = record.kwh_import_consumption
                else:
                    record_values = record.values
                    value = (record_values.get('kwh_import_consumption') or
                             record_values.get('kwh') or
                             record_values.get('power') or
                             record_values.get('consumption') or
                             0)

                monthly_data.append({
                    'timestamp': timestamp_local.isoformat(),
                    'year_month': timestamp_local.strftime("%Y-%m"),
                    'month': timestamp_local.month,
                    'value': float(value) if value is not None else 0,
                })

        print(f"Got {len(monthly_data)} monthly records from InfluxDB for {target_year}")

        # 누락된 월 채우기
        filled_data = fill_missing_months(monthly_data, start_time_local, end_time_local)

        # 타임존 정보 추가
        timezone_info = {
            "offset": str(local_utc_offset),
            "hours_from_utc": int(local_utc_offset.total_seconds() / 3600)
        }

        return {
            "success": True,
            "channel": channel,
            "year": target_year,
            "timezone": timezone_info,
            "monthlyData": filled_data,
            "query_range": {
                "start_local": start_time_local.isoformat(),
                "end_local": end_time_local.isoformat(),
                "start_utc": start_iso,
                "end_utc": end_iso
            }
        }

    except Exception as e:
        print(f"Error fetching monthly data: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": str(e),
            "monthlyData": []
        }


def fill_missing_days(data, start_time, end_time):
    """누락된 날짜를 0으로 채워주는 함수"""
    # 기존 데이터를 날짜별로 매핑
    data_map = {item['date']: item for item in data}

    filled_data = []
    current = start_time
    now_local = datetime.now(start_time.tzinfo)

    while current <= end_time and current.date() <= now_local.date():
        date_str = current.strftime("%Y-%m-%d")

        if date_str in data_map:
            filled_data.append(data_map[date_str])
        else:
            filled_data.append({
                'timestamp': current.isoformat(),
                'date': date_str,
                'day': current.day,
                'value': 0
            })

        current += timedelta(days=1)

    return filled_data


def fill_missing_months(data, start_time, end_time):
    """누락된 월을 0으로 채워주는 함수"""
    # 기존 데이터를 년월별로 매핑
    data_map = {item['year_month']: item for item in data}

    filled_data = []
    current = start_time
    now_local = datetime.now(start_time.tzinfo)

    while current <= end_time and (current.year < now_local.year or
                                   (current.year == now_local.year and current.month <= now_local.month)):
        year_month_str = current.strftime("%Y-%m")

        if year_month_str in data_map:
            filled_data.append(data_map[year_month_str])
        else:
            filled_data.append({
                'timestamp': current.isoformat(),
                'year_month': year_month_str,
                'month': current.month,
                'value': 0
            })

        # 다음 달로 이동
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    return filled_data


@router.get('/getLoadFactorData/{channel}')
def get_load_factor_data(channel: str, date: str = None):
    """
    부하율 계산을 위한 피상전력(S4) 시간별 평균 데이터 조회 (로컬 시간 사용)
    서버의 로컬 타임존을 자동으로 사용합니다.
    """
    if influx_state.client is None:
        return {"success": False, "message": "InfluxDB client not initialized"}

    if influx_state.error:
        print("InfluxDB error detected")
        return {"success": False, "message": "InfluxDB error", "loadFactorData": []}

    query_api = influx_state.query_api
    if not query_api:
        print("Query API not available")
        return {"success": False, "message": "Query API not available", "loadFactorData": []}

    try:
        # 현재 로컬 시간대 오프셋 가져오기
        local_now = datetime.now()
        local_utc_offset = local_now.astimezone().utcoffset()
        local_tz = timezone(local_utc_offset)

        # 날짜 파싱 (제공되지 않으면 오늘 날짜 사용) - 로컬 시간 기준
        if date:
            # 입력된 날짜를 로컬 시간으로 파싱
            target_date = datetime.strptime(date, "%Y-%m-%d")
            # 로컬 타임존 추가
            target_date = target_date.replace(tzinfo=local_tz)
        else:
            # 현재 로컬 시간
            target_date = datetime.now(local_tz)

        # 로컬 기준 시작 시간 (00:00:00)
        start_time_local = target_date.replace(hour=0, minute=0, second=0, microsecond=0)

        # 로컬 기준 종료 시간
        if target_date.date() == datetime.now().date():
            # 오늘이면 현재 시간까지
            end_time_local = datetime.now(local_tz)
        else:
            # 과거 날짜면 그날 23:59:59까지
            end_time_local = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        # ✅ trend는 로컬타임으로 저장되므로 UTC 변환 없이 직접 사용
        # RFC3339 형식으로 변환 (로컬 시간 그대로)

        start_time_utc = start_time_local.astimezone(timezone.utc)
        end_time_utc = end_time_local.astimezone(timezone.utc)
        start_iso = start_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_iso = end_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        # 만약 timezone 정보가 없다면 Z를 붙임 (InfluxDB 호환성)
        if not start_iso.endswith('Z') and '+' not in start_iso and '-' not in start_iso[-6:]:
            start_iso = start_time_local.strftime("%Y-%m-%dT%H:%M:%SZ")
            end_iso = end_time_local.strftime("%Y-%m-%dT%H:%M:%SZ")

        print(f"Local timezone offset: {local_utc_offset}")
        print(f"Load Factor Query range (Local): {start_time_local} to {end_time_local}")
        print(f"Load Factor Query range (ISO): {start_iso} to {end_iso}")

        # InfluxDB 쿼리: 피상전력(S4) 시간별 평균값 계산
        # ✅ trend measurement는 로컬타임으로 저장되므로 직접 시간 비교
        query = f'''
            from(bucket: "ntek")
            |> range(start: {start_iso}, stop: {end_iso})
            |> filter(fn: (r) => r["_measurement"] == "trend")
            |> filter(fn: (r) => r.channel == "{channel}")
            |> filter(fn: (r) => r["_field"] == "S4")
            |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
            |> sort(columns: ["_time"], desc: false)
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''

        # 쿼리 실행
        tables = query_api.query(org='ntek', query=query)

        load_factor_data = []
        for table in tables:
            for record in table.records:
                # ✅ trend는 로컬타임으로 저장되므로 시간 변환 처리 수정
                timestamp_utc = record.get_time()

                # timezone 정보 처리
                if timestamp_utc.tzinfo is None:
                    # timezone 정보가 없으면 로컬 타임존으로 가정
                    timestamp_local = timestamp_utc.replace(tzinfo=local_tz)
                else:
                    # 이미 timezone 정보가 있으면 로컬 시간으로 변환
                    timestamp_local = timestamp_utc.astimezone(local_tz)

                # 피상전력 값 추출
                apparent_power = None
                if hasattr(record, 'S4') and record.S4 is not None:
                    apparent_power = record.S4
                else:
                    # record.values 딕셔너리에서 직접 찾기
                    record_values = record.values
                    apparent_power = (record_values.get('S4') or
                                      record_values.get('apparent_power') or
                                      0)

                # 로컬 시간 기준으로 데이터 저장
                load_factor_data.append({
                    'timestamp': timestamp_local.isoformat(),  # 로컬 시간
                    'hour': timestamp_local.hour,  # 로컬 기준 시간 (0-23)
                    'apparent_power': float(apparent_power) if apparent_power is not None else 0,
                    'date': timestamp_local.strftime("%Y-%m-%d"),  # 날짜 확인용
                })

        print(f"Got {len(load_factor_data)} load factor records from InfluxDB for {target_date.date()}")

        # 디버깅: 첫 몇 개 레코드 출력
        if load_factor_data:
            print(f"Sample load factor data: {load_factor_data[:3]}")

        # 로컬 시간 기준으로 누락된 시간 채우기
        if len(load_factor_data) > 0:
            filled_data = fill_missing_load_factor_hours(load_factor_data, start_time_local, end_time_local)
        else:
            # 데이터가 없으면 빈 시간대 생성
            filled_data = []
            current = start_time_local
            now_local = datetime.now(local_tz)

            while current <= end_time_local and current <= now_local:
                filled_data.append({
                    'timestamp': current.isoformat(),
                    'hour': current.hour,
                    'apparent_power': 0,
                    'date': current.strftime("%Y-%m-%d")
                })
                current += timedelta(hours=1)

        # 타임존 정보 추가
        timezone_info = {
            "offset": str(local_utc_offset),
            "hours_from_utc": int(local_utc_offset.total_seconds() / 3600)
        }

        return {
            "success": True,
            "channel": channel,
            "date": target_date.strftime("%Y-%m-%d"),
            "timezone": timezone_info,
            "loadFactorData": filled_data,
            "query_range": {
                "start_local": start_time_local.isoformat(),
                "end_local": end_time_local.isoformat(),
                "start_iso": start_iso,
                "end_iso": end_iso
            }
        }

    except Exception as e:
        print(f"Error fetching load factor data: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": str(e),
            "loadFactorData": []
        }


def fill_missing_load_factor_hours(data, start_time, end_time):
    """누락된 시간의 피상전력 데이터를 0으로 채워주는 함수"""
    # 기존 데이터를 시간별로 매핑
    data_map = {}
    for item in data:
        hour_key = item['hour']
        data_map[hour_key] = item

    filled_data = []
    current = start_time
    now_local = datetime.now(start_time.tzinfo)

    while current <= end_time and current <= now_local:
        hour = current.hour

        if hour in data_map:
            filled_data.append(data_map[hour])
        else:
            filled_data.append({
                'timestamp': current.isoformat(),
                'hour': hour,
                'apparent_power': 0,
                'date': current.strftime("%Y-%m-%d")
            })

        current += timedelta(hours=1)

    return filled_data


@router.get('/getLoadFactorCalculated/{channel}')
def get_load_factor_calculated(channel: str, date: str = None):
    """
    부하율을 계산해서 반환하는 엔드포인트
    Redis에서 채널별 정격 KVA를 가져와서 부하율 계산
    """
    try:
        # Redis에서 설정 정보 가져오기
        redis_state.client.select(0)
        setupStr = redis_state.client.hget("System", "setup")

        if not setupStr:
            return {"success": False, "message": "System setup not found in Redis"}

        setting = json.loads(setupStr)

        # 채널 정보 찾기
        channel_dict = next(
            (channel_data for channel_data in setting.get("channel", [])
             if channel_data.get("channel", "") == channel),
            {}  # 기본값: 빈 dict
        )

        # n_kva 값 검증 및 변환
        n_kva = channel_dict.get("n_kva")
        try:
            ratedKVA = int(n_kva) if n_kva else 0
            if ratedKVA <= 0:
                return {
                    "success": False,
                    "message": f"Channel '{channel}' has missing or invalid n_kva value"
                }
        except (ValueError, TypeError):
            return {
                "success": False,
                "message": f"Channel '{channel}' has invalid n_kva value: {n_kva}"
            }

        # 피상전력 데이터 가져오기
        load_factor_response = get_load_factor_data(channel, date)

        if not load_factor_response["success"]:
            return load_factor_response

        load_factor_data = load_factor_response["loadFactorData"]

        # 데이터가 없는 경우 체크
        if not load_factor_data:
            return {
                "success": False,
                "message": "No load factor data available for the specified date"
            }

        # 부하율 계산
        calculated_data = []
        total_load_factor = 0
        valid_hours = 0

        for item in load_factor_data:
            apparent_power = item["apparent_power"]

            # 부하율 계산: (실제 피상전력 / 정격 KVA) × 100
            if apparent_power > 0:
                load_factor_percent = ((apparent_power/1000) / ratedKVA) * 100
                total_load_factor += load_factor_percent
                valid_hours += 1
            else:
                load_factor_percent = 0

            calculated_data.append({
                'timestamp': item['timestamp'],
                'hour': item['hour'],
                'apparent_power': apparent_power,
                'load_factor_percent': round(load_factor_percent, 2),
                'date': item['date']
            })

        # 평균 부하율 계산
        average_load_factor = round(total_load_factor / valid_hours, 2) if valid_hours > 0 else 0

        # 최대 부하율 계산
        max_load_factor = max([item['load_factor_percent'] for item in calculated_data], default=0)

        # 최소 부하율 계산 (0 제외)
        non_zero_factors = [item['load_factor_percent'] for item in calculated_data if item['load_factor_percent'] > 0]
        min_load_factor = min(non_zero_factors, default=0)

        return {
            "success": True,
            "channel": channel,
            "date": load_factor_response["date"],
            "rated_kva": ratedKVA,
            "timezone": load_factor_response["timezone"],
            "loadFactorData": calculated_data,
            "statistics": {
                "average_load_factor": average_load_factor,
                "max_load_factor": max_load_factor,
                "min_load_factor": min_load_factor,
                "valid_hours": valid_hours,
                "total_hours": len(calculated_data)
            },
            "query_range": load_factor_response["query_range"]
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "message": f"Invalid JSON in Redis setup: {str(e)}"
        }
    except Exception as e:
        print(f"Error calculating load factor: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Internal server error: {str(e)}",
            "loadFactorData": []
        }


@router.get('/getWeeklyLoadFactorData/{channel}')
def get_weekly_load_factor_data(channel: str, end_date: str = None, days: int = 7):
    """
    주간 부하율 데이터 조회 (히트맵 패턴 분석용)
    end_date: 종료 날짜 (YYYY-MM-DD), 기본값은 오늘
    days: 조회할 일수 (기본값 7일)
    """
    try:
        # Redis에서 설정 정보 가져오기
        redis_state.client.select(0)
        setupStr = redis_state.client.hget("System", "setup")

        if not setupStr:
            return {"success": False, "message": "System setup not found in Redis"}

        setting = json.loads(setupStr)

        # 채널 정보 찾기
        channel_dict = next(
            (channel_data for channel_data in setting.get("channel", [])
             if channel_data.get("channel", "") == channel),
            {}
        )

        # n_kva 값 검증
        n_kva = channel_dict.get("n_kva")
        try:
            ratedKVA = int(n_kva) if n_kva else 0
            if ratedKVA <= 0:
                return {
                    "success": False,
                    "message": f"Channel '{channel}' has missing or invalid n_kva value"
                }
        except (ValueError, TypeError):
            return {
                "success": False,
                "message": f"Channel '{channel}' has invalid n_kva value: {n_kva}"
            }

        if influx_state.client is None:
            return {"success": False, "message": "InfluxDB client not initialized"}

        if influx_state.error:
            return {"success": False, "message": "InfluxDB error", "weeklyData": []}

        query_api = influx_state.query_api
        if not query_api:
            return {"success": False, "message": "Query API not available", "weeklyData": []}

        # 현재 로컬 시간대 설정
        local_now = datetime.now()
        local_utc_offset = local_now.astimezone().utcoffset()
        local_tz = timezone(local_utc_offset)

        # 종료 날짜 설정
        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=local_tz)
        else:
            end_date_obj = datetime.now(local_tz)

        # 시작 날짜 계산
        start_date_obj = end_date_obj - timedelta(days=days - 1)

        # 시간 범위 설정 (시작일 00:00:00 ~ 종료일 23:59:59)
        start_time_local = start_date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time_local = end_date_obj.replace(hour=23, minute=59, second=59, microsecond=999999)

        # UTC로 변환
        start_time_utc = start_time_local.astimezone(timezone.utc)
        end_time_utc = end_time_local.astimezone(timezone.utc)
        start_iso = start_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_iso = end_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        print(f"Weekly Load Factor Query range (Local): {start_time_local} to {end_time_local}")
        print(f"Weekly Load Factor Query range (UTC): {start_iso} to {end_iso}")

        # InfluxDB 쿼리: 주간 피상전력 시간별 평균
        query = f'''
            from(bucket: "ntek")
            |> range(start: {start_iso}, stop: {end_iso})
            |> filter(fn: (r) => r["_measurement"] == "trend")
            |> filter(fn: (r) => r.channel == "{channel}")
            |> filter(fn: (r) => r["_field"] == "S4")
            |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
            |> sort(columns: ["_time"], desc: false)
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''

        # 쿼리 실행
        tables = query_api.query(org='ntek', query=query)

        weekly_data = []
        for table in tables:
            for record in table.records:
                # 시간 처리
                timestamp_raw = record.get_time()
                if timestamp_raw.tzinfo is None:
                    timestamp_utc = timestamp_raw.replace(tzinfo=timezone.utc)
                    timestamp_local = timestamp_utc.astimezone(local_tz)
                else:
                    timestamp_local = timestamp_raw.astimezone(local_tz)

                # 피상전력 값 추출
                apparent_power = None
                if hasattr(record, 'S4') and record.S4 is not None:
                    apparent_power = record.S4
                else:
                    record_values = record.values
                    apparent_power = (record_values.get('S4') or 0)

                # 부하율 계산
                if apparent_power and apparent_power > 0:
                    load_factor_percent = ((apparent_power/1000) / ratedKVA) * 100
                else:
                    load_factor_percent = 0

                weekly_data.append({
                    'timestamp': timestamp_local.isoformat(),
                    'date': timestamp_local.strftime("%Y-%m-%d"),
                    'hour': timestamp_local.hour,
                    'day_of_week': timestamp_local.weekday(),  # 0=월요일, 6=일요일
                    'apparent_power': float(apparent_power) if apparent_power is not None else 0,
                    'load_factor_percent': round(load_factor_percent, 2),
                })

        print(f"Got {len(weekly_data)} weekly load factor records from InfluxDB")

        # 일별 통계 계산
        daily_stats = {}
        for item in weekly_data:
            date = item['date']
            if date not in daily_stats:
                daily_stats[date] = {
                    'date': date,
                    'day_of_week': item['day_of_week'],
                    'avg_load_factor': 0,
                    'max_load_factor': 0,
                    'min_load_factor': float('inf'),
                    'overload_hours': 0,
                    'data_points': 0
                }

            stats = daily_stats[date]
            stats['max_load_factor'] = max(stats['max_load_factor'], item['load_factor_percent'])

            if item['load_factor_percent'] > 0:
                stats['min_load_factor'] = min(stats['min_load_factor'], item['load_factor_percent'])

            if item['load_factor_percent'] > 100:
                stats['overload_hours'] += 1

            stats['data_points'] += 1

        # 평균 계산
        for date, stats in daily_stats.items():
            day_data = [item for item in weekly_data if item['date'] == date and item['load_factor_percent'] > 0]
            if day_data:
                stats['avg_load_factor'] = round(sum(item['load_factor_percent'] for item in day_data) / len(day_data), 2)
            if stats['min_load_factor'] == float('inf'):
                stats['min_load_factor'] = 0

        # 전체 통계 계산
        all_load_factors = [item['load_factor_percent'] for item in weekly_data if item['load_factor_percent'] > 0]

        overall_stats = {
            "total_hours": len(weekly_data),
            "valid_hours": len(all_load_factors),
            "average_load_factor": round(sum(all_load_factors) / len(all_load_factors), 2) if all_load_factors else 0,
            "max_load_factor": max(all_load_factors, default=0),
            "min_load_factor": min(all_load_factors, default=0),
            "overload_hours": len([item for item in weekly_data if item['load_factor_percent'] > 100]),
        }

        # 부하율 분포 계산
        distribution = {
            "light": len([item for item in weekly_data if 0 < item['load_factor_percent'] <= 50]),
            "medium": len([item for item in weekly_data if 50 < item['load_factor_percent'] <= 80]),
            "high": len([item for item in weekly_data if 80 < item['load_factor_percent'] <= 100]),
            "overload": len([item for item in weekly_data if item['load_factor_percent'] > 100]),
        }

        # 타임존 정보
        timezone_info = {
            "offset": str(local_utc_offset),
            "hours_from_utc": int(local_utc_offset.total_seconds() / 3600)
        }

        return {
            "success": True,
            "channel": channel,
            "rated_kva": ratedKVA,
            "start_date": start_time_local.strftime("%Y-%m-%d"),
            "end_date": end_time_local.strftime("%Y-%m-%d"),
            "days_requested": days,
            "timezone": timezone_info,
            "weeklyData": weekly_data,
            "dailyStats": list(daily_stats.values()),
            "overallStats": overall_stats,
            "distribution": distribution,
            "query_range": {
                "start_local": start_time_local.isoformat(),
                "end_local": end_time_local.isoformat(),
                "start_utc": start_iso,
                "end_utc": end_iso
            }
        }

    except json.JSONDecodeError as e:
        return {"success": False, "message": f"Invalid JSON in Redis setup: {str(e)}"}
    except Exception as e:
        print(f"Error fetching weekly load factor data: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Internal server error: {str(e)}",
            "weeklyData": []
        }


@router.get('/getHeatmapLoadFactorData/{channel}')
def get_heatmap_load_factor_data(channel: str, weeks: int = 4):
    """
    히트맵 전용 부하율 데이터 조회 (더 긴 기간, 패턴 분석용)
    weeks: 조회할 주수 (기본값 4주)
    """
    try:
        # 기본적으로 weekly 엔드포인트 활용
        days = weeks * 7
        result = get_weekly_load_factor_data(channel, None, days)

        if not result["success"]:
            return result

        weekly_data = result["weeklyData"]

        # 히트맵용 데이터 구조로 변환
        # [hour, day_of_week, load_factor_percent] 형태
        heatmap_data = []

        # 요일별, 시간별 평균 계산
        pattern_data = {}
        for item in weekly_data:
            hour = item['hour']
            day_of_week = item['day_of_week']
            load_factor = item['load_factor_percent']

            key = f"{day_of_week}-{hour}"
            if key not in pattern_data:
                pattern_data[key] = []
            pattern_data[key].append(load_factor)

        # 평균값으로 히트맵 데이터 생성
        for day_of_week in range(7):  # 0=월요일 ~ 6=일요일
            for hour in range(24):
                key = f"{day_of_week}-{hour}"
                if key in pattern_data:
                    avg_load = sum(pattern_data[key]) / len(pattern_data[key])
                else:
                    avg_load = 0

                # [x, y, value] 형태: [hour, day_of_week, load_factor]
                heatmap_data.append([hour, day_of_week, round(avg_load, 1)])

        return {
            "success": True,
            "channel": channel,
            "weeks_analyzed": weeks,
            "total_data_points": len(weekly_data),
            "heatmapData": heatmap_data,
            "overallStats": result["overallStats"],
            "distribution": result["distribution"],
            "period": {
                "start_date": result["start_date"],
                "end_date": result["end_date"]
            }
        }

    except Exception as e:
        print(f"Error creating heatmap load factor data: {e}")
        return {
            "success": False,
            "message": str(e),
            "heatmapData": []
        }


def cleanup_executor():
    """프로그램 종료 시 호출"""
    global executor
    if executor:
        executor.shutdown(wait=True)
        executor = None