from fastapi import APIRouter, UploadFile, File, Request
from states.global_state import redis_state
import os, csv, sqlite3, shutil, logging
import ujson as json
import struct, subprocess
from pathlib import Path
from pydantic import BaseModel
from datetime import date
from .api import get_Calibrate
from utils.util import get_mac_address, Post, save_post, get_db_connection, get_lastpost, getVersions,check_get_logdb, service_exists, saveLog
from datetime import datetime
router = APIRouter()

# Path 객체 절대경로

base_dir = Path(__file__).resolve().parent
SETTING_FOLDER = base_dir.parent.parent / "config"  # ⬅️ 두 단계 상위로
DB_PATH = os.path.join(SETTING_FOLDER, "maintenance.db")


class CaliSet(BaseModel):
    channel: str
    type: str
    cmd: str
    cmdnum: str
    ref1 : str
    ref2 : str
    param: str

class CaliRef(BaseModel):
    U: str
    I: str
    In: str
    P: str
    Error: str

setting_file = os.path.join(SETTING_FOLDER, 'setup.json')
backup_file = os.path.join(SETTING_FOLDER, 'setup_backup.json')

class TimeSetRequest(BaseModel):
    datetime_str: str  # "2024-10-24T15:30:00"
    timezone: str = "Asia/Seoul"

def parse_csv(file_path):
    data = []
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    return data

def parse_csv_filelike(file_obj):
    data = []
    file_obj.seek(0)  # 위치 초기화
    reader = csv.DictReader(line.decode('utf-8') for line in file_obj)
    for row in reader:
        data.append(row)
    return data

@router.post('/upload')
def upload_file(file: UploadFile = File(...)):
    if file.filename == '':
        print('No selected file')
        return {'passOK': '0', 'error': 'No selected file'}
    else:
        try:
            calibration_file_path = os.path.join(SETTING_FOLDER, file.filename)
            with open(calibration_file_path, "wb") as f:
                content = file.file.read()
                f.write(content)
            data = parse_csv_filelike(file.file)
            redis_state.client.hset('calibration','setup', json.dumps(data))
            return {'passOK': '1', 'data': data, 'file_path': file.filename}
            # original_file_path = os.path.join(SETTING_FOLDER, 'setup.json')
            # if os.path.exists(original_file_path):
            #     with open(original_file_path, "r", encoding="utf-8") as f:
            #         setting = json.load(f)
            #     if len(data) > 0:
            #         for idx, ch in enumerate(setting["channel"]):
            #             ctData = setting["channel"][idx]["ctInfo"]
            #             for key, value in ctData:
            #                 ctData[key] = data[key]
            #             ptData = setting["channel"][idx]["ptInfo"]
            #             for key, value in ptData:
            #                 ptData[key] = data[key]
            #     if setting:
            #         with open(original_file_path, "w", encoding="utf-8") as f:
            #             json.dump(setting, f, indent=4)
            #         return {'passOK': '1', 'data': data, 'file_path':file.filename}
            #     else:
            #         return {'passOK': '0', 'error': 'Apply Failed'}
            # else:
            #     return {'passOK': '0', 'error': 'No exist setup file'}
        except Exception as e:
            return {'passOK': '0', 'error': str(e)}

@router.get('/checkSetup')
def check_setup():
    mac = get_mac_address()
    # redis_state.client.execute_command("SELECT", 0)
    if redis_state.client.hexists('calibration','setup'):
        data = redis_state.client.hget('calibration','setup')
        datalist = json.loads(data)
        return {'passOK': '1', 'data':datalist, 'mac': mac}
    else:
        return {'passOK': '0', 'error': 'No exist calibration setup', 'mac':mac}

@router.get('/calibrate/getUnbal')
def getUnbal():
    file_path = os.path.join(SETTING_FOLDER, 'setup.json')
    default_file_path = os.path.join(SETTING_FOLDER, 'default.json')
    # redis_state.client.select(0)
    if redis_state.client.hexists("System", "setup"):
        # Redis에 있으면 Redis 데이터 사용
        setting = json.loads(redis_state.client.hget("System", "setup"))
    else:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                setting = json.load(f)
        except json.JSONDecodeError:
            # setup.json이 손상된 경우 default.json으로 복구
            shutil.copy(default_file_path, file_path)
            with open(file_path, "r", encoding="utf-8") as f:
                setting = json.load(f)
    return { 'unbal': setting['unbalance']}

@router.get('/calibrateNow')
def cali_mount():
    mainResponse = get_Calibrate('Main')
    subResponse = get_Calibrate('Sub')

    return {'mainStatus': mainResponse['success'], 'mainData':mainResponse['retData']['meterData'], 'mainRef':mainResponse['retData']['refData'],
            'subStatus': subResponse['success'], 'subData': subResponse['retData']['meterData'], 'subRef': subResponse['retData']['refData']}

@router.get('/calibrate/applySetup')
def cali_setup():
    # redis_state.client.execute_command("SELECT", 0)
    if redis_state.client.hexists('calibration','setup'):
        shutil.copy(backup_file, setting_file)
        data = redis_state.client.hget('calibration','setup')
        datalist = json.loads(data)
        redis_state.client.hset("System", "setup", json.dumps(datalist))
        with open(SETTING_FOLDER, "w", encoding="utf-8") as f:
            json.dump(datalist, f, indent=4)
        redis_state.client.hset('service', 'cflag', 1)
        redis_state.client.hset('Service', 'save', 1)
        return {'passOK': '1'}
    else:
        return {'passOK': '0', 'error': 'No exist calibration setup'}

@router.post('/calibrate/saveRef')
def set_saveref(data:CaliRef):
    try:
        # redis_state.client.select(0)
        refdata = {"U": int(data.U), "I": int(data.I), "In": int(data.In), "P": int(data.P), "Error": float(data.Error)}
        redis_state.client.hset("calibration", "ref", json.dumps(refdata))
        return {'passOK': '1'}
    except Exception as e:
        print(str(e))
        return {'passOK': '0'}

@router.get('/calibrate/start')
def cali_start():
    try:
        # redis_state.client.select(0)
        redis_state.client.hset('Service','calibration', 1)
        return {'passOK': '1'}
    except Exception as e:
        return {'passOK': '0', 'error': str(e)}

@router.get('/calibrate/end')
def cali_end():
    # redis_state.client.select(0)
    redis_state.client.hset('Service', 'calibration', 0)
    if redis_state.client.hexists('calibration', 'setup') and redis_state.client.hexists('calibration','cflag'):
        if redis_state.client.hget('calibration', 'cflag') == 1:
            endflag = True
            redis_state.client.hset('calibration', 'cflag', 0)
        else:
            endflag = False
    else:
        endflag = False

    if endflag:
        try:
            shutil.copy(setting_file, backup_file)
            with open(setting_file, "r", encoding="utf-8") as f:
                setting = json.load(f)
                # redis_state.client.execute_command("SELECT", 0)
                redis_state.client.hset("System", "setup", json.dumps(setting))
            redis_state.client.hdel("calibration", "setup")
            redis_state.client.hset("Service", "save", 1)
            return {'passOK': '1'}
        except Exception as e:
            return {'passOK': '0', 'error': 'No exist setup file'}
    else:
        if redis_state.client.hexists("calibration","ref"):
            redis_state.client.hdel("calibration","ref")
        return {'passOK': '1'}

@router.post('/calibrate/cmd')
def set_cmd(data:CaliSet):
    try:
        if data.channel == 'Main':
            mode = 0
        elif data.channel == 'Sub':
            mode = 1
        else:
            mode = 2
        if data.type == 'SET':
            if data.ref1 != 'None':
                val1 = float(data.ref1)
            else:
                val1 = 0.0
            if data.ref2 != 'None':
                val2 = float(data.ref2)
            else:
                val2 = 0.0
        else:
            val1 = 0.0
            val2 = 0.0
        msg = {
            'id':mode,
            'cmd': data.cmdnum,
            'ref1': val1,
            'ref2': val2
        }

        # redis_state.client.select(0)
        if redis_state.client.hexists("calibration","ref"):
            refdict = json.loads(redis_state.client.hget("calibration", "ref"))
            if data.param != 'None':
                if "," in data.param:
                    refdict["U"] = float(data.ref1)
                    refdict["I"] = float(data.ref2)
                else:
                    refdict[data.param] = float(data.ref1)
                redis_state.client.hset("calibration", "ref", json.dumps(refdict))

        format_string = 'iiff'

        # 바이너리 데이터 생성

        redis_state.binary_client.select(0)
        binary_data = struct.pack(format_string,
                              int(msg['id']),      # 명시적 변환
                              int(msg['cmd']),     # 명시적 변환
                              float(msg['ref1']),  # 명시적 변환
                              float(msg['ref2']))  # 명시적 변환

        redis_state.binary_client.lpush('cali_command',binary_data)
        if data.type == 'SAVE':
            post= Post( title = 'Calibration',  context = 'Calibration',mtype = 3, utype='')
            save_post(post, 0, 0)
        return {'passOK': '1'}
    except Exception as e:
        logging.error(f"Error: {e}")
        return {'passOK': '0'}

@router.get("/calibrate/gettime")
async def get_device_time():
    """
    현재 장비 시간 조회
    """
    try:
        return {
            "success": True,
            "deviceTime": datetime.now().isoformat(),
            "timestamp": datetime.now().timestamp()
        }
    except Exception as e:
        return {"success": False }

@router.post("/calibrate/setSystemTime")
async def set_system_time(data: TimeSetRequest, request: Request):
    saveLog("Set Time", request)
    try:
        tz_cmd = f"timedatectl set-timezone {data.timezone}"
        subprocess.run(tz_cmd, shell=True, check=True)
        date_cmd = f"date -s '{data.datetime_str}'"
        result = subprocess.run(date_cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"System time set to: {data.datetime_str}")

        subprocess.run("hwclock -w", shell=True, check=True)
        current = subprocess.run("date", shell=True, capture_output=True, text=True)

        return {
            "success": True,
            "message": "System time updated",
            "current_time": current.stdout.strip(),
            "timezone": data.timezone
        }
    except Exception as e:
        logging.error(f"Error: {e}")
        return { "success": False }

@router.post("/checktime")
async def check_device_time(request: TimeSetRequest):
    """
    클라이언트 시간과 장비 시간 비교하여 상태 반환
    """
    try:
        device_now = datetime.now()

        # 클라이언트 시간 파싱 (YYYY-MM-DD HH:mm:ss 형식)
        client_dt = datetime.strptime(request.datetime_str, '%Y-%m-%d %H:%M:%S')

        # 시간 차이 계산
        diff_seconds = abs((device_now - client_dt).total_seconds())
        twenty_four_hours = 24 * 60 * 60  # 86400초
        status = diff_seconds <= twenty_four_hours

        return {
            "success": True,
            "deviceTime": device_now.isoformat(),
            "status": status,  # True: 정상, False: 24시간 이상 차이
            "diffSeconds": int(diff_seconds)
        }
    except Exception as e:
        logging.error(f"Error checking time: {e}")
        return {"success": False, "status": False}

@router.post('/savePost/{mode}/{idx}')
def save_maintanence(data: Post, mode: int, idx:int):
    return save_post(data,mode, idx)

@router.get('/getPost')
def get_post():
    """maintenance 테이블의 전체 데이터를 조회"""
    try:
        conn = get_db_connection()  # 이미 테이블 생성 보장됨
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM maintenance")
        rows = cursor.fetchall()
        conn.close()

        if rows:
            result = [dict(row) for row in rows]
            return {"result": 1, "data": result}
        else:
            return {"result": 0}

    except Exception as e:
        print(f"GET_POST ERROR: {e}")
        return {"result": 0, "msg": str(e)}


@router.get('/getLastPost')
def get_last():
    ret = get_lastpost()
    if ret.get("result") == 1:
        lastpost = ret.get("data", {})
        version_dict = getVersions()
        updateList = []

        key_map = {
            'fw': 'f_version',
            'a35': 'a_version',
            'web': 'w_version',
            'core': 'c_version',
            'smartsystem': 'smart_version'
        }

        if version_dict:
            for src_key, dst_key in key_map.items():
                last_val = lastpost.get(dst_key)
                ver_val = version_dict.get(src_key)
                if ver_val and last_val != ver_val:
                    lastpost[dst_key] = ver_val
                    updateList.append(src_key)

            if updateList:
                result = ",".join(updateList)
                update = Post(
                    title='Update SW',
                    context='Update SW',
                    mtype=1,
                    utype=result,
                    f_version=lastpost.get('f_version'),
                    a_version=lastpost.get('a_version'),
                    w_version=lastpost.get('w_version'),
                    c_version=lastpost.get('c_version'),
                    smart_version=lastpost.get('smart_version')
                )
                return {"result": 1, "data": update.dict(), "update":updateList}

    return ret


@router.get('/deletePost/{idx}')
def delete_post(idx):
    try:
        db_exists = os.path.exists(DB_PATH)
        if db_exists:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("delete FROM maintenance where id=?",(idx,))
            conn.commit()
            conn.close()
            return {"result": 1}
        else:
            return {"result": 0}
    except Exception as e:
        print(str(e))
        return {"result": 0}

@router.get('/getLog')
def get_log(page: int = 1, page_size: int = 10):
    """log 테이블의 데이터를 페이징하여 조회 (최신순)"""
    try:
        conn = check_get_logdb()
        cursor = conn.cursor()

        # 전체 개수
        cursor.execute("SELECT COUNT(*) as total FROM log")
        total = cursor.fetchone()['total']

        # 페이징
        offset = (page - 1) * page_size
        cursor.execute(
            "SELECT * FROM log ORDER BY id DESC LIMIT ? OFFSET ?",
            (page_size, offset)
        )
        rows = cursor.fetchall()
        conn.close()

        return {
            "result": 1 if rows else 0,
            "data": [dict(row) for row in rows] if rows else [],
            "total": total,
            "page": page,
            "total_pages": (total + page_size - 1) // page_size
        }

    except Exception as e:
        print(f"GET_POST ERROR: {e}")
        return {"result": 0, "msg": str(e)}


@router.get('/applog/recent/{item}')
def get_recent_logs(item: str, lines: int = 5, log_type: str = "all"):
    LOG_PATH = {
        "SmartSystems": "/usr/local/smartsystems/log",
        "Core": "/usr/local/sv500/logs/core",
        "WebServer": "/usr/local/sv500/logs/web",
        "A35": "/usr/local/sv500/logs/a35",
    }

    JOURNAL_SERVICES = {
        "frpc": "frpc",
        "mqClient": "mqClient",
    }

    try:
        # Journal 로그 처리
        if item in JOURNAL_SERVICES:
            service_name = JOURNAL_SERVICES[item]

            # 서비스 존재 여부 확인
            if not service_exists(f"{service_name}.service"):
                return {"success": False, "message": f"{item} 서비스가 설치되지 않음"}

            result = subprocess.run(
                ['journalctl', '-u', service_name, '-n', str(lines), '--no-pager', '-o', 'short'],
                capture_output=True,
                text=True,
                timeout=10
            )

            log_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            # "-- No entries --" 등 제거
            log_lines = [l for l in log_lines if l and not l.startswith('--')]

            if not log_lines:
                return {"success": False, "message": "로그 없음"}

            return {
                "success": True,
                "source": "journal",
                "service": service_name,
                "lines": log_lines,
                "count": len(log_lines)
            }

        # 파일 기반 로그 처리
        if item not in LOG_PATH:
            return {"success": False, "message": "잘못된 항목"}

        if not os.path.exists(LOG_PATH[item]):
            return {"success": False, "message": "로그 디렉토리 없음"}

        # 크기가 0보다 큰 로그 파일만 필터링
        log_files = [
            f for f in os.listdir(LOG_PATH[item])
            if f.endswith('.log') and os.path.getsize(os.path.join(LOG_PATH[item], f)) > 0
        ]

        # SmartSystems: 로그 타입별 필터링
        if item == "SmartSystems" and log_type != "all":
            if log_type == "ss":
                log_files = [f for f in log_files if f.startswith('SS')]
            elif log_type == "api":
                log_files = [f for f in log_files if f.startswith('RestAPI')]

        if not log_files:
            return {"success": False, "message": "로그 파일 없음"}

        # 수정 시간 기준 최신 파일
        latest_file = max(
            log_files,
            key=lambda f: os.path.getmtime(os.path.join(LOG_PATH[item], f))
        )

        file_path = os.path.join(LOG_PATH[item], latest_file)

        # 최근 N줄 읽기 (tail)
        result = subprocess.run(
            ['tail', '-n', str(lines), file_path],
            capture_output=True,
            text=True,
            timeout=5
        )

        log_lines = result.stdout.strip().split('\n') if result.stdout else []

        return {
            "success": True,
            "source": "file",
            "file": latest_file,
            "lines": log_lines,
            "count": len(log_lines)
        }

    except Exception as e:
        return {"success": False, "message": str(e)}