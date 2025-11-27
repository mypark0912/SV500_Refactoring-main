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
#from routes.auth import checkLoginAPI
from routes.util import get_mac_address, sysService, is_service_active, getVersions, saveLog, get_lastpost, Post, save_post
from routes.api import parameter_options
from .RedisBinary import Command, CmdType, ItemType

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
        redis_state.client.select(0)
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
        bucket_result = await create_influx_bucket()

        if not bucket_result["success"]:
            redis_state.client.hset("influx_init", "status", "P.FAIL")
            logging.warning(f"⚠️ Bucket creation failed: {bucket_result['message']}")

        # 다운샘플링 설정 (버킷 + Task) 추가
        downsampling_result = await setup_downsampling()
        if not downsampling_result["success"]:
            logging.warning(f"⚠️ Downsampling setup had issues: {downsampling_result['message']}")
        else:
            logging.info("✅ Downsampling buckets and tasks configured")

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


async def create_influx_bucket():
    try:
        config = aesState.getInflux()
        token = aesState.decrypt(config["cipher"])
        bucket_name = "ntek"
        retention_seconds = 365 * 24 * 60 * 60
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
            else:
                error_msg = response.json().get("message", response.text)
                logging.error(f"❌ Bucket '{bucket_name}' creation failed: {error_msg}")
                return {"success": False, "message": error_msg}

    except Exception as e:
        logging.error(f"❌ Bucket creation error: {e}")
        return {"success": False, "message": str(e)}


async def create_downsampling_buckets():
    """다운샘플링용 버킷 생성 (ntek_1h, ntek_1d)"""
    try:
        config = aesState.getInflux()
        token = aesState.decrypt(config["cipher"])

        buckets = [
            {
                "name": "ntek_1h",
                "retention_seconds": 90 * 24 * 60 * 60,  # 90일
                "description": "1시간 평균 데이터"
            },
            {
                "name": "ntek_1d",
                "retention_seconds": 730 * 24 * 60 * 60,  # 2년
                "description": "1일 평균/합계 데이터"
            }
        ]

        results = []

        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            for bucket_info in buckets:
                bucket_data = {
                    "orgID": config['org_id'],
                    "name": bucket_info["name"],
                    "retentionRules": []
                }

                # retention 설정 (0이면 무제한)
                if bucket_info["retention_seconds"] > 0:
                    bucket_data["retentionRules"] = [
                        {
                            "type": "expire",
                            "everySeconds": bucket_info["retention_seconds"]
                        }
                    ]

                response = await client.post(
                    f"http://127.0.0.1:8086/api/v2/buckets",
                    headers={"Authorization": f"Token {token}"},
                    json=bucket_data
                )

                if response.status_code == 201:
                    retention_info = f"{bucket_info['retention_seconds'] // (24 * 60 * 60)} days" if bucket_info[
                                                                                                         'retention_seconds'] > 0 else "infinite"
                    logging.info(f"✅ Bucket '{bucket_info['name']}' created (retention: {retention_info})")
                    results.append({"bucket": bucket_info["name"], "success": True})
                elif response.status_code == 422:
                    # 이미 존재하는 버킷
                    logging.info(f"ℹ️ Bucket '{bucket_info['name']}' already exists")
                    results.append({"bucket": bucket_info["name"], "success": True, "existed": True})
                else:
                    error_msg = response.json().get("message", response.text)
                    logging.error(f"❌ Bucket '{bucket_info['name']}' creation failed: {error_msg}")
                    results.append({"bucket": bucket_info["name"], "success": False, "error": error_msg})

        success_count = sum(1 for r in results if r["success"])
        return {
            "success": success_count > 0,
            "message": f"Created/verified {success_count}/{len(buckets)} buckets",
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


@router.get('/initDB/status')
async def get_init_status():
    redis_state.client.select(0)
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
        redis_state.client.select(0)

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

@router.get('/getSetting')
def get_setting():
    redis_state.client.execute_command("SELECT", 0)
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
        redis_state.client.execute_command("SELECT", 0)
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

# async def reset_asset():
#     try:
#         mainAsset = ''
#         subAsset = ''
#         redis_state.client.select(0)
#         if redis_state.client.hexists("System", "setup"):
#             setupflag = True
#             datStr = redis_state.client.hget("System", "setup")
#             setting = json.loads(datStr)
#             mainAsset = ''
#             subAsset = ''
#             if setting["General"]["useFunction"]["diagnosis_main"]:
#                 for chInfo in setting["channel"]:
#                     if chInfo["channel"] == 'Main':
#                         mainAsset = chInfo["assetInfo"]["name"]
#                         break
#             if setting["General"]["useFunction"]["diagnosis_sub"]:
#                 for chInfo in setting["channel"]:
#                     if chInfo["channel"] == 'Sub':
#                         subAsset = chInfo["assetInfo"]["name"]
#                         break
#             if mainAsset != '':
#                 data = await reset_smart(mainAsset, 0)
#                 if len(data) > 0:
#                     datas = await  reset_smart(mainAsset, 1)
#                     if len(datas) > 0:
#                         resetmain = 0
#                     else:
#                         resetmain = 1
#                 else:
#                     resetmain = 2
#             else:
#                 resetmain = -1
#             if subAsset != '':
#                 data = await reset_smart(subAsset, 0)
#                 if len(data) > 0:
#                     datas = await  reset_smart(subAsset, 1)
#                     if len(datas) > 0:
#                         resetsub = 0
#                     else:
#                         resetsub = 1
#                 else:
#                     resetsub = 2
#             else:
#                 resetsub = -1
#         else:
#             setupflag = False
#
#         if not setupflag:
#             return {"success": False, "msg": 'setup is not exist'}
#         else:
#             if resetmain > 1 or resetsub > 1:
#                 return {"success": False, "msg": "Unregistering asset is failed"}
#             else:
#                 return {"success": True, "main":{"status":resetmain, "asset":mainAsset}, "sub":{"status":resetsub, "asset":subAsset}}
#     except Exception as e:
#         print(str(e))
#         return {"success": False, "msg": str(e)}

async def reset_count(request:Request):
    redis_state.client.select(0)
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
        install_script = "/home/root/iss/install.sh"  # 예시

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
        redis_state.client.execute_command("SELECT", 0)
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
    # response = await  http_state.client.get(f"/getSettings")
    # data = response.json()
    async with httpx.AsyncClient(timeout=setting_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getSettings")
        data = response.json()
    #     if response.status_code in [400, 401, 500]:
    #         flag = await checkLoginAPI(request)
    #         if not flag:
    #             return {"success": False, "error": "Restful API Login Failed"}
    #         else:
    #             response = await client.get(f"http://{os_spec.restip}:5000/api/getSettings")
    #             data = response.json()
    if data:
        # print(data)
        return {"success": True, "data": data}
    else:
        return {"success": False, "error": "No Data"}

@router.get('/getDiagnosisProfile')
async def get_diagnosisprofile(request:Request):
    # response = await  http_state.client.get(f"/getProfile")
    # data = response.json()
    async with httpx.AsyncClient(timeout=setting_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getProfile")
        data = response.json()
    #     if response.status_code in [400, 401, 500]:
    #         flag = await checkLoginAPI(request)
    #         if not flag:
    #             return {"success": False, "error": "Restful API Login Failed"}
    #         else:
    #             response = await client.get(f"http://{os_spec.restip}:5000/api/getProfile")
    #             data = response.json()
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
        # response = await  http_state.client.post(f"/setSettings", json=data)
        # data = response.json()
        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.post(f"http://{os_spec.restip}:5000/api/setSettings", json=data)
            data = response.json()
        #     if response.status_code in [400, 401, 500]:
        #         flag = await checkLoginAPI(request)
        #         if not flag:
        #             return {"success": False, "error": "Restful API Login Failed"}
        #         else:
        #             response = await client.post(f"http://{os_spec.restip}:5000/api/setSettings", json=data)
        #             data = response.json()
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
        # response = await  http_state.client.post(f"/setProfile", json=data)
        # data = response.json()
        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.post(f"http://{os_spec.restip}:5000/api/setProfile", json=data)
            data = response.json()
        #     if response.status_code in [400, 401, 500]:
        #         flag = await checkLoginAPI(request)
        #         if not flag:
        #             return {"success": False, "error": "Restful API Login Failed"}
        #         else:
        #             response = await client.post(f"http://{os_spec.restip}:5000/api/setProfile",json=data)
        #             data = response.json()
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
    # response = await  http_state.client.get(f"/getAssetTypes")
    # data = response.json()
    async with httpx.AsyncClient(timeout=setting_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getAssetTypes")
        data = response.json()
    #     if response.status_code in [400, 401, 500]:
    #         flag = await checkLoginAPI(request)
    #         if not flag:
    #             return {"success": False, "error": "Restful API Login Failed"}
    #         else:
    #             response = await client.get(f"http://{os_spec.restip}:5000/api/getAssetTypes")
    #             data = response.json()
    if data:
        return {"success": True, "data": data}
    else:
        return {"success": False, "error": "No Data"}

@router.get('/getAssetList')
async def get_assetlist(request: Request):
    # response = await  http_state.client.get(f"/getAssetHierarchy")
    # datas = response.json()
    async with httpx.AsyncClient(timeout=setting_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/getAssetHierarchy")
        datas = response.json()
    #     if response.status_code in [400, 401, 500]:
    #         flag = await checkLoginAPI(request)
    #         if not flag:
    #             return {"success": False, "error": "Restful API Login Failed"}
    #         else:
    #             response = await client.get(f"http://{os_spec.restip}:5000/api/getAssetHierarchy")
    #             datas = response.json()
    

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
        redis_state.client.execute_command("SELECT", 0)
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

    if len(datas) > 0:
        if assetName in datas:
            return {"status": "1"}
        else:
            return {"status": "0", "error": "Create Failed"} #성공해도 리스트에는 추가안된상태로 리턴되서 여기로빠짐
    else:
        return {"status": "0", "error": "Create Failed"}

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

    if len(datas) > 0:     
        if newName in datas:
            return {"status": "1"}
        else:
            return {"status": "0", "error": "Modify Failed"}
    else:
        return {"status": "0", "error": "Modify Failed"}

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

    if len(datas) > 0:
        if not asset in datas:
            return {"status": "1"}
        else:
            return {"status": "0", "error": "Delete Failed"}
    else:
        return {"status": "1"}

@router.get('/unregisterAsset/{channel}/{asset}')
async def unreg_Asset(channel, asset):
    # async with httpx.AsyncClient(timeout=setting_timeout) as client:
    #     response = await client.get(f"http://{os_spec.restip}:5000/api/unregisterAsset?name={asset}")
    #     data = response.json()
    data = await reset_smart(asset, 0)
    if isinstance(data, list) and len(data) > 0:
        finflag = True
    else:
        finflag = False
    redis_state.client.execute_command("SELECT", 0)
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


# @router.get('/registerAsset/{channel}/{assetName}/{assetType}')  # Different response format (Fail, Success, Not Exist)
# async def reg_Asset(channel, assetName, assetType):
#     async with httpx.AsyncClient(timeout=setting_timeout) as client:
#         response = await client.get(f"http://{os_spec.restip}:5000/api/registerAsset?name={assetName}")
#         data = response.json()
#         if isinstance(data, dict):
#             status = data.get("Status")
#         elif isinstance(data, list):
#             status = 2
#
#     if status == 0:
#         finflag = True
#     else:
#         finflag = False
#
#     if finflag:
#         redis_state.client.execute_command("SELECT", 0)
#         if redis_state.client.hexists("System", "setup"):
#             datStr = redis_state.client.hget("System", "setup")
#             setting = json.loads(datStr)
#             for chInfo in setting["channel"]:
#                 if channel == chInfo["channel"]:
#                     chInfo["assetInfo"]["name"] = assetName
#                     chInfo["assetInfo"]["type"] = assetType
#                     break
#             redis_state.client.hset("System", "setup", json.dumps(setting))
#         return {"success": True}
#     else:
#         if status == 1:
#             return {"success": False, "error": data["Messages"]}
#         else:
#             return {"success": False, "error": ['Asset is registered already']}

@router.get('/registerAsset/{channel}/{assetName}/{assetType}')
async def reg_Asset(channel, assetName, assetType):
    async with httpx.AsyncClient(timeout=setting_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/registerAsset?name={assetName}")
        data = response.json()
    if isinstance(data, list) and len(data) > 0:
        finflag = True
    else:
        finflag = False
    redis_state.client.execute_command("SELECT", 0)
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
    if finflag:
        return {"success":True}
    else:
        return {"success":False}


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



def initialize_alarm_configs(channel, alams):
    rediskey = f"alarm_status:{channel}"
    alarmdict = {}
    for j in range(1, 33):
        if alams[str(j)][0] != 0:
            alarmdict[str(j)] = alams[str(j)]
    if len(alarmdict.keys()) > 0:
        redis_state.client.execute_command("SELECT", 1)
        redis_state.client.delete(rediskey)
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
            redis_state.client.hset(rediskey, key, json.dumps(init_data))

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
    redis_state.client.execute_command("SELECT", 0)
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

        redis_state.client.select(0)
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
            max_attempts = 10  # 최대 15초 (30 * 0.5초)
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
    redis_state.client.select(0)
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

@router.get('/restartdevice')
def restartdevice():
    redis_state.client.select(0)
    if redis_state.client.hexists("Service", "setting"):
        checkflag = redis_state.client.hget("Service", "setting")
        if int(checkflag) == 1:
            return {"success": False, "error": "Modbus setting is activated"}
    try:
        redis_state.client.hset("Service", "save", 1)
        redis_state.client.hset("Service", "restart", 1)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": "Redis Error"}

@router.get('/restartCore')
def restart_core():
    redis_state.client.select(0)
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
        redis_state.client.execute_command("SELECT", 0)
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
            return {"success": True, "result": result['resetRequired']}
        else:
            return {"success": False, "error": "resetRequired field not found in response"}

    except Exception as e:
        logging.error(str(e))
        return {"success": False, "error": str(e)}

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

@router.get("/test/{asset}")
async def test_asset(asset):
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

        if len(data) > 0:
            return {"success": True, "data": result}
        else:
            return {"success": False, "error": "No Data"}
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")
        return {"success": False, "error": "No Data"}

@router.get("/testwave/{asset}")
async def test_asset(asset, request:Request):
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
    redis_state.client.select(0)
    if not redis_state.client.exists("version"):
        return None
    fw = redis_state.client.hget("version","fw")
    a35 = redis_state.client.hget("version","a35")

    return {"fw":fw , "A35":a35}

@router.get("/SysCheck")
async def check_sysStatus():
    data = {}

    if os_spec.os == 'Windows':
        if not redis_state.client is None:
            redis_state.client.execute_command("SELECT", 0)
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
    redis_state.client.select(0)
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
        redis_state.client.select(1)
        redis_state.client.lpush('command', binary_data)

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


@router.get("/trigger")
async def push_both_channels(
        request: Request,
        cmd: int = CmdType.CMD_CAPTURE,  # 기본값: 2 (캡처)
        item: int = ItemType.ITEM_WAVEFORM  # 기본값: 7 (웨이브폼)
):
    try:
        # 채널 0에 푸시
        channel_0_command = Command(
            type=0,  # 채널 0
            cmd=cmd,
            item=item
        )
        result_0 = await push_command_left(channel_0_command, request)

        # 채널 1에 푸시
        channel_1_command = Command(
            type=1,  # 채널 1
            cmd=cmd,
            item=item
        )
        result_1 = await push_command_left(channel_1_command, request)

        return {
            "success": True,
            "message": "Command pushed to both channels (0 and 1)",
            "commands": {
                "channel_0": channel_0_command.dict(),
                "channel_1": channel_1_command.dict()
            },
            "results": {
                "channel_0": result_0,
                "channel_1": result_1
            }
        }
    except Exception as e:
        print(str(e))
        return {"success": False}

@router.get('/getMode')
def get_sysMode():
    try:
        redis_state.client.select(0)
        result = redis_state.client.hget("System","mode")
        return {"success": True, "mode": result}
    except Exception as e:
        print(str(e))
        return {"success": False}

@router.get('/updateSmartSystem/{mode}')
async def update_smartsystem(mode, request:Request):
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

    redis_state.client.select(0)
    result = redis_state.client.hget("System", "setup")
    if not result:
        return {"success": False, "message": "Setup data not found"}

    setting = json.loads(result)
    main_channel_data = next((ch for ch in setting["channel"] if ch.get("channel") == "Main"), None)
    sub_channel_data = next((ch for ch in setting["channel"] if ch.get("channel") == "Sub"), None)

    if not main_channel_data or not sub_channel_data:
        return {"success": False, "message": "Channel data not found"}

    if int(mode) == 1:
        main_channel_data['assetInfo']['name'] = ''
        main_channel_data['assetInfo']['type'] = ''
        main_channel_data['assetInfo']['nickname'] = ''
        sub_channel_data['assetInfo']['name'] = ''
        sub_channel_data['assetInfo']['type'] = ''
        sub_channel_data['assetInfo']['nickname'] = ''
        FILE_PATH = os.path.join(SETTING_FOLDER, "setup.json")
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(setting, f, indent=4)
        redis_state.client.hset("System","setup", json.dumps(setting))
        try:
            result = subprocess.run(
                ['sh', '/home/root/iss/install.sh', '--fresh'],
                capture_output=True,
                text=True,
                check=True
            )
            return {"success": True, "message": "Fresh install completed"}
        except subprocess.CalledProcessError as e:
            return {"success": False, "message": f"Install failed: {e.stderr}"}  # 6. 에러 메시지 추가
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Install timeout"}

    else:
        if main_channel_data['assetInfo']['name'] != '':
            reset_result1 = await reset_smart(main_channel_data['assetInfo']['name'], 0)
        if sub_channel_data['assetInfo']['name'] != '':
            reset_result2 = await reset_smart(sub_channel_data['assetInfo']['name'], 0)
        try:
            result = subprocess.run(
                ['sh', '/home/root/iss/install.sh'],
                capture_output=True,
                text=True,
                check=True
            )
            return {"success": True, "message": "Update completed"}
        except subprocess.CalledProcessError as e:
            return {"success": False, "message": f"Install failed: {e.stderr}"}
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Install timeout"}


