from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
import os, httpx, csv, psutil, struct
import ujson as json
import shutil, subprocess, logging, subprocess
from datetime import datetime
from states.global_state import influx_state, redis_state, aesState,os_spec
from collections import defaultdict
from routes.auth import checkLoginAPI
from routes.util import get_mac_address
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
async def initInflux():
    file_path = os.path.join(SETTING_FOLDER, 'influx.json')
    data = {
        "username": "admin",
        "password": "ntek9135",
        "org": "ntek",
        "bucket": "ntek",
        "retentionPeriodSeconds": 0  # 90 * 24 * 60 * 60
    }
    try:
        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.post(f"http://127.0.0.1:8086/api/v2/setup", json=data)
            resData = response.json()
            cipher = aesState.encrypt(resData.get("auth").get("token"))
            influxdata = {
                "token": cipher,
                "org": resData.get("org").get("name"),
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
        sysMdoe = redis_state.client.hget("System", "mode")
        if sysMdoe != 'device0':
            sysService('restart', 'SmartSystems')
            sysService('restart', 'SmartAPI')
        if set_cli['status']:
            return {"success": True, "message": "InfluxDB initialized successfully"}
        else:
            return {"success": True, "message": "InfluxDB initialized but check Influx CLI environment variables"}
    except Exception as e:
        logging.error(f"❌ Influxdb Init Error: {e}")
        influx_state.client = None
        influx_state.error = f"Exception during init: {str(e)}"
        return {"success": False, "message": influx_state.error}


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
export INFLUX_BUCKET="ntek"
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
            'INFLUX_BUCKET': "ntek"
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

        # 3. 설정 파싱 및 반환
        return parse_settings(setting)

    except Exception as e:
        return {"result": "0", "error": str(e)}


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

async def reset_asset():
    try:
        mainAsset = ''
        subAsset = ''
        redis_state.client.select(0)
        if redis_state.client.hexists("System", "setup"):
            setupflag = True
            datStr = redis_state.client.hget("System", "setup")
            setting = json.loads(datStr)
            mainAsset = ''
            subAsset = ''
            if setting["useFunction"]["diagnosis_main"]:
                for chInfo in setting["channel"]:
                    if chInfo["channel"] == 'Main':
                        mainAsset = chInfo["assetInfo"]["name"]
                        break
            if setting["useFunction"]["diagnosis_sub"]:
                for chInfo in setting["channel"]:
                    if chInfo["channel"] == 'Sub':
                        subAsset = chInfo["assetInfo"]["name"]
                        break
            if mainAsset != '':
                data = await reset_smart(mainAsset, 0)
                if len(data) > 0:
                    datas = await  reset_smart(mainAsset, 1)
                    if len(datas) > 0:
                        resetmain = 0
                    else:
                        resetmain = 1
                else:
                    resetmain = 2
            else:
                resetmain = -1
            if subAsset != '':
                data = await reset_smart(subAsset, 0)
                if len(data) > 0:
                    datas = await  reset_smart(subAsset, 1)
                    if len(datas) > 0:
                        resetsub = 0
                    else:
                        resetsub = 1
                else:
                    resetsub = 2
            else:
                resetsub = -1
        else:
            setupflag = False

        if not setupflag:
            return {"success": False, "msg": 'setup is not exist'}
        else:
            if resetmain > 1 or resetsub > 1:
                return {"success": False, "msg": "Unregistering asset is failed"}
            else:
                return {"success": True, "main":{"status":resetmain, "asset":mainAsset}, "sub":{"status":resetsub, "asset":subAsset}}
    except Exception as e:
        print(str(e))
        return {"success": False, "msg": str(e)}

async def reset_system():
    res = reset_asset()  # unregister main, sub asset
    if not res["success"]:
        return {"success": False, "msg": res["msg"]}
    else:
        ret = restartasset()  # smartservice restart
        if  ret["success"]:
            sysService("restart", "SmartSystems")
            sysService("restart", "SmartAPI")
    allcmd0 = Command(type=0, cmd=0, item=8)  # all item clear  (add item 8 to minhyuk)
    allcmd1 = Command(type=1, cmd=0, item=8)
    ret0 = await push_command_left(allcmd0)
    ret1 = await push_command_left(allcmd1)
    if not ret0["success"]:
        return {"success": False, "msg": 'Main channel clear is failed'}
    if not ret1["success"]:
        return {"success": False, "msg": 'Sub channel clear is failed'}
    return {"success": True}

@router.get('/ResetAll')
def resetAll():   #1. Unregiter asset, 2. Delete asset, 3. Restart SmartSystem, 4. Clear count, 5. Delete setup, 6. Delete user.db 7. setup default
    msg = ''
    if not redis_state.client is None:
        redis_state.client.execute_command("SELECT", 0)
        if redis_state.client.hexists("Service","setting"):
            checkflag = redis_state.client.hget("Service","setting")
            if int(checkflag) == 1:
                return {"success": False, "msg": "Modbus setting is activated"}
        ret = reset_system()
        if not ret["success"]:
            return {"success": False, "msg": 'System initialization is failed'}
        setting_path = os.path.join(SETTING_FOLDER, 'setup.json')
        db_path = os.path.join(SETTING_FOLDER, 'user.db')
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

            default_file_path = os.path.join(SETTING_FOLDER, 'default.json')

            with open(default_file_path, "r", encoding="utf-8") as f:
                defaults = json.load(f)

            defaults["mode"] = 'device0'
            defaults["General"]["deviceInfo"]["mac_address"] = ""
            defaults["General"]["deviceInfo"]["serial_number"] = ""

            with open(default_file_path, "w", encoding="utf-8") as f:
                json.dump(defaults, f, indent=2)  # indent 추가로 가독성 향상

            if redis_state.client.hexists("System", "setup"):
                redis_state.client.hdel("System","setup")
            if redis_state.client.hexists("System", "mode"):
                redis_state.client.hdel("System","mode")
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
    if len(data) > 0:
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
    if len(data) > 0:
        return {"success": True, "data": data}
    else:
        return {"success": False, "error": "No Data"}

@router.post('/setDiagnosisSetting')
async def set_diagnosissetting(request: Request):
    data = await request.json()
    if not data:
        return {"status": "0", "error": "No data provided"}
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
        return {"status": "0", "error": str(e)}

    if len(data) > 0:
        return {"status": "1", "success": True }
    else:
        return {"status": "1", "success": False, "error": "Save Failed"}

@router.post('/setDiagnosisProfile')
async def set_diagnosisprofile(request: Request):
    data = await request.json()
    if not data:
        return {"status": "0", "error": "No data provided"}
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
        return {"status": "0", "error": str(e)}

    if len(data) > 0:
        return {"status": "1","success": True }
    else:
        return {"status": "1", "success": False, "error": "Save Failed"}

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
    if len(data) > 0:
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

@router.get('/registerAsset/{channel}/{assetName}/{assetType}')
async def reg_Asset(channel, assetName, assetType):
    async with httpx.AsyncClient(timeout=setting_timeout) as client:
        response = await client.get(f"http://{os_spec.restip}:5000/api/registerAsset?name={assetName}")
        data = response.json()
    if len(data) > 0:
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
         
        else:
            # 그 외의 경우, "channel" 배열 내에서 해당 채널 업데이트 (없으면 추가)
            if "channel" not in setting or not isinstance(setting["channel"], list):
                setting["channel"] = []
            updated = False
            for idx, ch in enumerate(setting["channel"]):
                if ch.get("channel", "").lower() == channel.lower():
                    setting["channel"][idx] = data
                    updated = True
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
        redis_state.client.hset("System", "setup", json.dumps(setting))

        return {"status": "1", "data": setting}
    except Exception as e:
        print("Error:", e)
        return {"status": "0", "error": str(e)}

@router.get('/checkSystem/{mode}')
def checkService(mode):
    restartsmart = False
    restartapi = False
    if mode == 1:
        if is_service_enabled("smartsystemsservice"):
            if not is_service_active("smartsystemsservice"):
                sysService("start", "SmartSystems")
            else:
                restartsmart = True
        else:
            sysService("enable", "SmartSystems")
            sysService("start", "SmartSystems")
        if is_service_enabled("smartsystemsrestapiservice"):
            if not is_service_active("smartsystemsrestapiservice"):
                sysService("start", "SmartAPI")
            else:
                restartapi = True
        else:
            sysService("enable", "SmartAPI")
            sysService("start", "SmartAPI")
    else:
        if is_service_enabled("smartsystemsservice"):
            if is_service_active("smartsystemsservice"):
                sysService("stop", "SmartSystems")
            sysService("disable", "SmartSystems")
        if is_service_enabled("smartsystemsrestapiservice"):
            if is_service_active("smartsystemsrestapiservice"):
                sysService("stop", "SmartAPI")
            sysService("disable", "SmartAPI")
    return {"smart": restartsmart, "api": restartapi}

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
async def check_assetconfig(asset:str, request:Request):
    data = await request.json()
    if not data:
        return {"status": "0", "error": "No data provided"}
    try:
        # response = await  http_state.client.post(f"/checkNameplate?name={asset}", json=data)
        # result = response.json()
        async with httpx.AsyncClient(timeout=setting_timeout) as client:
            response = await client.post(f"http://{os_spec.restip}:5000/api/checkNameplate?name={asset}", json=data)
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
        return {"status": "0", "error": str(e)}

    if len(result) > 0:
        return {"success":True, "result":result['resetRequired']}
    else:
        return {"success": False, "error": "No Data"}

@router.post("/setAssetConfig/{asset}")
async def set_assetconfig(asset:str, request:Request):
    data = await request.json()
    if not data:
        return {"status": "0", "error": "No data provided"}
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
        return {"status": "0", "error": str(e)}

    if len(result) > 0:
        return {"success": True}
    else:
        return {"success": False, "error": "No Data"}

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
        return {"status": "0", "error": "No data provided"}
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
        return {"status": "0", "error": str(e)}

    if len(result) > 0:
        return {"success": True}
    else:
        return {"success": False, "error": "No Data"}

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

def is_service_active(name):
    try:
        result = subprocess.run(['systemctl', 'is-active', name],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                timeout=2)
        return result.stdout.strip() == "active"
    except Exception as e:
        print(f"❌ 서비스 상태 확인 실패: {name} - {e}")
        return False

@router.get("/SysCheck")
def check_sysStatus():
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
        servicedict = {
            'smartsystem' : 'smartsystemsservice',
            'smartapi': 'smartsystemsrestapiservice',
            'redis': 'redis',
            'influxdb': 'influxdb',
            'core': 'core',
            'webserver':'webserver'
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

        return {"success": True, "data":service_status,  "disk":[disk1, disk2]}

@router.get('/SysService/{cmd}/{item}')
def sysService(cmd, item):
    itemdict = {
      "Redis":"redis",
      "InfluxDB":"influxdb",
      "SmartSystems":"smartsystemsservice",
      "SmartAPI":"smartsystemsrestapiservice",
      "Core":"core",
      "WebServer":"webserver",
    }

    try:
        # systemctl 명령 실행
        result = subprocess.run(
            ['sudo', 'systemctl', cmd, itemdict[item]],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )

        return {
            'success': True,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'returncode': result.returncode,
            'service': itemdict[item],
            'action': cmd
        }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': f'Timeout expired while {cmd}ing {itemdict[item]}',
            'service': itemdict[item],
            'action': cmd
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'service': itemdict[item],
            'action': cmd
        }

@router.get('/ServiceStatus')
def check_allservice():
    redis_state.client.select(0)
    devMode = redis_state.client.hget("System", "mode")

    if devMode == 'device0':
        servicedict = {
            'redis': 'redis',
            'influxdb': 'influxdb',
            'core': 'core',
            'webserver': 'webserver'
        }
    else:
        servicedict = {
            'smartsystem': 'smartsystemsservice',
            'smartapi': 'smartsystemsrestapiservice',
            'redis': 'redis',
            'influxdb': 'influxdb',
            'core': 'core',
            'webserver': 'webserver'
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
async def push_command_left(command: Command):
    """새로운 command를 Redis 리스트의 왼쪽에 추가"""
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
        result_0 = await push_command_left(channel_0_command)

        # 채널 1에 푸시
        channel_1_command = Command(
            type=1,  # 채널 1
            cmd=cmd,
            item=item
        )
        result_1 = await push_command_left(channel_1_command)

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

