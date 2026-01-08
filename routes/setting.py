from fastapi import APIRouter, Request, UploadFile, File, BackgroundTasks
from starlette.background import BackgroundTask
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
import os, httpx, csv, psutil, struct, tempfile
import ujson as json
import shutil, logging, subprocess, asyncio
from datetime import datetime
from states.global_state import influx_state, redis_state, aesState,os_spec
from collections import defaultdict
from typing import Dict, Any, List
from routes.util import get_mac_address, sysService, is_service_active, getVersions, saveLog, get_lastpost, Post, save_post, WAVEFORM_PATHS
from routes.api import parameter_options
from .RedisBinary import Command, CmdType, ItemType
import pyinotify, threading
import asyncio, time

import sqlite3

# Path 객체 절대경로
from pathlib import Path
base_dir = Path(__file__).resolve().parent
SETTING_FOLDER = base_dir.parent.parent / "config"  # ⬅️ 두 단계 상위로
BEARINGDB_PATH = SETTING_FOLDER / "bearing.db"
setting_timeout = httpx.Timeout(
    connect=2.0,  # 연결에는 5초
    read=30.0,     # 응답 읽기는 2초
    write=2.0,    # 요청 전송은 5초
    pool=5.0      # 연결 풀은 5초
)

router = APIRouter()

def command_to_binary(command: Command) -> bytes:
    """Command 객체를 바이너리로 변환 (C 구조체와 호환)"""
    # C의 int는 보통 4바이트, enum도 int로 처리
    # 구조: int(4) + int(4) + int(4) = 12 bytes
    return struct.pack('iii', command.type, command.cmd, command.item)


def binary_to_command(binary_data: bytes) -> Command:
    """바이너리 데이터를 Command 객체로 변환"""
    if len(binary_data) != 12:
        raise ValueError("Invalid binary data size")

    type_val, cmd_val, item_val = struct.unpack('iii', binary_data)
    return Command(type=type_val, cmd=CmdType(cmd_val), item=ItemType(item_val))


def read_mac_plain(filepath):
    """파일에서 MAC 주소를 구분자 없이 읽기"""
    with open(filepath, 'rb') as f:
        mac_bytes = f.read(6)

        if len(mac_bytes) != 6:
            raise ValueError(f"잘못된 MAC 주소 길이: {len(mac_bytes)} bytes")

        # 구분자 없이 반환
        return mac_bytes.hex().lower()  # 더 간단한 방법

@router.get('/getMac')
def getMacAddr():
    devMac = get_mac_address()
    return {'success':True, 'mac': devMac}

@router.get('/checkInitDB')
async def checkInitDB():
    file_path = os.path.join(SETTING_FOLDER, 'influx.json')
    if not os.path.exists(file_path):
        return {'result': False}
    else:
        return {'result': True}


@router.get('/initDB')
async def initInflux(background_tasks: BackgroundTasks):
    file_path = os.path.join(SETTING_FOLDER, 'influx.json')
    data = {
        "username": "admin",
        "password": "ntek9135",
        "org": "ntek",
        "bucket": "nteks",
        "retentionPeriodSeconds": 0
    }
    try:
        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.post(f"http://127.0.0.1:8086/api/v2/setup", json=data)
            resData = response.json()
            if resData.get("code") == "conflict":
                logging.warning("⚠️ InfluxDB already initialized")
                return {"success": False, "message": "InfluxDB has already been initialized"}

            auth = resData.get("auth")
            org = resData.get("org")

            if not auth or not org:
                logging.error(f"❌ Unexpected response: {resData}")
                return {"success": False, "message": f"InfluxDB setup failed: {resData}"}

            token = auth.get("token")
            org_id = org.get("id")

            cipher = aesState.encrypt(token)
            influxdata = {
                "token": cipher,
                "org": org.get("name"),
                "org_id": org_id,
                "retention": data.get("retentionPeriodSeconds")
            }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(influxdata, f, indent=4)

        # init_influx()  # ✅ 초기화 수행 (json 생성 + client 전역 등록)
        if influx_state.client is None:
            return {"result": False}

        if influx_state.error:
            return {"success": False, "message": influx_state.error}
        set_cli = init_influxcli()
        sysService('restart', 'InfluxDB')
        background_tasks.add_task(complete_influx_setup)

        if set_cli['status']:
            return {"success": True, "message": "InfluxDB initialized successfully"}
        else:
            return {"success": True, "message": "InfluxDB initialized but check Influx CLI environment variables"}
    except Exception as e:
        logging.error(f"❌ Influxdb Init Error: {e}")
        influx_state._client = None
        influx_state._error = f"Exception during init: {str(e)}"
        return {"success": False, "message": str(e)}


@router.get("/initInfluxCLI")
def init_influxcli():
    try:
        config = aesState.getInflux()
        token = aesState.decrypt(config["cipher"])

        # 토큰 검증
        if not token or token == "":
            return {
                "status": False,
                "message": "No exist Influxdb Token"
            }

        # 더 안전한 이스케이프 처리
        import shlex
        token_escaped = shlex.quote(token)
        org_escaped = shlex.quote(config['org'])

        # 파일 생성, 권한 설정, source 적용을 한 번에
        full_command = f"""
cat > /etc/profile.d/influx.sh << 'EOF'
export INFLUX_TOKEN={token_escaped}
export INFLUX_HOST="http://localhost:8086"
export INFLUX_ORG={org_escaped}
export INFLUX_BUCKET="nteks"
EOF
chmod +x /etc/profile.d/influx.sh
source /etc/profile.d/influx.sh
"""

        result = subprocess.run(
            ['sudo', 'bash', '-c', full_command],
            check=True,
            capture_output=True,
            text=True
        )

        # 현재 프로세스 환경변수 설정
        os.environ.update({
            'INFLUX_TOKEN': token,
            'INFLUX_HOST': "http://localhost:8086",
            'INFLUX_ORG': config['org'],
            'INFLUX_BUCKET': "nteks"
        })

        return {
            "status": True,
            "message": "InfluxDB CLI environment initiated.",
            "file": "/etc/profile.d/influx.sh"
        }

    except subprocess.CalledProcessError as e:
        return {
            "status": False,
            "message": f"Command failed: {e.stderr if e.stderr else str(e)}"
        }
    except Exception as e:
        return {
            "status": False,
            "message": f"Error: {str(e)}"
        }


async def complete_influx_setup():
    """백그라운드에서 InfluxDB 재시작 대기 후 버킷 생성 및 서비스 재시작"""
    try:
        # redis_state.client.select(0)
        sysMode = redis_state.client.hget("System", "mode")
        redis_state.client.hset("influx_init", "status", "WAITING")

        # InfluxDB 재시작 완료 대기
        await asyncio.sleep(3)
        influx_ready = False

        for i in range(10):
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    health = await client.get(f"http://127.0.0.1:8086/health")
                    if health.status_code == 200:
                        influx_ready = True
                        logging.debug("✅ InfluxDB is ready")
                        break
            except:
                pass
            await asyncio.sleep(1)

        if not influx_ready:
            redis_state.client.hset("influx_init", "status", "FAIL")
            return

        # 버킷 생성
        bucket_result = await create_influx_bucket("ntek", 365)

        if not bucket_result["success"]:
            redis_state.client.hset("influx_init", "status", "P.FAIL")
            logging.warning(f"⚠️ Bucket creation failed: {bucket_result['message']}")

        # 다운샘플링 설정 (버킷 + Task) 추가
        downsampling_result = await setup_downsampling()
        if not downsampling_result["success"]:
            logging.warning(f"⚠️ Downsampling setup had issues: {downsampling_result['message']}")
        else:
            logging.info("✅ Downsampling buckets and tasks configured")

        bucket_result2 = await create_influx_bucket("ntek30", 30)

        if not bucket_result2["success"]:
            logging.warning(f"⚠️ Bucket creation failed: {bucket_result2['message']}")
        # 다른 서비스 재시작
        if sysMode != 'device0':
            sysService('restart', 'SmartSystems')
            sysService('restart', 'SmartAPI')

        sysService('restart', 'Core')

        redis_state.client.hset("influx_init", "status", "COMPLETE")
        logging.info("✅ InfluxDB initialization completed")

    except Exception as e:
        redis_state.client.hset("influx_init", "status", "FAIL")
        logging.error(f"❌ Background setup error: {e}")


async def create_influx_bucket(bucket_name:str, retention:int):
    try:
        config = aesState.getInflux()
        token = aesState.decrypt(config["cipher"])
        # bucket_name = "ntek"
        retention_seconds = retention * 24 * 60 * 60
        bucket_data = {
            "orgID": config['org_id'],
            "name": bucket_name,
            "retentionRules": [
                {
                    "type": "expire",
                    "everySeconds": retention_seconds  # 2년
                }
            ]
        }

        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.post(
                f"http://127.0.0.1:8086/api/v2/buckets",
                headers={"Authorization": f"Token {token}"},
                json=bucket_data
            )

            if response.status_code == 201:
                retention_info = f"{retention_seconds // (24 * 60 * 60)} days" if retention_seconds > 0 else "infinite"
                logging.info(f"✅ Bucket '{bucket_name}' created (retention: {retention_info})")
                return {"success": True, "message": f"Bucket '{bucket_name}' created successfully"}
            elif response.status_code == 422:  # ✅ 이 부분 추가 필요
                logging.info(f"ℹ️ Bucket '{bucket_name}' already exists")
                return {"success": True, "message": f"Bucket already exists"}
            else:
                error_msg = response.json().get("message", response.text)
                logging.error(f"❌ Bucket '{bucket_name}' creation failed: {error_msg}")
                return {"success": False, "message": error_msg}

    except Exception as e:
        logging.error(f"❌ Bucket creation error: {e}")
        return {"success": False, "message": str(e)}


# async def create_downsampling_buckets():
#     """다운샘플링용 버킷 생성 (ntek_1h, ntek_1d)"""
#     try:
#         config = aesState.getInflux()
#         token = aesState.decrypt(config["cipher"])
#
#         buckets = [
#             {
#                 "name": "ntek_1h",
#                 "retention_seconds": 90 * 24 * 60 * 60,  # 90일
#                 "description": "1시간 평균 데이터"
#             },
#             {
#                 "name": "ntek_1d",
#                 "retention_seconds": 730 * 24 * 60 * 60,  # 2년
#                 "description": "1일 평균/합계 데이터"
#             }
#         ]
#
#         results = []
#
#         async with httpx.AsyncClient(timeout=setting_timeout) as client:
#             for bucket_info in buckets:
#                 bucket_data = {
#                     "orgID": config['org_id'],
#                     "name": bucket_info["name"],
#                     "retentionRules": []
#                 }
#
#                 # retention 설정 (0이면 무제한)
#                 if bucket_info["retention_seconds"] > 0:
#                     bucket_data["retentionRules"] = [
#                         {
#                             "type": "expire",
#                             "everySeconds": bucket_info["retention_seconds"]
#                         }
#                     ]
#
#                 response = await client.post(
#                     f"http://127.0.0.1:8086/api/v2/buckets",
#                     headers={"Authorization": f"Token {token}"},
#                     json=bucket_data
#                 )
#
#                 if response.status_code == 201:
#                     retention_info = f"{bucket_info['retention_seconds'] // (24 * 60 * 60)} days" if bucket_info[
#                                                                                                          'retention_seconds'] > 0 else "infinite"
#                     logging.info(f"✅ Bucket '{bucket_info['name']}' created (retention: {retention_info})")
#                     results.append({"bucket": bucket_info["name"], "success": True})
#                 elif response.status_code == 422:
#                     # 이미 존재하는 버킷
#                     logging.info(f"ℹ️ Bucket '{bucket_info['name']}' already exists")
#                     results.append({"bucket": bucket_info["name"], "success": True, "existed": True})
#                 else:
#                     error_msg = response.json().get("message", response.text)
#                     logging.error(f"❌ Bucket '{bucket_info['name']}' creation failed: {error_msg}")
#                     results.append({"bucket": bucket_info["name"], "success": False, "error": error_msg})
#
#         success_count = sum(1 for r in results if r["success"])
#         return {
#             "success": success_count > 0,
#             "message": f"Created/verified {success_count}/{len(buckets)} buckets",
#             "results": results
#         }
#
#     except Exception as e:
#         logging.error(f"❌ Downsampling buckets creation error: {e}")
#         return {"success": False, "message": str(e)}
#
async def create_downsampling_buckets():
    """다운샘플링용 버킷 생성 (ntek_1h, ntek_1d, ntek30)"""
    try:
        results = []
        results.append(await create_influx_bucket("ntek_1h", 90))
        results.append(await create_influx_bucket("ntek_1d", 730))
        results.append(await create_influx_bucket("ntek30", 30))  # ✅ 추가

        success_count = sum(1 for r in results if r["success"])
        return {
            "success": success_count > 0,
            "message": f"Created/verified {success_count}/3 buckets",
            "results": results
        }

    except Exception as e:
        logging.error(f"❌ Downsampling buckets creation error: {e}")
        return {"success": False, "message": str(e)}


async def create_downsampling_tasks():
    """다운샘플링 Task 생성"""
    try:
        config = aesState.getInflux()
        token = aesState.decrypt(config["cipher"])
        org_name = "ntek"  # 조직 이름

        tasks = [
            # Task 1: trend 5분 → 1시간 평균
            {
                "name": "downsample_trend_to_1h",
                "flux": f'''
option task = {{name: "downsample_trend_to_1h", every: 1h, offset: 5m}}

from(bucket: "ntek")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "trend")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> to(bucket: "ntek_1h", org: "{org_name}")
''',
                "every": "1h",
                "description": "Downsample trend data to 1h average"
            },

            # Task 2: trend 1시간 → 1일 평균
            {
                "name": "downsample_trend_to_1d",
                "flux": f'''
option task = {{name: "downsample_trend_to_1d", cron: "10 0 * * *"}}

from(bucket: "ntek_1h")
  |> range(start: -1d)
  |> filter(fn: (r) => r["_measurement"] == "trend")
  |> aggregateWindow(every: 1d, fn: mean, createEmpty: false)
  |> to(bucket: "ntek_1d", org: "{org_name}")
''',
                "cron": "10 0 * * *",
                "description": "Downsample trend data to 1d average"
            },

            # Task 3: energy_consumption 1시간 → 1일 합계
            {
                "name": "downsample_energy_consumption_to_1d",
                "flux": f'''
option task = {{name: "downsample_energy_consumption_to_1d", cron: "15 0 * * *"}}

from(bucket: "ntek")
  |> range(start: -1d)
  |> filter(fn: (r) => r["_measurement"] == "energy_consumption")
  |> aggregateWindow(every: 1d, fn: sum, createEmpty: false)
  |> to(bucket: "ntek_1d", org: "{org_name}")
''',
                "cron": "15 0 * * *",
                "description": "Downsample energy_consumption to 1d sum"
            },

            # Task 4: energy_cumulative 1시간 → 1일 마지막 값
            {
                "name": "downsample_energy_cumulative_to_1d",
                "flux": f'''
option task = {{name: "downsample_energy_cumulative_to_1d", cron: "20 0 * * *"}}

from(bucket: "ntek")
  |> range(start: -1d)
  |> filter(fn: (r) => r["_measurement"] == "energy_cumulative")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> to(bucket: "ntek_1d", org: "{org_name}")
''',
                "cron": "20 0 * * *",
                "description": "Downsample energy_cumulative to 1d last value"
            }
        ]

        results = []

        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            for task_info in tasks:
                task_data = {
                    "orgID": config['org_id'],
                    "org": org_name,
                    "name": task_info["name"],
                    "description": task_info["description"],
                    "status": "active",
                    "flux": task_info["flux"]
                }

                response = await client.post(
                    f"http://127.0.0.1:8086/api/v2/tasks",
                    headers={"Authorization": f"Token {token}"},
                    json=task_data
                )

                if response.status_code == 201:
                    task_id = response.json().get("id")
                    logging.info(f"✅ Task '{task_info['name']}' created (ID: {task_id})")
                    results.append({"task": task_info["name"], "success": True, "id": task_id})
                elif response.status_code == 422:
                    # 이미 존재하는 Task
                    logging.info(f"ℹ️ Task '{task_info['name']}' already exists")
                    results.append({"task": task_info["name"], "success": True, "existed": True})
                else:
                    error_msg = response.json().get("message", response.text)
                    logging.error(f"❌ Task '{task_info['name']}' creation failed: {error_msg}")
                    results.append({"task": task_info["name"], "success": False, "error": error_msg})

        success_count = sum(1 for r in results if r["success"])
        return {
            "success": success_count > 0,
            "message": f"Created/verified {success_count}/{len(tasks)} tasks",
            "results": results
        }

    except Exception as e:
        logging.error(f"❌ Downsampling tasks creation error: {e}")
        return {"success": False, "message": str(e)}


async def setup_downsampling():
    """다운샘플링 전체 설정 (버킷 + Task)"""
    try:
        logging.info("🔧 Starting downsampling setup...")

        # 1. 버킷 생성
        bucket_result = await create_downsampling_buckets()
        if not bucket_result["success"]:
            logging.warning(f"⚠️ Bucket creation had issues: {bucket_result['message']}")

        # 2. Task 생성
        task_result = await create_downsampling_tasks()
        if not task_result["success"]:
            logging.warning(f"⚠️ Task creation had issues: {task_result['message']}")

        # 3. 결과 요약
        overall_success = bucket_result["success"] and task_result["success"]

        if overall_success:
            # redis_state.client.select(0)
            redis_state.client.hset("influx_init", "status", "COMPLETE")
            logging.info("✅ Downsampling setup completed successfully")
            return {
                "success": True,
                "message": "Downsampling buckets and tasks created",
                "buckets": bucket_result["results"],
                "tasks": task_result["results"]
            }
        else:
            return {
                "success": False,
                "message": "Downsampling setup had issues",
                "buckets": bucket_result.get("results", []),
                "tasks": task_result.get("results", [])
            }

    except Exception as e:
        logging.error(f"❌ Downsampling setup error: {e}")
        return {"success": False, "message": str(e)}


@router.get('/setup-downsampling')
async def setup_downsampling_endpoint():
    """
    다운샘플링 버킷과 Task를 생성합니다.
    (업데이트 후 1회 실행용)

    생성 항목:
    - 버킷: ntek_1h (90일), ntek_1d (2년)
    - Task: trend 5분→1시간→1일, energy 일간 집계
    """
    try:
        logging.info("🔧 다운샘플링 설정 시작...")

        result = await setup_downsampling()

        if result["success"]:
            logging.info("✅ 다운샘플링 설정 완료")
            return {
                "result": True,
                "message": "다운샘플링 버킷 및 Task가 생성되었습니다.",
                "buckets": result.get("buckets", []),
                "tasks": result.get("tasks", [])
            }
        else:
            logging.warning(f"⚠️ 다운샘플링 설정 중 일부 실패: {result['message']}")
            return {
                "result": False,
                "message": result["message"],
                "buckets": result.get("buckets", []),
                "tasks": result.get("tasks", [])
            }

    except Exception as e:
        logging.error(f"❌ 다운샘플링 설정 실패: {e}")
        import traceback
        traceback.print_exc()
        return{
            "result": False,
            "message":f"다운샘플링 설정 실패: {str(e)}"
        }

@router.get('/check-downsampling')
async def check_downsampling_status():
    """
    다운샘플링 버킷과 Task의 존재 여부를 확인합니다.
    """
    try:
        # 1. org_id 확인 및 가져오기
        ret = check_org_id_exists()
        print(f"check_org_id_exists: {ret}")

        if not ret["result"]:
            # org_id가 없으면 InfluxDB에서 조회해서 저장
            org_id = await get_org_id_from_influxdb()
            if not org_id:
                return {
                    "result": False,
                    "message": "org_id를 찾을 수 없습니다"
                }

        # 2. config 가져오기
        config = aesState.getInflux()

        if not config["result"]:
            return {
                "result": False,
                "message": "InfluxDB 설정 파일을 찾을 수 없습니다"
            }

        # 3. org_id 확인 (getInflux 결과에 없을 수도 있음)
        if "org_id" not in config or not config["org_id"]:
            # 파일에서 다시 확인
            ret = check_org_id_exists()
            if ret["result"] and ret["org_id"]:
                config["org_id"] = ret["org_id"]
            else:
                return {
                    "result": False,
                    "message": "org_id를 찾을 수 없습니다"
                }

        token = aesState.decrypt(config["cipher"])

        bucket_names = ["ntek_1h", "ntek_1d", "ntek30"]
        task_names = [
            "downsample_trend_to_1h",
            "downsample_trend_to_1d",
            "downsample_energy_consumption_to_1d",
            "downsample_energy_cumulative_to_1d"
        ]

        bucket_status = []
        task_status = []

        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            # 버킷 상태 확인
            try:
                buckets_response = await client.get(
                    f"http://127.0.0.1:8086/api/v2/buckets",
                    headers={"Authorization": f"Token {token}"},
                    params={"orgID": config['org_id']}
                )

                if buckets_response.status_code == 200:
                    all_buckets = buckets_response.json().get("buckets", [])

                    for bucket_name in bucket_names:
                        bucket = next((b for b in all_buckets if b["name"] == bucket_name), None)

                        if bucket:
                            retention = bucket.get("retentionRules", [])
                            retention_seconds = retention[0]["everySeconds"] if retention else 0
                            retention_days = retention_seconds // (
                                        24 * 60 * 60) if retention_seconds > 0 else "infinite"

                            bucket_status.append({
                                "name": bucket_name,
                                "exists": True,
                                "id": bucket["id"],
                                "retention_days": retention_days,
                                "created_at": bucket.get("createdAt")
                            })
                        else:
                            bucket_status.append({
                                "name": bucket_name,
                                "exists": False
                            })
                else:
                    logging.error(f"❌ 버킷 조회 실패: {buckets_response.status_code}")

            except Exception as e:
                logging.error(f"❌ 버킷 조회 중 오류: {e}")
                for bucket_name in bucket_names:
                    bucket_status.append({
                        "name": bucket_name,
                        "exists": False,
                        "error": str(e)
                    })

            # Task 상태 확인
            try:
                tasks_response = await client.get(
                    f"http://127.0.0.1:8086/api/v2/tasks",
                    headers={"Authorization": f"Token {token}"},
                    params={"orgID": config['org_id']}
                )

                if tasks_response.status_code == 200:
                    all_tasks = tasks_response.json().get("tasks", [])

                    for task_name in task_names:
                        task = next((t for t in all_tasks if t["name"] == task_name), None)

                        if task:
                            task_status.append({
                                "name": task_name,
                                "exists": True,
                                "id": task["id"],
                                "status": task.get("status"),
                                "created_at": task.get("createdAt"),
                                "last_run_status": task.get("lastRunStatus"),
                                "last_run_error": task.get("lastRunError")
                            })
                        else:
                            task_status.append({
                                "name": task_name,
                                "exists": False
                            })
                else:
                    logging.error(f"❌ Task 조회 실패: {tasks_response.status_code}")

            except Exception as e:
                logging.error(f"❌ Task 조회 중 오류: {e}")
                for task_name in task_names:
                    task_status.append({
                        "name": task_name,
                        "exists": False,
                        "error": str(e)
                    })

        # 전체 상태 판단
        all_buckets_exist = all(b["exists"] for b in bucket_status)
        all_tasks_exist = all(t["exists"] for t in task_status)

        return {
            "result": True,
            "all_configured": all_buckets_exist and all_tasks_exist,
            "buckets": {
                "all_exist": all_buckets_exist,
                "details": bucket_status
            },
            "tasks": {
                "all_exist": all_tasks_exist,
                "details": task_status
            },
            "summary": {
                "buckets_count": f"{sum(1 for b in bucket_status if b['exists'])}/{len(bucket_names)}",
                "tasks_count": f"{sum(1 for t in task_status if t['exists'])}/{len(task_names)}"
            }
        }

    except Exception as e:
        logging.error(f"❌ 다운샘플링 상태 확인 실패: {e}")
        import traceback
        traceback.print_exc()
        return {
            "result": False,
            "message": f"다운샘플링 상태 확인 실패: {str(e)}"
        }


def check_org_id_exists():
    """
    influx.json에 org_id가 있는지 확인

    Returns:
        bool: org_id가 있으면 True, 없으면 False
    """
    try:
        file_path = os.path.join(SETTING_FOLDER, 'influx.json')

        if not os.path.exists(file_path):
            return {"result": False}

        with open(file_path, "r", encoding="utf-8") as f:
            influx_config = json.load(f)

        if "org_id" in influx_config and influx_config["org_id"]:
            return {"result": True, "org_id": influx_config["org_id"]}
        else:
            return {"result": False, "org_id": None}

    except Exception as e:
        logging.error(f"❌ Error checking org_id: {e}")
        return {"result": False}


async def get_org_id_from_influxdb(org_name: str = "ntek") -> str:
    """
    InfluxDB에서 organization ID를 조회하고 influx.json에 저장

    Args:
        org_name: 조직 이름 (기본값: "ntek")

    Returns:
        str: org_id 또는 None
    """
    try:
        config = aesState.getInflux()
        token = aesState.decrypt(config["cipher"])

        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.get(
                "http://127.0.0.1:8086/api/v2/orgs",
                headers={"Authorization": f"Token {token}"}
            )

            if response.status_code == 200:
                orgs = response.json().get("orgs", [])
                target_org = next((org for org in orgs if org["name"] == org_name), None)

                if target_org:
                    org_id = target_org["id"]
                    logging.info(f"✅ Found org_id: {org_id}")

                    # influx.json에 org_id 저장
                    file_path = os.path.join(SETTING_FOLDER, 'influx.json')
                    with open(file_path, "r", encoding="utf-8") as f:
                        influx_config = json.load(f)

                    influx_config["org_id"] = org_id

                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(influx_config, f, indent=4)

                    logging.info(f"✅ org_id saved to influx.json")

                    return org_id
                else:
                    logging.warning(f"⚠️ Organization '{org_name}' not found")
                    return None
            else:
                logging.error(f"❌ API error: {response.status_code}")
                return None

    except Exception as e:
        logging.error(f"❌ Error getting org_id: {e}")
        return None


@router.get('/initDB/status')
async def get_init_status():
    # redis_state.client.select(0)
    status = redis_state.client.hget("influx_init", "status") or "IDLE"
    return {"status": status}


@router.get("/backup/download/{backup_type}")
async def download_backup(backup_type: str):
    try:
        LOG_PATH = '/usr/local/sv500/logs'
        BACKUP_DIR = '/usr/local/sv500/backup/influxdb'  # ✅

        # 백업 디렉토리가 없으면 생성 시도 (권한 있을 때만 가능)
        if not os.path.exists(BACKUP_DIR):
            try:
                os.makedirs(BACKUP_DIR, exist_ok=True)
            except PermissionError:
                return {"success": False, "message": "Backup directory not accessible. Please run installation script."}

        temp_dir = tempfile.mkdtemp(dir=BACKUP_DIR)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        #        background_tasks.add_task(shutil.rmtree, temp_dir)

        if backup_type in ["all", "other"]:
            # InfluxDB + logs 통합 백업
            return await _backup_all(temp_dir, timestamp, LOG_PATH)

        elif backup_type == "dbbackup":
            # InfluxDB만 백업
            return await _backup_influxdb(temp_dir, timestamp)

        elif backup_type == "log":
            # logs 폴더만 백업
            return await _backup_logs(temp_dir, timestamp, LOG_PATH)

        else:
            shutil.rmtree(temp_dir)
            return {"success": False, "message": "Invalid backup_type. Use: all, dbbackup, or logs"}

    except Exception as e:
        logging.error(f"❌ Backup error: {e}")
        return {"success": False, "message": str(e)}


async def _backup_all(temp_dir: str, timestamp: str, log_dir: str):
    """InfluxDB + logs 통합 백업"""
    try:
        config = aesState.getInflux()
        if not config["result"]:
            return {"success": False, "message": "InfluxDB not initialized"}

        token = aesState.decrypt(config["cipher"])
        org = config["org"]

        backup_name = f"backup_all_{timestamp}"
        backup_path = os.path.join(temp_dir, backup_name)
        os.makedirs(backup_path, exist_ok=True)

        # ✅ 임시 InfluxDB 백업 (루트 레벨에)
        temp_influx_backup = os.path.join(temp_dir, f"temp_influx_{timestamp}")

        backup_command = f"""
export INFLUX_TOKEN='{token}'
export INFLUX_HOST='http://localhost:8086'
export INFLUX_ORG='{org}'
influx backup {temp_influx_backup} --bucket ntek
"""

        result = subprocess.run(
            ['bash', '-c', backup_command],
            check=True,
            capture_output=True,
            text=True,
            timeout=300
        )

        logging.info(f"📋 Backup stdout: {result.stdout}")
        logging.info(f"📋 Backup stderr: {result.stderr}")

        logging.info(f"✅ InfluxDB backup completed")

        # ✅ 백업을 최종 위치로 이동
        influx_backup_path = os.path.join(backup_path, "influxdb")
        shutil.move(temp_influx_backup, influx_backup_path)
        logging.info(f"✅ InfluxDB backup moved to final location")

        # 2. logs 폴더 복사
        if os.path.exists(log_dir):
            logs_backup_path = os.path.join(backup_path, "logs")
            shutil.copytree(log_dir, logs_backup_path)
            logging.info(f"✅ Logs copied")

        # 3. 통합 압축
        #        tar_file = f"{backup_path}.tar.gz"
        parent_dir = os.path.dirname(temp_dir)
        tar_file = os.path.join(parent_dir, f"{backup_name}.tar.gz")

        result = subprocess.run(
            ['tar', '--ignore-failed-read', '-czf', tar_file, '-C', temp_dir, backup_name],
            capture_output=True,
            text=True,
            timeout=300
        )

        # ✅ exit code 0 또는 1 허용
        if result.returncode > 1:
            raise subprocess.CalledProcessError(result.returncode, ['tar'], result.stdout, result.stderr)

        if not os.path.exists(tar_file):
            raise Exception("Backup file not created")

        logging.info(f"✅ All backup created: {backup_name}.tar.gz")

        def cleanup():
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                if os.path.exists(tar_file):
                    os.remove(tar_file)
            except Exception as e:
                logging.error(f"Cleanup error: {e}")

        return FileResponse(
            path=tar_file,
            filename=f"{backup_name}.tar.gz",
            media_type='application/gzip',
            background=BackgroundTask(cleanup)
        )

    except subprocess.TimeoutExpired:
        logging.error("❌ Backup timeout")
        return {"success": False, "message": "Backup timeout"}
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        logging.error(f"❌ Backup failed: {error_msg}")
        return {"success": False, "message": f"Backup failed: {error_msg}"}


async def _backup_influxdb(temp_dir: str, timestamp: str):
    """InfluxDB만 백업"""
    try:
        config = aesState.getInflux()
        if not config["result"]:
            return {"success": False, "message": "InfluxDB not initialized"}

        token = aesState.decrypt(config["cipher"])
        org = config["org"]

        backup_name = f"backup_influxdb_{timestamp}"
        backup_path = os.path.join(temp_dir, backup_name)

        backup_command = f"""
set -e
export INFLUX_TOKEN='{token}'
export INFLUX_HOST='http://localhost:8086'
export INFLUX_ORG='{org}'
influx backup {backup_path} --bucket ntek
"""

        result = subprocess.run(
            ['bash', '-c', backup_command],
            check=True,
            capture_output=True,
            text=True,
            timeout=300
        )

        # ✅ tar 파일을 부모 디렉토리에 생성
        parent_dir = os.path.dirname(temp_dir)
        tar_file = os.path.join(parent_dir, f"{backup_name}.tar.gz")

        subprocess.run(
            ['tar', '-czf', tar_file, '-C', temp_dir, backup_name],
            check=True,
            timeout=300
        )

        if not os.path.exists(tar_file):
            raise Exception("Backup file not created")

        logging.info(f"✅ InfluxDB backup created: {backup_name}.tar.gz")

        # ✅ 정리 함수
        def cleanup():
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                if os.path.exists(tar_file):
                    os.remove(tar_file)
            except Exception as e:
                logging.error(f"Cleanup error: {e}")

        return FileResponse(
            path=tar_file,
            filename=f"{backup_name}.tar.gz",
            media_type='application/gzip',
            background=BackgroundTask(cleanup)
        )

    except subprocess.TimeoutExpired:
        return {"success": False, "message": "Backup timeout"}
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        logging.error(f"❌ Backup failed: {error_msg}")
        return {"success": False, "message": f"Backup failed: {error_msg}"}


async def _backup_logs(temp_dir: str, timestamp: str, log_dir: str):
    """logs 폴더만 백업"""
    try:
        if not os.path.exists(log_dir):
            return {"success": False, "message": f"Logs directory not found: {log_dir}"}

        backup_name = f"backup_logs_{timestamp}"

        # ✅ tar 파일을 부모 디렉토리에 생성
        parent_dir = os.path.dirname(temp_dir)
        tar_file = os.path.join(parent_dir, f"{backup_name}.tar.gz")

        # logs 폴더 압축
        result = subprocess.run(
            ['tar', '--ignore-failed-read', '-czf', tar_file, '-C', os.path.dirname(log_dir),
             os.path.basename(log_dir)],
            capture_output=True,  # ✅ 추가
            text=True,  # ✅ 추가
            timeout=300
        )

        logging.info(f"📋 tar stderr: {result.stderr}")

        # ✅ exit code 0 또는 1 모두 허용 (1은 경고)
        if result.returncode > 1:
            raise subprocess.CalledProcessError(
                result.returncode,
                ['tar'],
                result.stdout,
                result.stderr
            )

        if not os.path.exists(tar_file):
            raise Exception("Backup file not created")

        logging.info(f"✅ Logs backup created: {backup_name}.tar.gz")

        # ✅ 정리 함수
        def cleanup():
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                if os.path.exists(tar_file):
                    os.remove(tar_file)
            except Exception as e:
                logging.error(f"Cleanup error: {e}")

        return FileResponse(
            path=tar_file,
            filename=f"{backup_name}.tar.gz",
            media_type='application/gzip',
            background=BackgroundTask(cleanup)
        )

    except subprocess.TimeoutExpired:
        return {"success": False, "message": "Backup timeout"}
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        logging.error(f"❌ Backup failed: {error_msg}")
        return {"success": False, "message": f"Backup failed: {error_msg}"}

def parse_settings(setting):
    """설정을 파싱하여 결과 딕셔너리 생성"""
    # 기본값 설정
    result = {
        "result": "1",
        "mode": setting.get("mode", ""),
        "lang": setting.get("lang", ""),
        "location": "",
        "Diag_main": False,
        "Diag_sub": False,
        "enable_main": False,
        "enable_sub": False,
        "pq_main": False,
        "pq_sub": False,
        "assetType_main": "",
        "assetName_main": "",
        "assetType_sub": "",
        "assetName_sub": "",
        "assetNickname_main": "",
        "assetNickname_sub": "",
        "assetdriveType_main":"",
        "assetdriveType_sub": "",
        "main_kva": -1,
        "sub_kva": -1,
        "pf_sign": -1,
        "va_type": -1,
        "unbalance":-1
    }

    # channel 검증
    if "channel" not in setting:
        result["result"] = "0"
        return result

    # device 모드인 경우만 상세 정보 파싱
    if 'device' in result["mode"]:
        # General 정보 파싱
        general_data = setting.get("General", {})
        use_function = general_data.get("useFuction", {})  # 오타 수정 필요
        dev_info = general_data.get("deviceInfo", {})
        result["pf_sign"] = general_data.get("pf_sign", 0)
        result["va_type"] = general_data.get("va_type", 0)
        result["unbalance"] = general_data.get("unbalance", 0)
        result["location"] = dev_info.get("location", "")
        result["Diag_main"] = bool(use_function.get("diagnosis_main", 0))
        result["Diag_sub"] = bool(use_function.get("diagnosis_sub", 0))

        # 채널별 정보 파싱
        for channel_data in setting["channel"]:
            channel_name = channel_data.get("channel", "")

            if channel_name == "Main":
                parse_channel_data(channel_data, result, "main", result["Diag_main"])
            elif channel_name == "Sub":
                parse_channel_data(channel_data, result, "sub", result["Diag_sub"])

    return result


def parse_channel_data(channel_data, result, prefix, diag_enabled):
    """채널 데이터를 파싱하여 결과에 추가"""
    result[f"enable_{prefix}"] = bool(channel_data.get("Enable", 0))
    result[f"pq_{prefix}"] = bool(channel_data.get("PowerQuality", 0))

    if diag_enabled:
        asset_info = channel_data.get("assetInfo", {})
        result[f"assetType_{prefix}"] = asset_info.get("type", "")
        result[f"assetName_{prefix}"] = asset_info.get("name", "")
        result[f"assetNickname_{prefix}"] = asset_info.get("nickname", "")
        result[f"assetdriveType_{prefix}"] = asset_info.get("driveType", "")

        if asset_info.get("type") == 'Transformer':
            result[f"{prefix}_kva"] = int(channel_data.get("n_kva", 0))

@router.get('/checkSettingFile') #check setup.json
def check_setupfile(request: Request):
    """
    우선순위:
    1. setup.json 파일 확인 (최우선)
    2. 파일이 없으면 default.json으로 생성
    3. Redis에 없으면 파일에서 로드하여 Redis에 저장
    """
    file_path = os.path.join(SETTING_FOLDER, 'setup.json')
    default_file_path = os.path.join(SETTING_FOLDER, 'default.json')
    deviceMac = get_mac_address()
    ser = ''
    if os_spec.os != 'Windows':
        mac_file_path = os.path.join(SETTING_FOLDER, 'serial_num_do_not_modify.txt')
        if os.path.exists(mac_file_path):
            ser = read_mac_plain(mac_file_path)

            # if ser != deviceMac:
            #     deviceMac = ser

    if redis_state.client is None:
        return {"result": "0", "error": "Redis not available"}

    try:
        # redis_state.client.select(0)

        # 1. 먼저 setup.json 파일 확인 및 생성
        if not os.path.exists(file_path):
            # setup.json이 없으면 default.json으로 생성
            if os.path.exists(default_file_path):
                shutil.copy(default_file_path, file_path)
            else:
                return {"result": "0", "error": "No default.json found"}

        # 2. Redis에 setup이 있는지 확인
        if redis_state.client.hexists("System", "setup"):
            # Redis에 있으면 Redis 데이터 사용
            setting = json.loads(redis_state.client.hget("System", "setup"))
            # deviceMac = get_mac_address()
            if deviceMac != setting["General"]["deviceInfo"]["mac_address"]:
                setting["General"]["deviceInfo"]["mac_address"] = deviceMac
            if ser != '':
                setting["General"]["deviceInfo"]["serial_number"] = ser
            else:
                setting["General"]["deviceInfo"]["mac_address"] = deviceMac

        else:
            # Redis에 없으면 파일에서 읽어서 Redis에 저장
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    setting = json.load(f)
            except json.JSONDecodeError:
                # setup.json이 손상된 경우 default.json으로 복구
                shutil.copy(default_file_path, file_path)
                with open(file_path, "r", encoding="utf-8") as f:
                    setting = json.load(f)

            # Redis에 저장
            # deviceMac = get_mac_address()
            if deviceMac != setting["General"]["deviceInfo"]["mac_address"]:
                setting["General"]["deviceInfo"]["mac_address"] = deviceMac
                # setting["General"]["deviceInfo"]["serial_number"] = deviceMac
            if ser != '':
                setting["General"]["deviceInfo"]["serial_number"] = ser
            else:
                setting["General"]["deviceInfo"]["mac_address"] = deviceMac

            redis_state.client.hset("System", "setup", json.dumps(setting))
            if "mode" in setting:
                redis_state.client.hset("System", "mode", setting["mode"])

        for idx, ch in enumerate(setting["channel"]):
            setting["channel"][idx]["ctInfo"]["inorminal"] = float(setting["channel"][idx]["ctInfo"]["inorminal"])/1000

        # 3. 설정 파싱 및 반환
        return parse_settings(setting)

    except Exception as e:
        return {"result": "0", "error": str(e)}

def saveStartCurrent(setting):
    main_channel_data = next((ch for ch in setting["channel"] if ch.get("channel") == "Main"), None)
    if main_channel_data:
        main_c = int(main_channel_data["ctInfo"]["startingcurrent"]) / 1000
    else:
        main_c = 0
    sub_channel_data = next((ch for ch in setting["channel"] if ch.get("channel") == "Sub"), None)
    if sub_channel_data:
        sub_c = int(sub_channel_data["ctInfo"]["startingcurrent"]) / 1000
    else:
        sub_c = 0
    return {"main": main_c, "sub": sub_c}

def save_StartCurrent_DemandInterval_SamplingPeriod(setting):
    main_channel_data = next((ch for ch in setting["channel"] if ch.get("channel") == "Main"), None)
    if main_channel_data:
        main_c = int(main_channel_data["ctInfo"]["startingcurrent"]) / 1000
        if int(main_channel_data["demand"]["demand_interval"]) != 15:
            main_d = int(main_channel_data["demand"]["demand_interval"])*60
        else:
            main_d = 15*60
        main_s = int(main_channel_data["sampling"]["period"])*60
        main_data = {
            "PT_WiringMode":int(main_channel_data["ptInfo"]["wiringmode"]),
            "RatedFrequency": int(main_channel_data["ptInfo"]["linefrequency"]),
            "RatedVoltage": int(main_channel_data["ptInfo"]["vnorminal"]),
            "RatedCurrent": int(main_channel_data["ctInfo"]["inorminal"]),
            "RatedKVA": int(main_channel_data["n_kva"])
        }
    else:
        main_c = 0
        main_d = 15*60
        main_s = 0
        main_data = {}
    sub_channel_data = next((ch for ch in setting["channel"] if ch.get("channel") == "Sub"), None)
    if sub_channel_data:
        sub_c = int(sub_channel_data["ctInfo"]["startingcurrent"]) / 1000
        if int(sub_channel_data["demand"]["demand_interval"]) != 15:
            sub_d = int(sub_channel_data["demand"]["demand_interval"])*60
        else:
            sub_d = 15 * 60
        sub_s = int(sub_channel_data["sampling"]["period"])*60
        sub_data = {
            "PT_WiringMode": int(sub_channel_data["ptInfo"]["wiringmode"]),
            "RatedFrequency": int(sub_channel_data["ptInfo"]["linefrequency"]),
            "RatedVoltage": int(sub_channel_data["ptInfo"]["vnorminal"]),
            "RatedCurrent": int(sub_channel_data["ctInfo"]["inorminal"]),
            "RatedKVA": int(sub_channel_data["n_kva"])
        }
    else:
        sub_c = 0
        sub_d = 15*60
        sub_s = 0
        sub_data = {}
    return {"StartCurrent":{"main": main_c, "sub": sub_c},"Demand":{"main": main_d, "sub": sub_d},
            "Sampling":{"main": main_s, "sub": sub_s}, "Channel": {"main": main_data, "sub":sub_data}}

@router.get('/getSetting')
def get_setting():
    # redis_state.client.execute_command("SELECT", 0)
    if redis_state.client.hexists("System", "setup"):
        redisContext = redis_state.client.hget("System", "setup")
        setting = json.loads(redisContext)
    else:
        file_path = os.path.join(SETTING_FOLDER, 'setup.json')
        if not os.path.exists(file_path):
            return {"passOK": 0, "error": "setting file not found"}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                setting = json.load(f)
        except Exception as e:
            return {"passOK": 0}

    for idx, ch in enumerate(setting["channel"]):
        setting["channel"][idx]["ctInfo"]["inorminal"] = float(
            setting["channel"][idx]["ctInfo"]["inorminal"]) / 1000

    setup_dict = {
        "mode": setting.get("mode", ""),
        "lang": setting.get("lang",""),
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

    return {"passOK": 1, "data":setup_dict}

@router.get('/getSettingData/{channel}')  # get setting with setup.json
def getDatafromSetting(channel):
    # redis_state.client.execute_command("SELECT", 0)
    if redis_state.client.hexists("System", "setup"):
        redisContext = redis_state.client.hget("System", "setup")
        setting = json.loads(redisContext)
    else:
        file_path = os.path.join(SETTING_FOLDER, 'setup.json')
        if not os.path.exists(file_path):
            return {"passOK": "0", "error": "setting file not found"}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                    setting = json.load(f)
        except Exception as e:
            return {"passOK": "0"}

    for idx, ch in enumerate(setting["channel"]):
        setting["channel"][idx]["ctInfo"]["inorminal"] = float(
            setting["channel"][idx]["ctInfo"]["inorminal"]) / 1000

    if channel in setting:
        return {"passOK": "1", "data": setting[channel]}
    else:
        main_channel = [ch for ch in setting["channel"] if ch["channel"] == channel]
        if not main_channel:
            return {"passOK": "0"}
        else:
            return {"passOK": "1", "data": main_channel}


@router.get('/Reset')
def reset():
    msg = ''

    if not redis_state.client is None:
        # redis_state.client.execute_command("SELECT", 0)
        if redis_state.client.hexists("Service","setting"):
            checkflag = redis_state.client.hget("Service","setting")
            if int(checkflag) == 1:
                return {"success": False, "msg": "Modbus setting is activated"}

        setting_path = os.path.join(SETTING_FOLDER, 'setup.json')
        backup_file_path = os.path.join(SETTING_FOLDER, 'setup_backup.json')
        try:
            if os.path.exists(setting_path):
                shutil.copy(setting_path, backup_file_path)  # setup.json을 setting_backup.json으로 백업
                os.remove(setting_path)
            else:
                msg = "No exist setup.json"

            if redis_state.client.hexists("System", "setup"):
                nowSetup = json.loads(redis_state.client.hget("System", "setup"))
                default_file_path = os.path.join(SETTING_FOLDER, 'default.json')

                with open(default_file_path, "r", encoding="utf-8") as f:
                    defaults = json.load(f)

                defaults["mode"] = nowSetup["mode"]
                defaults["General"]["deviceInfo"]["mac_address"] = get_mac_address()
                defaults["General"]["deviceInfo"]["serial_number"] = get_mac_address()

                with open(default_file_path, "w", encoding="utf-8") as f:
                    json.dump(defaults, f, indent=2)  # indent 추가로 가독성 향상

                redis_state.client.hdel("System", "setup")
        except Exception as e:
            print(str(e))
            return {"success": False, "msg": str(e)}
    else:
        msg += "No saved setup in Redis"
    if msg == '':
        return {"success": True, "msg": "Reset success"}
    else:
        return {"success": True, "msg": msg}


async def reset_count(request:Request):
    # redis_state.client.select(0)
    if redis_state.client.hexists("System","setup"):
        setup = json.loads(redis_state.client.hget("System","setup"))
        mainEnable = 0
        subEnable = 0
        for chInfo in setup["channel"]:
            if chInfo["channel"] == 'Main':
                mainEnable = chInfo["Enable"]
                break
        for chInfo in setup["channel"]:
            if chInfo["channel"] == 'Sub':
                subEnable = chInfo["Enable"]
                break
        if mainEnable == 1:
            allcmd0 = Command(type=0, cmd=0, item=8)  # all item clear  (add item 8 to minhyuk)
            ret0 = await push_command_left(allcmd0, request)
            if not ret0["success"]:
                return False
        if subEnable == 1:
            allcmd1 = Command(type=1, cmd=0, item=8)  # all item clear  (add item 8 to minhyuk)
            ret1 = await push_command_left(allcmd1, request)
            if not ret1["success"]:
                return False

        return True
    else:
        return False


async def reset_system(request:Request):
    ret = sysService("stop", "Core")
    retflag = True
    if ret["success"]:
        try:
            start = "1970-01-01T00:00:00Z"
            stop = datetime.utcnow().isoformat() + "Z"

            # ntek 버킷의 measurement 목록 조회 후 삭제
            query = '''
            import "influxdata/influxdb/schema"
            schema.measurements(bucket: "ntek")
            '''

            try:
                tables = influx_state.query_api.query(query, org='ntek')
                measurements = []
                for table in tables:
                    for record in table.records:
                        meas_name = record.values.get("_value")
                        if meas_name:
                            measurements.append(meas_name)

                # 각 measurement 개별 삭제
                for measurement in measurements:
                    try:
                        influx_state.delete_api.delete(
                            start=start,
                            stop=stop,
                            predicate=f'_measurement="{measurement}"',
                            bucket='ntek',
                            org='ntek'
                        )
                        logging.info(f"✅ Deleted measurement: {measurement} from ntek")
                    except Exception as e:
                        retflag = False
                        logging.warning(f"⚠️ Failed to delete {measurement}: {e}")
                        break

            except Exception as e:
                logging.warning(f"⚠️ No measurements found in ntek or query failed: {e}")
                retflag = True  # 데이터가 없어도 성공으로 처리

        except Exception as e:
            retflag = False
            logging.error(f"❌ Failed to delete InfluxDB ntek bucket: {e}")
            return {"success": False, "msg": f"Failed deleting Influxdb: {str(e)}"}
    else:
        retflag = False
        return {"success": False, "msg": "Failed stopping core service"}

    # SmartSystem 버킷들도 동일하게 measurement 삭제
    if service_exists("smartsystemsservice.service"):
        result = await reinstall_smartsystem()
        retflag = result["success"]

    if retflag:
        res = await reset_count(request)
        if not res:
            return {"success": False, "msg": "Failed clearing system count"}
        return {"success": True}
    else:
        return {"success": False, "msg": "System reset incomplete"}


async def reinstall_smartsystem():
    """SmartSystem 재설치로 완전 초기화"""
    try:
        # 설치 스크립트 경로 (실제 경로에 맞게 수정 필요)
        install_script = "/usr/local/sv500/iss/install.sh"  # 예시

        if not os.path.exists(install_script):
            # 또는 reinstall 명령어가 있다면
            return {"success": False, "msg": "Reinstall script is not existed"}

        # 스크립트 실행
        result = subprocess.run(
            [install_script, "--fresh"],  # 또는 적절한 옵션
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            logging.info("✅ SmartSystem install script completed")
            return {"success": True}
        else:
            logging.error(f"❌ Install script failed: {result.stderr}")
            return {"success": False, "msg": result.stderr}

    except subprocess.TimeoutExpired:
        logging.error("❌ Install script timeout")
        return {"success": False, "msg": "Install script timeout"}
    except Exception as e:
        logging.error(f"❌ Install script error: {e}")
        return {"success": False, "msg": str(e)}


def delete_channel_data():
    """
    ch1, ch2의 waveform과 event 파일 삭제 (간단 버전)
    """
    base_path = "/home/root"
    directories_to_clean = [
        "ch1/waveform",
        "ch1/event",
        "ch2/waveform",
        "ch2/event"
    ]

    total_deleted = 0

    try:
        for dir_path in directories_to_clean:
            full_path = os.path.join(base_path, dir_path)

            if not os.path.exists(full_path):
                continue

            for root, dirs, files in os.walk(full_path, topdown=False):
                for filename in files:
                    try:
                        os.remove(os.path.join(root, filename))
                        total_deleted += 1
                    except:
                        pass

        logging.info(f"✅ Deleted {total_deleted} channel data files")
        return {"success": True, "deleted": total_deleted}

    except Exception as e:
        logging.error(f"❌ Failed to delete channel data: {e}")
        return {"success": False, "msg": str(e)}


@router.get('/ResetAll')
async def resetAll(request:Request):
    # 1. stop service core and delete ntek 2. stop service SmartSystem 3. clear service SmartSystem and delete ssdb,ssdbnr 4. Clear count, 5. Delete setup, 6. Delete user.db
    saveLog("Factory Default", request)
    msg = ''
    if not redis_state.client is None:
        # redis_state.client.execute_command("SELECT", 0)
        if redis_state.client.hexists("Service", "setting"):
            checkflag = redis_state.client.hget("Service", "setting")
            if int(checkflag) == 1:
                return {"success": False, "msg": "Modbus setting is activated"}
        ret = await reset_system(request) #stop core, reinstall smartsystem
        if not ret["success"]:
            return ret
        setting_path = os.path.join(SETTING_FOLDER, 'setup.json')
        db_path = os.path.join(SETTING_FOLDER, 'user.db')
        bearing_db_path = os.path.join(SETTING_FOLDER, 'bearing.db')
        mt_path = os.path.join(SETTING_FOLDER, 'maintenance.db')
        backup_file_path = os.path.join(SETTING_FOLDER, 'setup_backup.json')
        try:
            if os.path.exists(setting_path):
                shutil.copy(setting_path, backup_file_path)  # setup.json을 setting_backup.json으로 백업
                os.remove(setting_path)
            else:
                msg = "No exist setup.json"
            if os.path.exists(db_path):
                os.remove(db_path)
            else:
                msg += "No exist user.db"
            if os.path.exists(bearing_db_path):
                os.remove(bearing_db_path)
            if os.path.exists(mt_path):
                os.remove(mt_path)

            default_file_path = os.path.join(SETTING_FOLDER, 'default.json')

            with open(default_file_path, "r", encoding="utf-8") as f:
                defaults = json.load(f)

            defaults["mode"] = 'device0'
            defaults["General"]["deviceInfo"]["mac_address"] = ""
            defaults["General"]["deviceInfo"]["serial_number"] = ""

            with open(default_file_path, "w", encoding="utf-8") as f:
                json.dump(defaults, f, indent=2)  # indent 추가로 가독성 향상

            if redis_state.client.hexists("System", "setup"):
                redis_state.client.hdel("System", "setup")
            if redis_state.client.hexists("System", "mode"):
                redis_state.client.hdel("System", "mode")
            if redis_state.client.exists("Equipment"):
                redis_state.client.delete("Equipment")
            rt = delete_channel_data()
            sysService("start", "Core")
            if service_exists("smartsystemsservice.service"):
                sysService("start", "SmartSystems")
                sysService("start", "SmartAPI")
        except Exception as e:
            print(str(e))
            return {"success": False, "msg": str(e)}
    else:
        msg += "No saved setup in Redis"
    if msg == '':
        return {"success": True, "msg": "Reset success"}
    else:
        return {"success": True, "msg": msg}


@router.get('/getDiagnosisSetting')
async def get_diagnosissetting(request:Request):
    async with httpx.AsyncClient(timeout=setting_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getSettings")
        data = response.json()

    if data:
        # print(data)
        return {"success": True, "data": data}
    else:
        return {"success": False, "error": "No Data"}

@router.get('/getDiagnosisProfile')
async def get_diagnosisprofile(request:Request):

    async with httpx.AsyncClient(timeout=setting_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getProfile")
        data = response.json()

    if data:
        return {"success": True, "data": data}
    else:
        return {"success": False, "error": "No Data"}

@router.post('/setDiagnosisSetting')
async def set_diagnosissetting(request: Request):
    data = await request.json()
    status = 0
    if not data:
        return {"status": "1", "success": False, "error": ["No data provided"]}
    try:

        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.post(f"http://{os_spec.restip}:5000/api/setSettings", json=data)
            data = response.json()

    except Exception as e:
        print("Error:", e)
        return {"status": "0", "success": False, "error": [str(e)]}

    if data:
        if data["Status"] == 0:
            return {"status": "1", "success": True }
        else:
            return {"status": "1", "success": False, "error": data["Messages"]}
    else:
        return {"status": "1", "success": False, "error": ["Save failed in setSettings API"]}

@router.post('/setDiagnosisProfile')
async def set_diagnosisprofile(request: Request):
    data = await request.json()
    if not data:
        return {"status": "1", "success": False, "error": ["No data provided"]}
    try:

        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.post(f"http://{os_spec.restip}:5000/api/setProfile", json=data)
            data = response.json()

    except Exception as e:
        print("Error:", e)
        return {"status": "0", "success": False, "error": [str(e)]}

    if data:
        if data["Status"] == 0:
            return {"status": "1", "success": True }
        else:
            return {"status": "1", "success": False, "error": data["Messages"]}
    else:
        return {"status": "1", "success": False, "error": ["Save Failed in setProfile API"]}

@router.get("/getAssetTypes")  # Diagnosis, Report Vue : get Asset info
async def get_assetTypes(request: Request):

    async with httpx.AsyncClient(timeout=setting_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getAssetTypes")
        data = response.json()

    if data:
        return {"success": True, "data": data}
    else:
        return {"success": False, "error": "No Data"}

@router.get('/getAssetList')
async def get_assetlist(request: Request):

    async with httpx.AsyncClient(timeout=setting_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getAssetHierarchy")
        datas = response.json()


    if len(datas) > 0:
        grouped = defaultdict(list)
        for item in datas:
            aid = item["AssemblyType"]
            if aid is not None and aid != "null" and item["AssemblyID"] !="null" and item["Name"] !="Plant":
                grouped[aid].append({
                    "Name": item["Name"],
                    "Type": aid
                })
        return {'success': True, "data":grouped}
    else:
        return {'success': False, "msg": 'No exist assets'}

@router.post('/upload')  # upload setup.json
def upload_file(file: UploadFile = File(...)):
    if file.filename == '':
        return {'passOK': '0', 'error': 'No selected file'}

    # 기존 setup.json 파일 경로
    original_file_path = os.path.join(SETTING_FOLDER, 'setup.json')
    backup_file_path = os.path.join(SETTING_FOLDER, 'setup_backup.json')

    try:

        
        # 기존 setup.json 파일이 존재하면 백업
        if os.path.exists(original_file_path):
            shutil.copy(original_file_path, backup_file_path)  # setup.json을 setting_backup.json으로 백업

        # 업로드된 파일을 setup.json으로 저장
        with open(original_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file.file.seek(0)  # 다시 읽기 위해 커서 초기화
        file_content = file.file.read().decode("utf-8")

        # Redis에 그대로 문자열로 저장
        # redis_state.client.execute_command("SELECT", 0)
        redis_state.client.hset("System", "setup", file_content)
        redis_state.client.hset("Service", "save", 1)
        redis_state.client.hset("Service", "restart", 1)
        return {'passOK': '1', 'file_path': original_file_path}

    except Exception as e:
        return {'passOK': '0', 'error': str(e)}

@router.get('/checkBearing')
def load_bearings_from_db():
    """DB에서 Bearing 데이터 로드"""
    try:
        # DB 경로 확인
        print(f"DB Path: {BEARINGDB_PATH}")
        
        # DB 초기화 (테이블이 없으면 생성)
        conn = sqlite3.connect(str(BEARINGDB_PATH))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bearings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT UNIQUE NOT NULL,
                BPFO REAL NOT NULL,
                BPFI REAL NOT NULL,
                BSF REAL NOT NULL,
                FTF REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        
        # 데이터 조회
        cursor.execute('SELECT Name, BPFO, BPFI, BSF, FTF FROM bearings ORDER BY Name')
        rows = cursor.fetchall()
        
        # 수동으로 딕셔너리 변환
        result = []
        for row in rows:
            result.append({
                'Name': row[0],
                'BPFO': float(row[1]),
                'BPFI': float(row[2]),
                'BSF': float(row[3]),
                'FTF': float(row[4])
            })
        
        conn.close()
        
        print(f"Loaded {len(result)} bearings from DB")
        
        if len(result) == 0:
            return {'passOK': '1', 'data': [], 'msg': 'No bearing data in database'}
        
        return {'passOK': '1', 'data': result}
        
    except Exception as e:
        print(f"DB Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'passOK': '0', 'msg': f'Database error: {str(e)}'}

def init_bearing_db_from_csv():
    """초기 Bearing DB 파일(NTEKBearingDB.csv)을 DB에 업로드"""
    try:
        logging.info("🔄 Starting bearing DB initialization...")
        
        # ✅ 1. DB 연결 및 테이블 생성 (먼저!)
        conn = sqlite3.connect(str(BEARINGDB_PATH))
        cursor = conn.cursor()
        
        logging.info(f"📂 DB Path: {BEARINGDB_PATH}")
        
        # ✅ 테이블 생성 (없으면 생성)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bearings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT UNIQUE NOT NULL,
                BPFO REAL NOT NULL,
                BPFI REAL NOT NULL,
                BSF REAL NOT NULL,
                FTF REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        logging.info("✅ Bearing table created/verified")
        
        # ✅ 2. 파일 경로 확인
        bearing_file = SETTING_FOLDER / "NTEKBearingDB.csv"
        logging.info(f"📂 CSV Path: {bearing_file}")
        
        if not bearing_file.exists():
            conn.close()
            logging.warning(f"⚠️ NTEKBearingDB.csv not found at {bearing_file}")
            return {'success': False, 'msg': 'NTEKBearingDB.csv file not found'}
        
        # ✅ 3. 파일에서 데이터 읽기
        data = get_Bearing(str(bearing_file))
        
        if not data or len(data) == 0:
            conn.close()
            logging.warning("⚠️ No bearing data in file")
            return {'success': False, 'msg': 'No bearing data in file'}
        
        logging.info(f"📋 Parsed {len(data)} bearings from CSV")
        
        # ✅ 4. 데이터 삽입
        inserted_count = 0
        skipped_count = 0
        
        for bearing in data:
            try:
                name = str(bearing.get('Name', ''))
                bpfo = float(bearing.get('BPFO', 0))
                bpfi = float(bearing.get('BPFI', 0))
                bsf = float(bearing.get('BSF', 0))
                ftf = float(bearing.get('FTF', 0))
                
                cursor.execute('''
                    INSERT INTO bearings (Name, BPFO, BPFI, BSF, FTF)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, bpfo, bpfi, bsf, ftf))
                
                inserted_count += 1
                
            except sqlite3.IntegrityError:
                skipped_count += 1
                continue
            except Exception as e:
                logging.error(f"Error inserting bearing {bearing.get('Name')}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        logging.info(f"✅ Bearing DB initialized: {inserted_count} inserted, {skipped_count} skipped")
        
        return {
            'success': True,
            'inserted': inserted_count,
            'skipped': skipped_count,
            'msg': f'Successfully initialized bearing database'
        }
        
    except Exception as e:
        logging.error(f"❌ Bearing DB initialization error: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'msg': str(e)}
      
@router.post('/uploadBearing')
def upload_bearing_to_db(file: UploadFile = File(...)):
    """업로드된 Bearing 파일을 DB에 저장"""
    if file.filename == '':
        return {'passOK': '0', 'error': 'No selected file'}

    try:
        # 임시 파일로 저장
        temp_file_path = os.path.join(SETTING_FOLDER, file.filename)
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 파일에서 데이터 읽기
        data = get_Bearing(temp_file_path)
        
        print(f"Parsed {len(data)} bearings from file")
        
        # DB에 삽입
        conn = sqlite3.connect(str(BEARINGDB_PATH))
        cursor = conn.cursor()
        
        inserted = []
        skipped = []
        
        for bearing in data:
            try:
                # 데이터 타입 확인 및 변환
                name = str(bearing.get('Name', ''))
                bpfo = float(bearing.get('BPFO', 0))
                bpfi = float(bearing.get('BPFI', 0))
                bsf = float(bearing.get('BSF', 0))
                ftf = float(bearing.get('FTF', 0))
                
                cursor.execute('''
                    INSERT INTO bearings (Name, BPFO, BPFI, BSF, FTF)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, bpfo, bpfi, bsf, ftf))
                
                inserted.append({
                    'Name': name,
                    'BPFO': bpfo,
                    'BPFI': bpfi,
                    'BSF': bsf,
                    'FTF': ftf
                })
                print(f"Inserted: {name}")
                
            except sqlite3.IntegrityError:
                skipped.append(bearing.get('Name', 'Unknown'))
                print(f"Skipped (duplicate): {bearing.get('Name', 'Unknown')}")
                continue
            except Exception as e:
                print(f"Error inserting bearing: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"Total inserted: {len(inserted)}, Skipped: {len(skipped)}")
        
        # 파일을 날짜와 함께 백업 저장
        if os.path.exists(temp_file_path):
            # 현재 날짜/시간 (YYYYMMDD_HHMMSS 형식)
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H")
            
            # 파일명과 확장자 분리
            file_base, file_ext = os.path.splitext(file.filename)
            
            # 새 파일명: 원본파일명_YYYYMMDD_HHMMSS.확장자
            backup_filename = f"{file_base}_{timestamp}{file_ext}"
            backup_path = os.path.join(SETTING_FOLDER, backup_filename)
            
            # 파일 복사 (이동이 아닌 복사)
            shutil.copy(temp_file_path, backup_path)
            print(f"Backup saved: {backup_filename}")
            
            # 임시 파일 삭제
            os.remove(temp_file_path)
        
        if len(inserted) == 0 and len(skipped) > 0:
            return {
                'passOK': '1', 
                'data': [], 
                'msg': f'All {len(skipped)} bearings already exist in database'
            }
        
        return {
            'passOK': '1', 
            'data': inserted, 
            'inserted': len(inserted),
            'skipped': len(skipped)
        }

    except Exception as e:
        print(f"Upload Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'passOK': '0', 'error': str(e)}

def init_bearing_db():
    """Bearing 데이터베이스 초기화"""
    conn = sqlite3.connect(BEARINGDB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bearings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT UNIQUE NOT NULL,
            BPFO REAL NOT NULL,
            BPFI REAL NOT NULL,
            BSF REAL NOT NULL,
            FTF REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_all_bearings():
    """DB에서 모든 Bearing 데이터 조회"""
    try:
        conn = sqlite3.connect(BEARINGDB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT Name, BPFO, BPFI, BSF, FTF FROM bearings ORDER BY Name')
        rows = cursor.fetchall()
        
        result = [dict(row) for row in rows]
        conn.close()
        
        return result
    except Exception as e:
        print(f"DB 조회 오류: {e}")
        return []

def insert_bearings(bearing_list):
    """새로운 Bearing 데이터를 DB에 삽입 (중복 제외)"""
    try:
        conn = sqlite3.connect(BEARINGDB_PATH)
        cursor = conn.cursor()
        
        inserted = []
        for bearing in bearing_list:
            try:
                cursor.execute('''
                    INSERT INTO bearings (Name, BPFO, BPFI, BSF, FTF)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    bearing['Name'],
                    float(bearing['BPFO']),
                    float(bearing['BPFI']),
                    float(bearing['BSF']),
                    float(bearing['FTF'])
                ))
                inserted.append(bearing)
            except sqlite3.IntegrityError:
                # 중복된 Name은 무시
                continue
        
        conn.commit()
        conn.close()
        
        return inserted
    except Exception as e:
        print(f"DB 삽입 오류: {e}")
        return []
@router.get('/download')  # download setup.json
def download_setting():
    file_path = os.path.join(SETTING_FOLDER, 'setup.json')

    # 파일이 존재하지 않으면 에러 처리
    if not os.path.exists(file_path):
        return {"passOK": "0", "error": "setting file not found"}

    try:
        # 파일을 클라이언트로 다운로드 응답
        response = FileResponse(file_path, media_type="application/json", filename="setup.json")
        response.headers["Content-Disposition"] = "attachment; filename=setup.json"  # 다운로드 강제
        return response
    except Exception as e:
        return {"passOK": "0", "error": f"An unexpected error occurred: {str(e)}"}


async def reset_smart(asset, mode):
    if mode == 0:
        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.get(f"http://{os_spec.restip}:5000/api/unregisterAsset?name={asset}")
            data = response.json()
    else:
        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.get(f"http://{os_spec.restip}:5000/api/deleteAsset?name={asset}")
            data = response.json()
    return data


@router.post('/createAsset')
async def createAsset(request: Request):
    data = await request.json()

    if not data:
        return {"status": "0", "error": "No data provided"}
    assetType = data['assetType']
    assetName = data['assetName']
    print("assetType",assetType,"assetName",assetName)
    try:
        # response = await  http_state.client.get(f"/createAsset?type={assetType}&name={assetName}")
        # datas = response.json()
        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.get(f"http://{os_spec.restip}:5000/api/createAsset?type={assetType}&name={assetName}")
            datas = response.json()
        #     if response.status_code in [400, 401, 500]:
        #         flag = await checkLoginAPI(request)
        #         if not flag:
        #             return {"success": False, "error": "Restful API Login Failed"}
        #         else:
        #             response = await client.get(f"http://{os_spec.restip}:5000/api/createAsset?type={assetType}&name={assetName}")
        #             datas = response.json()
    except Exception as e:
        print(str(e))
        return {"status": "0", "error": "Created Failed"}

    if datas:
        if datas["Status"] == 0:
            return {"status": "1"}
        else:
            return {"status": "0", "error": "Create Failed"}  # 성공해도 리스트에는 추가안된상태로 리턴되서 여기로빠짐
    else:
        return {"status": "0", "error": "Create Failed"}
    # if len(datas) > 0:
    #     if assetName in datas:
    #         return {"status": "1"}
    #     else:
    #         return {"status": "0", "error": "Create Failed"} #성공해도 리스트에는 추가안된상태로 리턴되서 여기로빠짐
    # else:
    #     return {"status": "0", "error": "Create Failed"}

@router.post('/modifyAsset')
async def modifyAsset(request: Request):
    data = await request.json()
    if not data:
        return {"status": "0", "error": "No data provided"}
    assetName = data.get("assetName") 
    newName = data.get("newName")
    try:
        # response = await  http_state.client.get(f"/renameAsset?name={assetName}&newname={newName}")
        # datas = response.json()
        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.get(f"http://{os_spec.restip}:5000/api/renameAsset?name={assetName}&newname={newName}")
            datas = response.json()
        #     if response.status_code in [400, 401, 500]:
        #         flag = await checkLoginAPI(request)
        #         if not flag:
        #             return {"success": False, "error": "Restful API Login Failed"}
        #         else:
        #             response = await client.get(f"http://{os_spec.restip}:5000/api/renameAsset?name={assetName}&newname={newName}")
        #             datas = response.json()
    except Exception as e:
        return {"status": "0", "error": "Modify Failed"}

    if datas:
        if datas["Status"] == 0:
            return {"status": "1"}
        else:
            return {"status": "0", "error": "Modify Failed"}  # 성공해도 리스트에는 추가안된상태로 리턴되서 여기로빠짐
    else:
        return {"status": "0", "error": "Modify Failed"}
    # if len(datas) > 0:
    #     if newName in datas:
    #         return {"status": "1"}
    #     else:
    #         return {"status": "0", "error": "Modify Failed"}
    # else:
    #     return {"status": "0", "error": "Modify Failed"}

@router.get('/deleteAsset/{asset}')
async def deleteAsset(asset):
    try:
        datas = await reset_smart(asset, 1)
        # async with httpx.AsyncClient(timeout=setting_timeout) as client:
        #     response = await client.get(f"http://{os_spec.restip}:5000/api/deleteAsset?name={asset}")
        #     datas = response.json()
    except Exception as e:
        print(str(e))
        return {"status": "0", "error": "Delete Failed"}

    if datas:
        if datas["Status"] == 0:
            return {"status": "1"}
        else:
            return {"status": "0", "error": "Delete Failed"}  # 성공해도 리스트에는 추가안된상태로 리턴되서 여기로빠짐
    else:
        return {"status": "0", "error": "Delete Failed"}

    # if len(datas) > 0:
    #     if not asset in datas:
    #         return {"status": "1"}
    #     else:
    #         return {"status": "0", "error": "Delete Failed"}
    # else:
    #     return {"status": "1"}

@router.get('/unregisterAsset/{channel}/{asset}')
async def unreg_Asset(channel, asset):
    # async with httpx.AsyncClient(timeout=setting_timeout) as client:
    #     response = await client.get(f"http://{os_spec.restip}:5000/api/unregisterAsset?name={asset}")
    #     data = response.json()
    data = await reset_smart(asset, 0)
    # remove_applyStatus(channel, asset)
    if isinstance(data, list) and len(data) > 0:
        finflag = True
    else:
        finflag = False
    # redis_state.client.execute_command("SELECT", 0)
    if redis_state.client.hexists("System","setup"):
        datStr = redis_state.client.hget("System","setup")
        setting = json.loads(datStr)
        for chInfo in setting["channel"]:
            if channel == chInfo["channel"]:
                chInfo["assetInfo"]["name"] =''
                chInfo["assetInfo"]["type"] = ''
                finflag = True
                break
        redis_state.client.hset("System","setup", json.dumps(setting))
    if finflag:
        return {"success":True}
    else:
        return {"success":False}


@router.get('/registerAsset/{channel}/{assetName}/{assetType}')
async def reg_Asset(channel, assetName, assetType):
    async with httpx.AsyncClient(timeout=setting_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/registerAsset?name={assetName}")
        data = response.json()
    if isinstance(data, list) and len(data) > 0:
        finflag = True
    else:
        finflag = False
    # redis_state.client.execute_command("SELECT", 0)
    if redis_state.client.hexists("System","setup"):
        datStr = redis_state.client.hget("System","setup")
        setting = json.loads(datStr)
        for chInfo in setting["channel"]:
            if channel == chInfo["channel"]:
                chInfo["assetInfo"]["name"] = assetName
                chInfo["assetInfo"]["type"] = assetType
                finflag = True
                break
        redis_state.client.hset("System","setup", json.dumps(setting))

        # set_applyStatus(channel, assetName)
    if finflag:
        return {"success":True}
    else:
        return {"success":False}

# def make_applyStatus():
#     equipStatus = {
#         "restartFW": False,
#         "commisionAsset": {
#             "Main": {
#                 "Name": '',
#                 "result": False,
#             },
#             "Sub": {
#                 "Name": '',
#                 "result": False,
#             }
#         }
#     }
#     return equipStatus

# def set_applyStatus(channel, assetName):
#     if redis_state.client.hexists("Equipment", "applyStatus"):
#         applyst = redis_state.client.hget("Equipment", "applyStatus")
#         equipStatus = json.loads(applyst)
#     else:
#         equipStatus = make_applyStatus()
#     if equipStatus["commisionAsset"].get(channel):
#         if equipStatus["commisionAsset"][channel]["Name"] == '':
#             equipStatus["commisionAsset"][channel]["Name"] = assetName
#             equipStatus["commisionAsset"][channel]["result"] = False
#         elif equipStatus["commisionAsset"][channel]["Name"] == assetName:
#             equipStatus["commisionAsset"][channel]["result"] = False
#     else:
#         equipStatus["commisionAsset"][channel] = {
#             "Name": assetName,
#             "result": False
#         }
#     redis_state.client.hset("Equipment", "applyStatus", json.dumps(equipStatus))
#
#
# def remove_applyStatus(channel, assetName):
#     if redis_state.client.hexists("Equipment", "applyStatus"):
#         applyst = redis_state.client.hget("Equipment", "applyStatus")
#         equipStatus = json.loads(applyst)
#
#         if equipStatus["commisionAsset"].get(channel):
#             if equipStatus["commisionAsset"][channel]["Name"] == assetName:
#                 equipStatus["commisionAsset"][channel]["Name"] = ''
#                 equipStatus["commisionAsset"][channel]["result"] = False
#
#         redis_state.client.hset("Equipment", "applyStatus", json.dumps(equipStatus))

def save_alarm_configs_to_redis(setting_dict: dict):
    dash_alarms_data = {}

    # 각 채널 순회
    for channel_config in setting_dict.get("channel", []):
        channel_name = channel_config.get("channel")
        asset_info = channel_config.get("assetInfo", {})
        status_info = channel_config.get("status_Info", {})
        # use_do = channel_config.get("useDO", 0)  # 채널별 useDO
        confStatus = channel_config.get("confStatus", 0)  # 채널별 useDO
        if not channel_name:
            continue

        # useDO가 0이면 해당 채널은 저장하지 않음 (기존 로직 사용)
        if confStatus == 0:
            continue

        # 채널별 DashAlarms 데이터
        dash_alarms_data[channel_name] = {
            "assetType": asset_info.get("type", ""),
            "assetName": asset_info.get("name", ""),
            "assetNickName": asset_info.get("nickname", ""),
            "diagnosis": status_info.get("diagnosis", []),
            "pq": status_info.get("pq", [])
        }

    return dash_alarms_data

def save_ai_configs_to_redis(setting_dict: dict):
    ai_data = {}

    # 각 채널 순회
    for channel_config in setting_dict.get("channel", []):
        channel_name = channel_config.get("channel")
        status_info = channel_config.get("ai_modbus", [])
        # use_do = channel_config.get("useDO", 0)  # 채널별 useDO
        confStatus = channel_config.get("useAI", 0)  # 채널별 useDO
        if not channel_name:
            continue

        # useDO가 0이면 해당 채널은 저장하지 않음 (기존 로직 사용)
        if confStatus == 0:
            continue

        # 채널별 DashAlarms 데이터
        ai_data[channel_name] = [item for item in status_info if item.get("enable") == 1]

    return ai_data


def initialize_alarm_configs(channel, alams):
    rediskey = f"alarm_status:{channel}"
    alarmdict = {}
    for j in range(1, 33):
        if alams[str(j)][0] != 0:
            alarmdict[str(j)] = alams[str(j)]
    if len(alarmdict.keys()) > 0:
        # redis_state.client_db1.execute_command("SELECT", 1)
        redis_state.client_db1.delete(rediskey)
        for key in alarmdict:
            if alarmdict[key][1] == 0:
                condstr = 'UNDER'
            else:
                condstr = 'OVER'
            init_data = {
                "status": 0,
                "count": 0,
                "condition": condstr,
                "value": 0,
                "chan": alarmdict[key][0],
                "cond": alarmdict[key][1],
                "level": alarmdict[key][3],
                "chan_text": parameter_options[alarmdict[key][0]],
                "last_update": int(datetime.now().timestamp()),
                "status_text": "None"
            }
            redis_state.client_db1.hset(rediskey, key, json.dumps(init_data))

@router.post('/savefile/{channel}')  # save setup.json
async def saveSetting(channel: str, request: Request):
    deviceMac = get_mac_address()
    ser=''
    ctSetup = {}
    if os_spec.os != 'Windows':
        mac_file_path = os.path.join(SETTING_FOLDER, 'serial_num_do_not_modify.txt')
        if os.path.exists(mac_file_path):
            ser = read_mac_plain(mac_file_path)
            # if ser != deviceMac:
            #     deviceMac = ser
    # redis_state.client.select(0)
    if redis_state.client.hexists("Service","setting"):
        checkflag = redis_state.client.hget("Service","setting")
        if int(checkflag) == 1:
            return {"status": "0", "error": "Modbus setting is activated"}
    try:
        FILE_PATH = os.path.join(SETTING_FOLDER, "setup.json")
        #FTP_PATH = os.path.join(SETTING_FOLDER, "WaveformFTP.json")
        # 클라이언트로부터 JSON 데이터 받기
        data = await request.json()
        if not data:
            return {"status": "0", "error": "No data provided"}

        # 파일이 존재하면 읽기, 없으면 기본 구조 생성
        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                setting = json.load(f)
        else:
            # 기본 JSON 구조 (필요에 따라 수정)
            setting = {"mode": "device", "General": {}, "channel": []}

        # 채널 파라미터가 "general"이면 "General" 부분 업데이트
        if channel.lower() == "general":        
            setting["General"] = data
        # elif channel.lower() == "status":
        #     setting["status_Info"] = data
        else:
            # 그 외의 경우, "channel" 배열 내에서 해당 채널 업데이트 (없으면 추가)
            if "channel" not in setting or not isinstance(setting["channel"], list):
                setting["channel"] = []
            updated = False
            for idx, ch in enumerate(setting["channel"]):
                if ch.get("channel", "").lower() == channel.lower():
                    setting["channel"][idx] = data
                    updated = True
                    setting["channel"][idx]["ctInfo"]["inorminal"] = int(float(data["ctInfo"]["inorminal"])*1000)
                    break
            if not updated:
                setting["channel"].append(data)

        # 업데이트된 설정을 파일에 저장 (덮어쓰기)
        if deviceMac != setting["General"]["deviceInfo"]["mac_address"]:
            setting["General"]["deviceInfo"]["mac_address"] = deviceMac
            # setting["General"]["deviceInfo"]["serial_number"] = deviceMac
        if ser != '':
            setting["General"]["deviceInfo"]["serial_number"] = ser
        else:
            setting["General"]["deviceInfo"]["serial_number"] = deviceMac

        with open(FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(setting, f, indent=4)

        if len(setting["channel"]) > 0:
            for i in range(0,len(setting["channel"])):
                initialize_alarm_configs(setting["channel"][i]["channel"], setting["channel"][i]["alarm"])

        # redis_state.client.select(0)
        saveCurrent = saveStartCurrent(setting)
        dash_alarms_data = save_alarm_configs_to_redis(setting)
        redis_state.client.hset("System", "setup", json.dumps(setting))
        redis_state.client.hset("Equipment", "StartingCurrent", json.dumps(saveCurrent))
        if dash_alarms_data:
            redis_state.client.hset("Equipment", "DashAlarms", json.dumps(dash_alarms_data))
        else:
            redis_state.client.hdel("Equipment", "DashAlarms")
        return {"status": "1", "data": setting}
    except Exception as e:
        print("Error:", e)
        return {"status": "0", "error": str(e)}

def compare_channel_changes(redis_data: dict, post_data: dict) -> Dict[str, Any]:
    result = {
        "General": {"status": "no_change", "changed_fields": []},
        "Main": {"status": "disabled", "changed_fields": []},
        "Sub": {"status": "disabled", "changed_fields": []}
    }

    # General 비교 - 모든 필드 체크
    redis_general = redis_data.get("General", {})
    post_general = post_data.get("General", {})

    general_fields_to_compare = [
        "va_type", "pf_sign", "unbalance",
        "deviceInfo", "tcpip", "modbus",
        "useFuction", "ftpInfo", "sntpInfo"
    ]

    general_changed_fields = []
    for field in general_fields_to_compare:
        redis_val = redis_general.get(field)
        post_val = post_general.get(field)

        # 딕셔너리인 경우 깊은 비교
        if isinstance(redis_val, dict) and isinstance(post_val, dict):
            if redis_val != post_val:
                general_changed_fields.append(field)
        elif redis_val != post_val:
            general_changed_fields.append(field)

    if general_changed_fields:
        result["General"]["status"] = "config_changed"
        result["General"]["changed_fields"] = general_changed_fields

    # Channel 비교
    redis_channels = {ch["channel"]: ch for ch in redis_data.get("channel", [])}
    post_channels = {ch["channel"]: ch for ch in post_data.get("channel", [])}

    channel_fields_to_compare = [
        "Enable", "PowerQuality", "ctInfo", "ptInfo", "assetInfo",
        "eventInfo", "sampling", "demand", "trendInfo", "alarm",
        "n_kva", "confStatus","status_Info", "useDO", "useAI", "ai_modbus"
    ]

    for channel_name in ["Main", "Sub"]:
        redis_ch = redis_channels.get(channel_name, {})
        post_ch = post_channels.get(channel_name, {})

        if post_ch.get("Enable") != 1:
            continue

        changed_fields = []
        for field in channel_fields_to_compare:
            redis_val = redis_ch.get(field)
            post_val = post_ch.get(field)

            # 딕셔너리/리스트인 경우 깊은 비교
            if isinstance(redis_val, (dict, list)) and isinstance(post_val, (dict, list)):
                if redis_val != post_val:
                    changed_fields.append(field)
            elif redis_val != post_val:
                changed_fields.append(field)

        result[channel_name]["changed_fields"] = changed_fields

        if not changed_fields:
            result[channel_name]["status"] = "no_change"
        elif changed_fields == ["assetInfo"]:
            result[channel_name]["status"] = "asset_only"
        else:
            result[channel_name]["status"] = "config_changed"

    return result


# @router.post('/savefileNew')  # ⭐ {channel} 제거
# async def saveSetting2(request: Request):
#     deviceMac = get_mac_address()
#     ser = ''
#
#     if os_spec.os != 'Windows':
#         mac_file_path = os.path.join(SETTING_FOLDER, 'serial_num_do_not_modify.txt')
#         if os.path.exists(mac_file_path):
#             ser = read_mac_plain(mac_file_path)
#
#     # redis_state.client.select(0)
#     if redis_state.client.hexists("Service", "setting"):
#         checkflag = redis_state.client.hget("Service", "setting")
#         if int(checkflag) == 1:
#             return {"status": "0", "error": "Modbus setting is activated"}
#
#     try:
#         FILE_PATH = os.path.join(SETTING_FOLDER, "setup.json")
#
#         # 클라이언트로부터 전체 설정 데이터 받기
#         data = await request.json()
#         if not data:
#             return {"status": "0", "error": "No data provided"}
#
#         # 기본 구조 확인
#         if "General" not in data:
#             data["General"] = {}
#         if "channel" not in data or not isinstance(data["channel"], list):
#             data["channel"] = []
#
#         # MAC 주소 및 시리얼 번호 업데이트
#         if "deviceInfo" not in data["General"]:
#             data["General"]["deviceInfo"] = {}
#
#         data["General"]["deviceInfo"]["mac_address"] = deviceMac
#
#         if ser != '':
#             data["General"]["deviceInfo"]["serial_number"] = ser
#         else:
#             data["General"]["deviceInfo"]["serial_number"] = deviceMac
#
#         # 각 채널의 ctInfo.inorminal 값 처리
#
#         for ch in data["channel"]:
#             if "ctInfo" in ch and "inorminal" in ch["ctInfo"]:
#                 ch["ctInfo"]["inorminal"] = int(float(ch["ctInfo"]["inorminal"]) * 1000)
#
#
#         prevSetup = redis_state.client.hget("System", "setup")
#         prevData = json.loads(prevSetup)
#
#         # 파일에 저장
#         with open(FILE_PATH, "w", encoding="utf-8") as f:
#             json.dump(data, f, indent=4)
#
#         # 알람 설정 초기화
#         if len(data["channel"]) > 0:
#             for ch in data["channel"]:
#                 if "channel" in ch and "alarm" in ch:
#                     initialize_alarm_configs(ch["channel"], ch["alarm"])
#
#         # Redis에 저장
#         # saveCurrent = saveStartCurrent(data)
#         procData = save_StartCurrent_DemandInterval_SamplingPeriod(data)
#         dash_alarms_data = save_alarm_configs_to_redis(data)
#         result = compare_channel_changes(prevData, data)
#         restartAsset = False
#         restartdevice = False
#         if result["General"]["status"] == 'config_changed' or result["Main"]["status"] == 'config_changed' or result["Sub"]["status"] == 'config_changed':
#             restartdevice = True
#         elif result["Main"]["status"] == 'asset_only' or result["Sub"]["status"] == 'asset_only':
#             restartAsset = True
#
#         checkResult = check_ApplyStatus()
#
#         if not restartAsset:
#             commision_asset = checkResult.get("commisionAsset", {})
#
#             for channel in ["Main", "Sub"]:
#                 channel_data = commision_asset.get(channel, {})
#                 if channel_data.get("Name") and not channel_data.get("result", False):
#                     restartAsset = True
#                     break  # 하나라도 해당되면 바로 종료
#
#         if not restartdevice:
#             if not checkResult["restartFW"]:
#                 restartdevice = True
#
#         redis_state.client.hset("System", "setup", json.dumps(data))
#         redis_state.client.hset("Equipment", "StartingCurrent", json.dumps(procData["StartCurrent"]))
#         redis_state.client.hset("Equipment", "DemandInterval", json.dumps(procData["Demand"]))
#         redis_state.client.hset("Equipment", "SamplingPeriod", json.dumps(procData["Sampling"]))
#
#         if dash_alarms_data:
#             redis_state.client.hset("Equipment", "DashAlarms", json.dumps(dash_alarms_data))
#         else:
#             redis_state.client.hdel("Equipment", "DashAlarms")
#
#         return {"status": "1", "data": data, "restartDevice": restartdevice, "restartAsset": restartAsset}
#
#     except Exception as e:
#         print("Error:", e)
#         import traceback
#         traceback.print_exc()
#         return {"status": "0", "error": str(e)}

@router.post('/savefileNew')  # ⭐ {channel} 제거
async def saveSetting2(request: Request):
    deviceMac = get_mac_address()
    ser = ''

    if os_spec.os != 'Windows':
        mac_file_path = os.path.join(SETTING_FOLDER, 'serial_num_do_not_modify.txt')
        if os.path.exists(mac_file_path):
            ser = read_mac_plain(mac_file_path)

    if redis_state.client.hexists("Service", "setting"):
        checkflag = redis_state.client.hget("Service", "setting")
        if int(checkflag) == 1:
            return {"status": "0", "error": "Modbus setting is activated"}

    try:

        data = await request.json()
        if not data:
            return {"status": "0", "error": "No data provided"}

        # 기본 구조 확인
        if "General" not in data:
            data["General"] = {}
        if "channel" not in data or not isinstance(data["channel"], list):
            data["channel"] = []

        # MAC 주소 및 시리얼 번호 업데이트
        if "deviceInfo" not in data["General"]:
            data["General"]["deviceInfo"] = {}

        data["General"]["deviceInfo"]["mac_address"] = deviceMac

        if ser != '':
            data["General"]["deviceInfo"]["serial_number"] = ser
        else:
            data["General"]["deviceInfo"]["serial_number"] = deviceMac

        # 각 채널의 ctInfo.inorminal 값 처리

        for ch in data["channel"]:
            if "ctInfo" in ch and "inorminal" in ch["ctInfo"]:
                ch["ctInfo"]["inorminal"] = int(float(ch["ctInfo"]["inorminal"]) * 1000)

        redis_state.client.hset("System", "config", json.dumps(data))
        return {"status": "1"}
    except Exception as e:
        print("Error:", e)
        import traceback
        traceback.print_exc()
        return {"status": "0", "error": str(e)}


@router.get('/apply')
def apply():
    if redis_state.client.hexists("Service", "setting"):
        checkflag = redis_state.client.hget("Service", "setting")
        if int(checkflag) == 1:
            return {"status": "0", "error": "Modbus setting is activated"}

    saveSetup = redis_state.client.hget("System", "config")
    saveData = json.loads(saveSetup)

    prevSetup = redis_state.client.hget("System", "setup")
    prevData = json.loads(prevSetup)

    FILE_PATH = os.path.join(SETTING_FOLDER, "setup.json")

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(saveData, f, indent=4)

    if len(saveData["channel"]) > 0:
        for ch in saveData["channel"]:
            if "channel" in ch and "alarm" in ch:
                initialize_alarm_configs(ch["channel"], ch["alarm"])

    procData = save_StartCurrent_DemandInterval_SamplingPeriod(saveData)
    dash_alarms_data = save_alarm_configs_to_redis(saveData)
    ai_data = save_ai_configs_to_redis(saveData)
    result = compare_channel_changes(prevData, saveData)

    restartdevice = False

    if result["General"]["status"] == 'config_changed' or result["Main"]["status"] == 'config_changed' or result["Sub"][
        "status"] == 'config_changed':
        restartdevice = True

    redis_state.client.hset("System", "setup", json.dumps(saveData))
    redis_state.client.hset("Equipment", "StartingCurrent", json.dumps(procData["StartCurrent"]))
    redis_state.client.hset("Equipment", "DemandInterval", json.dumps(procData["Demand"]))
    redis_state.client.hset("Equipment", "SamplingPeriod", json.dumps(procData["Sampling"]))
    redis_state.client.hset("Equipment", "ChannelData", json.dumps(procData["Channel"]))

    if dash_alarms_data:
        redis_state.client.hset("Equipment", "DashAlarms", json.dumps(dash_alarms_data))
    else:
        redis_state.client.hdel("Equipment", "DashAlarms")

    if ai_data:
        redis_state.client.hset("Equipment", "AIConfig", json.dumps(ai_data))
    else:
        redis_state.client.hdel("Equipment", "AIConfig")

    return {"status": "1", "data": saveData, "restartDevice": restartdevice}

@router.get('/checkCommision/{asset}')
async def check_comm(asset):
    try:
        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.get(f"http://{os_spec.restip}:5000/api/iscommrequired?name={asset}")
            data = response.json()

        if data:
            return {"status": 1, "result": data["CommissioningRequired"]}
        else:
            return {"status": 0, "error": "Failed to call API"}
    except Exception as e:
        return {"status": 0, "error": str(e)}

@router.get('/checkSmart')
def check_smart():
    if is_service_active("smartsystemsrestapiservice"):
        return {"success": True}
    else:
        return {"success": False}


@router.get('/manageSmart/{mode}')
async def manage_smart(mode):
    restartsmart = False
    restartapi = False

    if int(mode) == 1:
        if is_service_enabled("smartsystemsrestapiservice"):
            if not is_service_active("smartsystemsrestapiservice"):
                ret = sysService("start", "SmartAPI")
                restartapi = ret["success"]
            else:
                restartapi = True
        else:
            ret = sysService("enable", "SmartAPI")
            if ret["success"]:
                ret = sysService("start", "SmartAPI")
                restartapi = ret["success"]

        if restartapi:
            max_attempts = 30  # 최대 15초 (30 * 0.5초)
            for i in range(max_attempts):
                if await checkSmartAPI_active():
                    logging.debug(f"✅ SmartAPI ready after {i * 0.5:.1f}s")
                    break

                if i == max_attempts - 1:
                    logging.warning("⚠️ SmartAPI start timeout")
                    return {
                        "api": False,
                        "smart": restartsmart,
                        "success": False,  # ⭐ 추가
                        "message": "Service started but not responding"
                    }

                await asyncio.sleep(0.5)
            if not is_service_enabled("smartsystemsservice"):
                ret = sysService("enable", "SmartSystems")
                restartsmart = ret["success"]
    else:  # mode == 0
        if service_exists("smartsystemsservice.service"):
            if is_service_enabled("smartsystemsrestapiservice"):
                if is_service_active("smartsystemsrestapiservice"):
                    ret = sysService("stop", "SmartAPI")
                    restartapi = ret["success"]
                sysService("disable", "SmartAPI")

            if is_service_enabled("smartsystemsservice"):
                if is_service_active("smartsystemsservice"):
                    ret = sysService("stop", "SmartSystems")
                    restartsmart = ret["success"]
                sysService("disable", "SmartSystems")

    return {
        "api": restartapi,
        "smart": restartsmart,
        "success": True  # ⭐ 추가 (정상 완료)
    }


async def checkSmartAPI_active():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{os_spec.restip}:5000/api/alive",
                timeout=1.0
            )
            return response.status_code == 200
    except:
        return False

@router.get('/restartasset')  # save setup.json
async def restartasset():
    # redis_state.client.select(0)
    if redis_state.client.hexists("Service","setting"):
        checkflag = redis_state.client.hget("Service","setting")
        if int(checkflag) == 1:
            return {"status": "0","success": False, "error": "Modbus setting is activated"}
    try:
        # redis_state.client.hset("Service","save",1)
        # redis_state.client.hset("Service", "restart", 1)
        if is_service_active("smartsystemsrestapiservice"):
            async with httpx.AsyncClient(timeout=setting_timeout) as client:
                response = await client.get(f"http://{os_spec.restip}:5000/api/isServiceRestartNeeded")
                data = response.json()
                # if response.status_code in [400, 401, 500]:
                #     flag = await checkLoginAPI(request)
                #     if not flag:
                #         return {"success": False, "error": "Restful API Login Failed"}
                #     else:
                #         response = await client.get(f"http://{os_spec.restip}:5000/api/isServiceRestartNeeded")
                #         data = response.json()
            if data['ServiceRestartRequired']:
                return {"status": "1", "success": True}
            else:
                return {"status": "1", "success": False}
        else:
            return {"status": "0", "success": False, "error": "RestfulAPI Service is not running"}
    except Exception as e:
        print("Error:", e)
        return {"status": "0", "success": False, "error": "Redis Error"}

# @router.get('/restartdevice')
# def restartdevice():
#     redis_state.client.select(0)
#     if redis_state.client.hexists("Service", "setting"):
#         checkflag = redis_state.client.hget("Service", "setting")
#         if int(checkflag) == 1:
#             return {"success": False, "error": "Modbus setting is activated"}
#     try:
#         redis_state.client.hset("Service", "save", 1)
#         redis_state.client.hset("Service", "restart", 1)
#         return {"success": True}
#     except Exception as e:
#         return {"success": False, "error": "Redis Error"}

@router.get('/restartdevice')
async def restartdevice(timeout: int = 30):
    # redis_state.client.select(0)

    if redis_state.client.hexists("Service", "setting"):
        checkflag = redis_state.client.hget("Service", "setting")
        if int(checkflag) == 1:
            return {"success": False, "error": "Modbus setting is activated"}

    if redis_state.client.hexists("Equipment", "applyStatus"):
        applyst = redis_state.client.hget("Equipment", "applyStatus")
        applycontext = json.loads(applyst)
        applycontext["restartFW"] = True
        redis_state.client.hset("Equipment", "applyStatus", json.dumps(applycontext))
    else:
        applycontext = { "restartFW":True, "commisionAsset":{}}
        redis_state.client.hset("Equipment", "applyStatus", json.dumps(applycontext))
    try:
        redis_state.client.hset("Service", "save", 1)
        redis_state.client.hset("Service", "restart", 1)

        # save = 0 될 때까지 대기
        for _ in range(timeout * 10):  # 0.1초 간격
            await asyncio.sleep(0.1)

            save_flag = redis_state.client.hget("Service", "save")
            if save_flag is not None and int(save_flag) == 0:
                return {"success": True, "message": "Restart completed"}

        return {"success": False, "error": f"Timeout ({timeout}s) - save flag not cleared"}

    except Exception as e:
        return {"success": False, "error": f"Redis Error: {str(e)}"}

@router.get('/restartCore')
def restart_core():
    # redis_state.client.select(0)
    if redis_state.client.hexists("Service", "setting"):
        checkflag = redis_state.client.hget("Service", "setting")
        if int(checkflag) == 1:
            return {"success": False, "error": "Modbus setting is activated"}
    try:
        redis_state.client.hset("Service", "restart", 1)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": "Redis Error"}

@router.post('/restoreSetting') #restore setup.json
def restore_setting():
    if redis_state.client.hexists("Service","setting"):
        checkflag = redis_state.client.hget("Service","setting")
        if int(checkflag) == 1:
            return {"status": "0", "error": "Modbus setting is activated"}

    setting_file = os.path.join(SETTING_FOLDER, 'setup.json')
    backup_file = os.path.join(SETTING_FOLDER, 'setup_backup.json')

    # 백업 파일이 존재하는지 확인
    if not os.path.exists(backup_file):
        return JSONResponse(status_code=400, content={"passOK": "0", "error": "setting_backup.json not found"})

    try:
        # 백업 파일을 setup.json으로 덮어쓰기
        shutil.copy(backup_file, setting_file)
        with open(backup_file, "r", encoding="utf-8") as f:
            setting = json.load(f)
        # redis_state.client.execute_command("SELECT", 0)
        redis_state.client.hset("System", "setup", json.dumps(setting))
        redis_state.client.hset("Service", "save", 1)
        redis_state.client.hset("Service", "restart", 1)
        return {"passOK": "1", "message": "Restore successful"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"passOK": "0", "error": f"Error occurred while restoring: {str(e)}"})


def get_Bearing(filename):
    _, ext = os.path.splitext(filename)

    if ext.lower() != ".csv":
        return json.loads(filename)
    else:
        parsed_result = []
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 문자열 → float 변환 (Name은 그대로)
                for key in row:
                    if key != "Name":
                        row[key] = float(row[key])
                parsed_result.append(row)
        return parsed_result

@router.get("/getAssetConfig/{asset}")  #Setting Vue : get Asset info
async def get_assetconfig(asset, request:Request):
    # response = await  http_state.client.get(f"/getNameplate?name="+asset)
    # data = response.json()
    async with httpx.AsyncClient(timeout=setting_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getNameplate?name="+asset)
        data = response.json()
    #     if response.status_code in [400, 401, 500]:
    #         flag = await checkLoginAPI(request)
    #         if not flag:
    #             return {"success": False, "error": "Restful API Login Failed"}
    #         else:
    #             response = await client.get(f"http://{os_spec.restip}:5000/api/getNameplate?name={asset}")
    #             data = response.json()
    #     superlist = set_structNameplate(data)
    if len(data) > 0:
        return {"success": True, "data": data}
    else:
        return {"success": False, "error": "No Data"}


@router.post("/checkAssetConfig/{asset}")
async def check_assetconfig(asset: str, request: Request):
    data = await request.json()
    if not data:
        return {"status": "0", "error": "No data provided"}

    try:
        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.post(
                f"http://{os_spec.restip}:5000/api/checkNameplate?name={asset}",
                json=data
            )
            result = response.json()

        # ✅ 응답 체크
        if 'resetRequired' in result:
            return {"status": "1", "success": True, "result": result['resetRequired']}
        else:
            return {"status": "1","success": False, "error": "resetRequired field not found in response"}

    except Exception as e:
        logging.error(str(e))
        return {"status": "0","success": False, "error": str(e)}

# @router.post("/checkAssetConfig/{asset}")
# async def check_assetconfig(asset:str, request:Request):
#     data = await request.json()
#     if not data:
#         return {"status": "0", "error": "No data provided"}
#     try:
#         # response = await  http_state.client.post(f"/checkNameplate?name={asset}", json=data)
#         # result = response.json()
#         async with httpx.AsyncClient(timeout=setting_timeout) as client:
#             response = await client.post(f"http://{os_spec.restip}:5000/api/checkNameplate?name={asset}", json=data)
#             result = response.json()
#         #     if 'status' in result and result['status'] == 500:
#         #         flag = await checkLoginAPI(request)
#         #         if not flag:
#         #             return {"success": False, "error": "Restful API Login Failed"}
#         #         else:
#         #             response = await client.post(f"http://{os_spec.restip}:5000/api/setNameplate?name={asset}", json=data)
#         #             result = response.json()
#     except Exception as e:
#         print("Error:", e)
#         return {"status": "0", "error": str(e)}
#
#     if 'resetRequired' in result:
#         return {"success":True, "result":result['resetRequired']}
#     else:
#         return {"success": False, "error": "No Data"}
    # if len(result) > 0:
    #     return {"success":True, "result":result['resetRequired']}
    # else:
    #     return {"success": False, "error": "No Data"}

@router.post("/setAssetConfig/{asset}")
async def set_assetconfig(asset:str, request:Request):
    data = await request.json()
    if not data:
        return {"status":"1", "success": False, "error": ["No data provided"]}
    try:
        # response = await  http_state.client.post(f"/setNameplate?name={asset}", json=data)
        # result = response.json()
        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.post(f"http://{os_spec.restip}:5000/api/setNameplate?name={asset}", json=data)
            result = response.json()
        #     if 'status' in result and result['status'] == 500:
        #         flag = await checkLoginAPI(request)
        #         if not flag:
        #             return {"success": False, "error": "Restful API Login Failed"}
        #         else:
        #             response = await client.post(f"http://{os_spec.restip}:5000/api/setNameplate?name={asset}", json=data)
        #             result = response.json()
    except Exception as e:
        print("Error:", e)
        return {"status": "0", "error": [str(e)]}

    if result:
        if result["Status"] == 0:
            return {"status":"1","success": True}
        else:
            return {"status":"1","success": False, "error": result["Messages"]}
    else:
        return {"status":"1","success": False, "error": ["Save failed in setNameplate API"]}

@router.get("/getAssetParams/{asset}")  #Setting Vue : get Asset info
async def get_assetParams(asset, request:Request):
    # response = await  http_state.client.get(f"/getParameters?name="+asset)
    # data = response.json()
    async with httpx.AsyncClient(timeout=setting_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getParameters?name="+asset)
        data = response.json()
    #     if response.status_code in [400, 401, 500]:
    #         flag = await checkLoginAPI(request)
    #         if not flag:
    #             return {"success": False, "error": "Restful API Login Failed"}
    #         else:
    #             response = await client.get(f"http://{os_spec.restip}:5000/api/getParameters?name={asset}")
    #             data = response.json()
    if len(data) > 0:
        return {"success": True, "data": data }
    else:
        return {"success": False, "error": "No Data"}

@router.post("/setAssetParams/{asset}")
async def set_assetParams(asset:str, request:Request):
    data = await request.json()
    if not data:
        return {"status":"1","success": False, "error": ["No data provided"]}
    try:
        # response = await  http_state.client.post(f"/setParameters?name={asset}", json=data)
        # result = response.json()
        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.post(f"http://{os_spec.restip}:5000/api/setParameters?name={asset}", json=data)
            result = response.json()
        #     if 'status' in result and result['status'] == 500:
        #         flag = await checkLoginAPI(request)
        #         if not flag:
        #             return {"success": False, "error": "Restful API Login Failed"}
        #         else:
        #             response = await client.post(f"http://{os_spec.restip}:5000/api/setParameters?name={asset}", json=data)
        #             result = response.json()
    except Exception as e:
        print("Error:", e)
        return {"status":"0", "success": False, "error": [str(e)]}

    if result:
        if result["Status"] == 0:
            return {"status":"1", "success": True}
        else:
            return {"status":"1", "success": False, "error": result["Messages"]}
    else:
        return {"status":"1", "success": False, "error": ["Save failed in setParameters API"]}

@router.get("/test/{channel}/{asset}") 
async def test_asset(channel, asset):
    test_timeout = httpx.Timeout(
        connect=2.0,  # 연결에는 5초
        read=60.0,  # 응답 읽기는 2초
        write=2.0,  # 요청 전송은 5초
        pool=5.0  # 연결 풀은 5초
    )

    try:
        async with httpx.AsyncClient(timeout=test_timeout) as client:
            response = await client.get(f"http://{os_spec.restip}:5000/api/getComm?name={asset}")
            data = response.json()

        result = dict()
        result["AssetName"] = data["AssetName"]
        result["SerialNumber"] = data["SerialNumber"]
        result["Channel"] = data["Channel"]
        result["Commissions"] = data["Commissions"]

        # if redis_state.client.hexists("Equipment","applyStatus"):
        #     applyst = redis_state.client.hget("Equipment","applyStatus")
        #     applycontext = json.loads(applyst)
        #     if applycontext["commisionAsset"][channel]["Name"] == asset:
        #         if len(result["Commissions"]) > 0:
        #             applycontext["commisionAsset"][channel]["result"] = False
        #         else:
        #             applycontext["commisionAsset"][channel]["result"] = True

        #     redis_state.client.hset("Equipment", "applyStatus", json.dumps(applycontext))

        if len(data) > 0:
            return {"success": True, "data": result}
        else:
            return {"success": False, "error": "No Data"}
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")
        return {"success": False, "error": "No Data"}

@router.get("/testwave/{asset}")
async def test_wave(asset, request:Request):
    try:
        # HTTP 클라이언트 상태 확인
        # if http_state.error:
        #     return {"success": False, "error": http_state.error}
        #
        # # 클라이언트 가져오기
        # client = http_state.client
        # if not client:
        #     return {"success": False, "error": "HTTP client not initialized"}
        #
        # response = await http_state.client.get(f"/getWaveform?name={asset}")
        # data = response.json()
        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.get(f"http://{os_spec.restip}:5000/api/getWaveform?name={asset}")
            data = response.json()

        if len(data) > 0:
            waveTDict = dict()
            waveTDict["SR"] = data["SR"]
            waveTDict["Duration"] = data["Duration"]
            waveTDict["Vwave"] = data["Vwave"]
            waveTDict["Iwave"] = data["Iwave"]
            waveTDict["Vfft"] = data["Vfft"]
            waveTDict["Ifft"] = data["Ifft"]
            return {"success": True, "waveT": waveTDict}
        else:
            return {"success": False, "error": "No Data"}
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")
        return {"success": False, "error": "No Data"}

def service_exists(name):
    """서비스 파일이 존재하는지 확인"""
    try:
        result = subprocess.run(
            ['systemctl', 'list-unit-files', name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2
        )
        return name in result.stdout
    except:
        return False

def is_service_enabled(name):
    """서비스 부팅 시 자동 시작 여부 확인 (enabled/disabled)"""
    try:
        result = subprocess.run(['systemctl', 'is-enabled', name],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                timeout=2)
        return result.stdout.strip() == "enabled"
    except Exception as e:
        print(f"❌ 서비스 enabled 상태 확인 실패: {name} - {e}")
        return False


@router.get("/checkSmartStatus")
async def check_SmartStatus():
    try:
        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.get(f"http://{os_spec.restip}:5000/api/status")
            data = response.json()

            return {"success": True, "data":data}
        # data = {
        #     "State": "Stop",
        #     "Message": "Smart Systems RestAPI Service is successfully initialized and running",
        #     "ServiceStartTime": "2025-11-13T03:22:48.2809239+09:00",
        #     "RunTimeErrors": ["Corrupted smart systems files.","No asset defined in smart system."]
        # }
        # return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "msg":str(e)}

def is_same_version(current: str, new: str) -> bool:
    """두 버전이 같은지"""
    return tuple(map(int, new.split('.'))) == tuple(map(int, current.split('.')))

async def check_SmartVersion():
    try:
        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.get(f"http://{os_spec.restip}:5000/api/version")
            data = response.json()
            # short_version = '.'.join(data["Version"].split('.')[:3])
            return {"success": True, "Version":data["Version"]}

    except Exception as e:
        return {"success": False, "Version": "1.0.3"}

def check_a35version():
    # redis_state.client.select(0)
    if not redis_state.client.exists("version"):
        return None
    fw = redis_state.client.hget("version","fw")
    a35 = redis_state.client.hget("version","a35")

    return {"fw":fw , "A35":a35}

@router.post('/uploadCerts')
def upload_certs(files: List[UploadFile] = File(...)):
    """AWS IoT Core 인증서 파일들 업로드 (복수)"""
    if not files:
        return {'passOK': 0, 'error': 'No files provided'}

    allowed_extensions = {'.pem', '.crt', '.key', '.cert'}
    save_path = os.path.join(SETTING_FOLDER, "certs")
    os.makedirs(save_path, exist_ok=True)

    uploaded = []
    errors = []

    for file in files:
        if file.filename == '':
            continue

        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            errors.append({'filename': file.filename, 'error': 'Invalid file type'})
            continue

        try:
            file_path = os.path.join(save_path, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            os.chmod(file_path, 0o600)
            uploaded.append(file.filename)

        except Exception as e:
            errors.append({'filename': file.filename, 'error': str(e)})

    return {
        'passOK': 1 if uploaded else 0,
        'uploaded': uploaded,
        'errors': errors
    }


@router.get('/listCerts')
def list_certs():
    """저장된 인증서 파일 목록"""
    cert_path = os.path.join(SETTING_FOLDER, "certs")

    if not os.path.exists(cert_path):
        return {'passOK': 1, 'files': []}

    files = []
    for f in os.listdir(cert_path):
        file_path = os.path.join(cert_path, f)
        if os.path.isfile(file_path):
            files.append({
                'filename': f,
                'size': os.path.getsize(file_path),
                'modified': os.path.getmtime(file_path)
            })

    return {'passOK': 1, 'files': files}

@router.delete('/deleteCert/{filename}')
def delete_cert(filename: str):
    """인증서 파일 삭제"""
    # 경로 조작 방지
    if '..' in filename or '/' in filename:
        return {'passOK': 0, 'error': 'Invalid filename'}

    file_path = os.path.join(SETTING_FOLDER, "certs", filename)

    if not os.path.exists(file_path):
        return {'passOK': 0, 'error': 'File not found'}

    try:
        os.remove(file_path)
        return {'passOK': 1, 'filename': filename}
    except Exception as e:
        return {'passOK': 0, 'error': str(e)}

@router.get("/checkMQTT")
def check_mqtt():
    if redis_state.client.hexists("System", "setup"):
        setup = json.loads(redis_state.client.hget("System", "setup"))
    else:
        file_path = os.path.join(SETTING_FOLDER, 'setup.json')
        if not os.path.exists(file_path):
            return {"passOK": 0, "error": "setting file not found"}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                setup = json.load(f)
        except Exception as e:
            return {"passOK": 0}

    ret = {}
    if setup:
        if "MQTT" in setup["General"]:
            if int(setup["General"]["MQTT"]["Use"]) == 1:
                if service_exists("mqClient"):
                    if is_service_enabled("mqClient"):
                        if not is_service_active("mqClient"):
                            ret["start"] = execService("start","mqClient",0.3)
                    else:
                        ret["enable"] = execService("enable", "mqClient",0.5)
                        ret["start"] = execService("start", "mqClient")
                else:
                    ret["service"] = create_service_file("mqClient","MQTT Client","/home/root/mqClient/mqtt_client","/home/root/mqClient")
                    ret["reload"] = execService("daemon-reload", None, 0.5)  # 이거 추가!
                    ret["enable"] = execService("enable", "mqClient",0.5)
                    ret["start"] = execService("start", "mqClient",0.3)
            else:
                if service_exists("mqClient"):
                    if is_service_enabled("mqClient"):
                        if is_service_active("mqClient"):
                            ret["stop"] = execService("stop", "mqClient",0)
                        ret["disable"] = execService("disable", "mqClient",0)
    return {"passOK":1, "result": ret}

def create_service_file(
        service_name: str,
        description: str,
        exec_start: str,
        working_directory: str,
        user: str = "root",
        after: str = "network.target",
        restart: str = "always",
        wanted_by: str = "multi-user.target"
) -> bool:
    """systemd 서비스 파일 내용을 생성합니다."""

    service_content = f"""[Unit]
Description={description}
After={after}

[Service]
ExecStart={exec_start}
WorkingDirectory={working_directory}
Restart={restart}
User={user}

[Install]
WantedBy={wanted_by}
"""
    filename = f"/etc/systemd/system/{service_name}.service"
    try:
        with open(filename, 'w') as f:
            f.write(service_content)
        return True
    except Exception as e:
        print(str(e))
        return False

def execService(cmd: str, item: str = None, wait_after: float = 0) -> dict:
    """
    systemctl 명령 실행

    Args:
        cmd: systemctl 명령 (start, stop, enable, disable, daemon-reload 등)
        item: 서비스 이름 (daemon-reload의 경우 None)
        wait_after: 명령 실행 후 대기 시간(초)
    """
    try:
        if cmd == "daemon-reload":
            command = ['sudo', 'systemctl', 'daemon-reload']
        else:
            if not item:
                return {
                    'success': False,
                    'error': f'Service name required for {cmd}',
                    'action': cmd
                }
            command = ['sudo', 'systemctl', cmd, item]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )

        # 성공 시 대기
        if result.returncode == 0 and wait_after > 0:
            time.sleep(wait_after)

        return {
            'success': result.returncode == 0,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'returncode': result.returncode,
            'service': item,
            'action': cmd
        }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': f'Timeout expired while {cmd}ing {item or "daemon"}',
            'service': item,
            'action': cmd
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'service': item,
            'action': cmd
        }

@router.get("/SysCheck")
async def check_sysStatus():
    data = {}

    if os_spec.os == 'Windows':
        if not redis_state.client is None:
            # redis_state.client.execute_command("SELECT", 0)
            if redis_state.client.hexists("System", "Status"):
                data = json.loads(redis_state.client.hget("System", "Status"))
        data["core"] = 0

        usage = psutil.disk_usage('/')
        disk1 = {
            "drive": "/",
            "totalGB": round(usage.total / (1024 ** 3), 2),
            "freeGB": round(usage.free / (1024 ** 3), 2),
            "status": "ok" if usage.percent < 90 else "warning"
        }

        return {"success": True, "data": data, "disk": [disk1]}
    else:
        version_dict = getVersions()
        key_map = {
            'fw': 'fw',
            'a35': 'A35',
            'web': 'WebServer',
            'core': 'Core',
            'smartsystem': 'SmartSystems'
        }
        versionDict = {}
        if version_dict:
            for src_key, dst_key in key_map.items():
                versionDict[dst_key] = version_dict[src_key]

        apiResult = await check_SmartVersion()

        if apiResult:
            versionDict['SmartSystems'] = apiResult['Version']

        a35Dict = check_a35version()
        if not a35Dict is None:
            versionDict['fw'] = a35Dict['fw']
            versionDict['A35'] = a35Dict['A35']

        servicedict = {
            'smartsystem' : 'smartsystemsservice',
            'smartapi': 'smartsystemsrestapiservice',
            'redis': 'redis',
            'influxdb': 'influxdb',
            'core': 'core',
            'webserver':'webserver',
            'a35':'sv500A35'
        }
        service_status = {}

        # 각 서비스의 상태 확인
        for key, service_name in servicedict.items():
            service_status[key] = is_service_active(service_name)

        usage = psutil.disk_usage('/')
        disk1 = {
            "drive": "/",
            "totalGB": round(usage.total / (1024 ** 3), 2),
            "freeGB": round(usage.free / (1024 ** 3), 2),
            "status": "ok" if usage.percent < 90 else "warning"
        }

        usage = psutil.disk_usage('/usr/local')
        disk2 = {
            "drive": "/usr/local",
            "totalGB": round(usage.total / (1024 ** 3), 2),
            "freeGB": round(usage.free / (1024 ** 3), 2),
            "status": "ok" if usage.percent < 90 else "warning"
        }

        return {"success": True, "data":service_status,  "disk":[disk1, disk2], "versions":versionDict}

@router.get('/SysService/{cmd}/{item}')
def control_service(cmd, item):
    return sysService(cmd, item)

@router.get('/ServiceStatus')
def check_allservice():
    # redis_state.client.select(0)
    devMode = redis_state.client.hget("System", "mode")

    if devMode == 'device0':
        servicedict = {
            'redis': 'redis',
            'influxdb': 'influxdb',
            'core': 'core',
            'webserver': 'webserver',
            'a35':'a35'
        }
    else:
        servicedict = {
            'smartsystem': 'smartsystemsservice',
            'smartapi': 'smartsystemsrestapiservice',
            'redis': 'redis',
            'influxdb': 'influxdb',
            'core': 'core',
            'webserver': 'webserver',
            'a35':'a35',
        }

    service_status = {}

    # 각 서비스의 상태 확인
    for key, service_name in servicedict.items():
        service_status[key] = is_service_active(service_name)

    # 상태 확인
    abnormal = False
    for key, value in service_status.items():
        if not value:  # 서비스가 죽어있으면 비정상
            abnormal = True
            break

    status_list = get_system_status()

    resultDict = {}
    if abnormal:
        resultDict["service"] = False
        resultDict["serviceDict"] = service_status
    else:
        resultDict["service"] = True

    if len(status_list) > 0:
        resultDict["data"] = status_list
        resultDict["system"] = False
    else:
        resultDict["system"] = True

    return resultDict


def get_system_status():
    """시스템 상태 조회"""
    # CPU 사용률 (1초간 측정)
    cpu_percent = psutil.cpu_percent(interval=1)

    # 메모리 사용률
    memory = psutil.virtual_memory()
    memory_percent = memory.percent

    # 루트 디렉토리(/) 사용률
    disk = psutil.disk_usage('/')
    disk_percent = round((disk.used / disk.total) * 100, 1)

    highList = []
    if memory_percent > 90:
        highList.append('MEMORY')
    if cpu_percent > 90:
        highList.append('CPU')
    if disk_percent > 80:
        highList.append('DISK')

    return highList

@router.post("/command")
async def push_command_left(command: Command, request:Request):
    """새로운 command를 Redis 리스트의 왼쪽에 추가"""
    if command.cmd != 2:
        saveLog(command.get_item_name(), request)
    try:
        binary_data = command_to_binary(command)
        # redis_state.client_db1.select(1)
        redis_state.client_db1.lpush('command', binary_data)

        return {
            "success": True,
            "message": "Command pushed to left of list",
            "data": command.dict()
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


async def wait_for_file(watch_paths: list, timeout: int = 30) -> dict:
    """파일 생성 대기 (IN_CLOSE_WRITE 이벤트 감시)"""
    result = {path: None for path in watch_paths}
    paths_completed = set()
    event = threading.Event()

    wm = pyinotify.WatchManager()


    class Handler(pyinotify.ProcessEvent):
        def process_IN_CLOSE_WRITE(self, event_data):
            print(f"[DEBUG] 파일 쓰기 완료: {event_data.pathname}")
            if event_data.pathname.endswith('.json'):
                # 어느 감시 경로에서 생성됐는지 찾기
                for path in watch_paths:
                    if event_data.pathname.startswith(path):  # 경로 포함 여부로 체크
                        result[path] = event_data.pathname
                        paths_completed.add(path)
                        print(f"[DEBUG] 매칭 성공! ({len(paths_completed)}/{len(watch_paths)})")
                        if len(paths_completed) == len(watch_paths):
                            event.set()
                        break

    notifier = pyinotify.ThreadedNotifier(wm, Handler())

    for path in watch_paths:
        wm.add_watch(path, pyinotify.IN_CLOSE_WRITE)

    notifier.start()

    try:
        for _ in range(timeout * 10):
            if event.is_set():
                return {"success": True, "files": result}
            await asyncio.sleep(0.1)

        return {"success": False, "message": f"타임아웃 ({timeout}초)", "files": result}
    finally:
        notifier.stop()

@router.get("/HarmTrigger/{channel}")
async def set_harmTrigger(channel, request:Request, cmd: int = CmdType.CMD_CAPTURE, item: int = ItemType.ITEM_WAVEFORM):
    try:
        if channel == 'Main' or channel == 'main':
            chtype = 0
        else:
            chtype = 1
        await push_command_left(Command(type=chtype, cmd=cmd, item=item), request)
        redis_state.client_db1.hset("waveRequest",channel,1)
        return {"success": True}

    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/trigger")
async def trigger_waveform(
        request: Request,
        cmd: int = CmdType.CMD_CAPTURE,
        item: int = ItemType.ITEM_WAVEFORM,
        target: int = 2,
        timeout: int = 90
):
    """웨이브폼 트리거 및 파일 생성 대기"""
    try:
        # 1. 감시 경로 결정
        if target == 2:
            watch_paths = [WAVEFORM_PATHS[0], WAVEFORM_PATHS[1]]
        else:
            watch_paths = [WAVEFORM_PATHS[target]]

        # 2. 기존 파일 삭제
        for path in watch_paths:
            if os.path.exists(path):
                for filename in os.listdir(path):
                    file_path = os.path.join(path, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            print(f"[DEBUG] 기존 파일 삭제: {file_path}")
                    except Exception as e:
                        print(f"[WARNING] 파일 삭제 실패 {file_path}: {e}")

        # 3. 감시 상태 초기화
        result = {path: None for path in watch_paths}
        paths_created = {}  # 생성 감지된 파일들
        paths_completed = set()  # 완료 감지된 경로들
        event = threading.Event()
        wm = pyinotify.WatchManager()

        class Handler(pyinotify.ProcessEvent):
            def process_IN_CREATE(self, event_data):
                """파일 생성 시작 감지"""
                if event_data.pathname.endswith('.json') or event_data.pathname.endswith('.bin'):
                    print(f"[DEBUG] 파일 생성 시작: {event_data.pathname}")
                    for path in watch_paths:
                        if event_data.pathname.startswith(path):
                            paths_created[path] = event_data.pathname
                            print(f"[DEBUG] 생성 감지 ({len(paths_created)}/{len(watch_paths)})")
                            break

            def process_IN_CLOSE_WRITE(self, event_data):
                """파일 쓰기 완료 감지"""
                if event_data.pathname.endswith('.json') or event_data.pathname.endswith('.bin'):
                    print(f"[DEBUG] 파일 쓰기 완료: {event_data.pathname}")
                    for path in watch_paths:
                        if event_data.pathname.startswith(path):
                            result[path] = event_data.pathname
                            paths_completed.add(path)
                            print(f"[DEBUG] 완료 감지 ({len(paths_completed)}/{len(watch_paths)})")

                            if len(paths_completed) == len(watch_paths):
                                print(f"[DEBUG] 모든 파일 완료!")
                                event.set()
                            break

        notifier = pyinotify.ThreadedNotifier(wm, Handler())
        for path in watch_paths:
            wm.add_watch(path, pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE)

        notifier.start()

        try:
            # 4. 트리거 전송
            if target in [0, 2]:
                await push_command_left(Command(type=0, cmd=cmd, item=item), request)
            if target in [1, 2]:
                await push_command_left(Command(type=1, cmd=cmd, item=item), request)

            print(f"[DEBUG] 트리거 전송 완료 (target={target}), 파일 대기 중...")

            # 5. 파일 생성 완료 대기
            for _ in range(timeout * 10):
                if event.is_set():
                    return {
                        "success": True,
                        "message": "정상 완료",
                        "files": result
                    }
                await asyncio.sleep(0.1)

            # 6. 타임아웃 - 생성은 감지했는지 확인
            if len(paths_created) > 0:
                # 생성은 감지했는데 완료를 못 감지 = 다른 프로세스가 가져감
                print(f"[WARNING] 생성 감지했으나 완료 미감지 - 다른 프로세스가 파일 처리한 것으로 추정")
                return {
                    "success": True,
                    "message": "파일 생성 감지 (다른 프로세스가 처리)",
                    "files": paths_created,
                    "assumed_taken": True
                }
            else:
                # 생성조차 감지 못함 = 진짜 타임아웃
                return {
                    "success": False,
                    "message": f"타임아웃 ({timeout}초) - 파일 생성 감지 실패",
                    "files": result
                }

        finally:
            notifier.stop()

    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get('/getMode')
def get_sysMode():
    try:
        # redis_state.client.select(0)
        result = redis_state.client.hget("System","mode")
        return {"success": True, "mode": result}
    except Exception as e:
        print(str(e))
        return {"success": False}


@router.get('/updateSmartSystem/{mode}')
async def update_smartsystem(mode, request: Request):
    if int(mode) == 1:
        c_text = 'Smart System reinstall'
        saveLog("Reinstll SmartSystem", request)
    else:
        c_text = 'Smart System update'
        saveLog("Update SmartSystem", request)
    lastpost = get_lastpost()
    if lastpost["result"] == 1:
        idx = int(lastpost["data"]["id"])
        smartVersion = lastpost["data"]["smart_version"]
        dict = getVersions()
        if smartVersion != dict["smartsystem"]:
            smartVersion = dict["smartsystem"]
        update = Post(title='SW Update', context=c_text, mtype=1, utype='smartsystem',
                      smart_version=smartVersion)
        save_post(update, 1, idx)
    else:
        update = Post(title='SW Install', context='Smart System install', mtype=0, utype='smartsystem',
                      smart_version='1.0.0')
        save_post(update, 0, 0)


    if int(mode) == 1:
        reset_assetInfo('Main','Sub')
        try:
            result = subprocess.run(
                ['sh', '/usr/local/sv500/iss/install.sh', '--fresh'],
                capture_output=True,
                text=True,
                check=True
            )
            service_timeout = 30
            start_time = time.time()

            while time.time() - start_time < service_timeout:
                if check_smart():
                    break
                await asyncio.sleep(1)

            if not check_smart():
                return {"success": False, "message": "Service start timed out"}

            # 2. API 헬스체크 재시도 (최대 60초)
            health_timeout = 60
            start_time = time.time()

            while time.time() - start_time < health_timeout:
                try:
                    async with httpx.AsyncClient(timeout=5) as client:
                        response = await client.get(f"http://{os_spec.restip}:5000/api/alive")
                        if response.status_code == 200:
                            return {"success": True, "message": "Fresh installation is completed"}
                except Exception as e:
                    print(f"Health check retry... {e}")
                await asyncio.sleep(3)  # 3초 간격 재시도

            return {"success": False, "message": "Health check timed out after 60s"}
        except subprocess.CalledProcessError as e:
            return {"success": False, "message": f"Fresh installation is failed: {e.stderr}"}  # 6. 에러 메시지 추가
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Fresh installation is timeout"}

    else:
        try:
            result = subprocess.run(
                ['sh', '/usr/local/sv500/iss/install.sh'],
                capture_output=True,
                text=True,
                check=True
            )
            service_timeout = 30
            start_time = time.time()

            while time.time() - start_time < service_timeout:
                if check_smart():
                    break
                await asyncio.sleep(1)

            if not check_smart():
                return {"success": False, "message": "Service start timed out"}

            # 2. API 헬스체크 재시도 (최대 60초)
            health_timeout = 60
            start_time = time.time()

            while time.time() - start_time < health_timeout:
                try:
                    async with httpx.AsyncClient(timeout=5) as client:
                        response = await client.get(f"http://{os_spec.restip}:5000/api/alive")
                        if response.status_code == 200:
                            return {"success": True, "message": "Update completed"}
                except Exception as e:
                    print(f"Health check retry... {e}")
                await asyncio.sleep(3)  # 3초 간격 재시도

            return {"success": False, "message": "Health check timed out after 60s"}

        except subprocess.CalledProcessError as e:
            return {"success": False, "message": f"Update failed: {e.stderr}"}
        except Exception as e:
            return {"success": False, "message": str(e)}


def reset_assetInfo(channel1, channel2):
    FILE_PATH = os.path.join(SETTING_FOLDER, "setup.json")

    if redis_state.client.hexists("System", "setup"):
        setting = json.loads(redis_state.client.hget("System", "setup"))
    else:
        if not os.path.exists(FILE_PATH):
            return {"success": False, "error": "setting file not found"}
        try:
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                setting = json.load(f)
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 채널별 에셋정보 리셋
    if channel1 != '':
        for ch in setting.get("channel", []):
            if ch.get("channel") == "Main":
                ch["assetInfo"] = {
                    "name": "",
                    "type": "",
                    "nickname": "",
                    "driveType": "DOL"
                }
                break

    if channel2 != '':
        for ch in setting.get("channel", []):
            if ch.get("channel") == "Sub":
                ch["assetInfo"] = {
                    "name": "",
                    "type": "",
                    "nickname": "",
                    "driveType": "DOL"
                }
                break

    # 저장
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(setting, f, indent=2, ensure_ascii=False)

    redis_state.client.hset("System", "setup", json.dumps(setting))


@router.post("/setDefaultIP")
async def set_defaultIP(request:Request):
    try:
        data = await request.json()
        default_file_path = os.path.join(SETTING_FOLDER, 'default.json')

        with open(default_file_path, "r", encoding="utf-8") as f:
            defaults = json.load(f)

        defaults["General"]["tcpip"]["ip_address"] = data["ip"]

        with open(default_file_path, "w", encoding="utf-8") as f:
            json.dump(defaults, f, indent=2)  # indent 추가로 가독성 향상

        saveLog("Default IP Change : " + data["ip"], request)
        return {"success": True}
    except Exception as e:
        return {"success" : False}