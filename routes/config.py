from fastapi import APIRouter, UploadFile, File
from states.global_state import redis_state
import os, csv, sqlite3, shutil, logging
import ujson as json
import struct, subprocess
from pathlib import Path
from pydantic import BaseModel
from datetime import date
from .api import get_Calibrate
from .util import get_mac_address, Post, save_post, get_db_connection
from datetime import datetime
router = APIRouter()

# Path 객체 절대경로

base_dir = Path(__file__).resolve().parent
SETTING_FOLDER = base_dir.parent.parent / "config"  # ⬅️ 두 단계 상위로
DB_PATH = os.path.join(SETTING_FOLDER, "maintenance.db")

# def get_db_connection():
#     conn = sqlite3.connect(DB_PATH)
#     conn.row_factory = sqlite3.Row  # → dict처럼 row 접근 가능
#     return conn
#


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
    redis_state.client.execute_command("SELECT", 0)
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
    redis_state.client.select(0)
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
    redis_state.client.execute_command("SELECT", 0)
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
        redis_state.client.select(0)
        refdata = {"U": int(data.U), "I": int(data.I), "In": int(data.In), "P": int(data.P), "Error": float(data.Error)}
        redis_state.client.hset("calibration", "ref", json.dumps(refdata))
        return {'passOK': '1'}
    except Exception as e:
        print(str(e))
        return {'passOK': '0'}

@router.get('/calibrate/start')
def cali_start():
    try:
        redis_state.client.select(0)
        redis_state.client.hset('Service','calibration', 1)
        return {'passOK': '1'}
    except Exception as e:
        return {'passOK': '0', 'error': str(e)}

@router.get('/calibrate/end')
def cali_end():
    redis_state.client.select(0)
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
                redis_state.client.execute_command("SELECT", 0)
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

        redis_state.client.select(0)
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
async def set_system_time(request: TimeSetRequest):
    try:
        tz_cmd = f"timedatectl set-timezone {request.timezone}"
        subprocess.run(tz_cmd, shell=True, check=True)
        date_cmd = f"date -s '{request.datetime_str}'"
        result = subprocess.run(date_cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"System time set to: {request.datetime_str}")

        # 3. 하드웨어 시계 동기화
        subprocess.run("hwclock -w", shell=True, check=True)

        # 4. 현재 시간 확인
        current = subprocess.run("date", shell=True, capture_output=True, text=True)

        return {
            "success": True,
            "message": "System time updated",
            "current_time": current.stdout.strip(),
            "timezone": request.timezone
        }
    except Exception as e:
        logging.error(f"Error: {e}")
        return { "success": False }

@router.post('/savePost/{mode}/{idx}')
def save_maintanence(data: Post, mode: int, idx:int):
    return save_post(data,mode, idx)
    # title = data.title
    # context = data.context
    # mtype = data.mtype
    # utype = data.utype
    # f_version = data.f_version
    # a_version = data.a_version
    # w_version = data.w_version
    # c_version = data.c_version
    # smart_version = data.smart_version
    # today = date.today()
    # formatted = today.strftime("%Y-%m-%d")
    # try:
    #     conn = get_db_connection()
    #     cursor = conn.cursor()
    #     if mode == 0:
    #         cursor.execute(
    #             "INSERT INTO `maintenance` (title,context, mtype, utype, f_version, a_version, w_version,c_version, smart_version,date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    #             (title, context, mtype, utype, f_version,a_version,w_version, c_version,smart_version, formatted)
    #         )
    #     else:
    #         cursor.execute(
    #             "UPDATE `maintenance` SET title=?,context=?, mtype=?, utype=?, f_version=?, a_version=?, w_version=?,c_version=?, smart_version=?, date=? where id=?",
    #             (title, context, mtype, utype, f_version, a_version, w_version, c_version,smart_version, formatted, idx )
    #         )
    #     conn.commit()
    #     conn.close()
    #     return {"passOK": "1"}
    # except Exception as e:
    #     print(str(e))
    #     return {"passOK": "0", "msg": str(e)}

@router.get('/getPost')
def get_post():
    result = []
    try:
        db_exists = os.path.exists(DB_PATH)
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        flag = False
        if not db_exists:
            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS maintenance (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            context TEXT NOT NULL,
                            mtype int NOT NULL,
                            utype TEXT NOT NULL,
                            f_version TEXT,
                            a_version TEXT,
                            w_version TEXT,
                            c_version TEXT,
                            smart_version TEXT,
                            date TEXT
                        )
                    ''')
            cursor.execute("SELECT * FROM maintenance")
            rows = cursor.fetchall()
            if len(rows) > 0:
                result = [dict(row) for row in rows]
                flag = True
            else:
                flag = False
        else:
            cursor.execute("SELECT * FROM maintenance")
            rows = cursor.fetchall()
            if len(rows) > 0:
                result = [dict(row) for row in rows]
                flag = True
            else:
                flag = False
        conn.commit()
        conn.close()
    except Exception as e:
        print(str(e))
        flag = False
    if flag:
        return {"result": 1, "data": result}
    else:
        return {"result": 0}

@router.get('/getLastPost')
def get_post():
    last_record = {}
    try:
        # db_exists = os.path.exists(DB_PATH)
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
                        SELECT * FROM maintenance 
                        ORDER BY id DESC 
                        LIMIT 1
                    ''')
        last_record = cursor.fetchone()
        if len(last_record) > 0:
            flag = True
        else:
            flag = False
        conn.commit()
        conn.close()
    except Exception as e:
        print(str(e))
        flag = False
    if flag:
        return {"result": 1, "data": dict(last_record)}
    else:
        return {"result": 0}

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
