import logging, socket
import uuid, psutil, sqlite3, os, subprocess
import httpx
from pathlib import Path
from datetime import date
from pydantic import BaseModel
from fastapi import Request
from enum import IntEnum
from states.global_state import redis_state, os_spec

base_dir = Path(__file__).resolve().parent
SETTING_FOLDER = base_dir.parent.parent / "config"  # ⬅️ 두 단계 상위로
DB_PATH = os.path.join(SETTING_FOLDER, "maintenance.db")
LogDB_PATH = "/usr/local/sv500/logs/web/log.db"

class Post(BaseModel):
    title: str
    context: str
    mtype: int
    utype: str
    f_version: str = ""
    a_version: str = ""
    w_version: str = ""
    c_version: str = ""
    smart_version: str = ""
    mq_version: str = ""
    build_version: str = ""

class WatchTarget(IntEnum):
    MAIN = 0
    SUB = 1
    BOTH = 2

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

WAVEFORM_PATHS = {
    WatchTarget.MAIN: "/sv500/ch1/waveform",
    WatchTarget.SUB: "/sv500/ch2/waveform"
}

def get_db_connection():
    """DB 연결 및 테이블 생성"""
    try:
        # 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

        # DB 연결
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 테이블 생성 (없으면)
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
                mq_version TEXT,
                build_version TEXT,
                date TEXT
            )
        ''')
        conn.commit()

        # build_version, mq_version 컬럼 마이그레이션 (기존 DB 대응)
        cursor.execute("PRAGMA table_info(maintenance)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'build_version' not in columns:
            cursor.execute("ALTER TABLE maintenance ADD COLUMN build_version TEXT DEFAULT ''")
            conn.commit()
        if 'mq_version' not in columns:
            cursor.execute("ALTER TABLE maintenance ADD COLUMN mq_version TEXT DEFAULT ''")
            conn.commit()

        return conn

    except Exception as e:
        logging.error(f"DB Connection Error: {str(e)} - {DB_PATH}")
        print(f"DB Connection Error: {str(e)} - {DB_PATH}")
        raise


def create_logdb_connection():
    conn = sqlite3.connect(LogDB_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            logdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            account TEXT NOT NULL,
            userRole TEXT NOT NULL,
            action TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    if os.path.exists(LogDB_PATH):
        return True
    else:
        return False

def check_get_logdb():
    conn = sqlite3.connect(LogDB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def saveLog(action: str, request: Request):
    user = request.session.get("user")
    userRole = request.session.get("userRole")

    conn = check_get_logdb()
    if conn is None:
        logging.error("Database connection failed")
        return

    try:
        cursor = conn.cursor()

        # 로그 삽입
        cursor.execute(
            "INSERT INTO log (account, userRole, action) VALUES (?, ?, ?)",
            (user, userRole, action)
        )

        # 방금 삽입한 ID로 조회
        last_id = cursor.lastrowid
        cursor.execute("SELECT * FROM log WHERE id = ?", (last_id,))
        last_record = cursor.fetchone()

        if last_record:
            logMessage = f"{last_record['logdate']}: {last_record['action']}/{last_record['userRole']}-{last_record['account']}"
            logging.debug(logMessage)

        conn.commit()

    except Exception as e:
        logging.error(f"Error in saveLog: {e}")
        conn.rollback()
    finally:
        conn.close()


def updateLog(action: str, request: Request):
    user = request.session.get("user")
    userRole = request.session.get("userRole")

    conn = check_get_logdb()
    if conn is None:
        logging.error("Database connection failed")
        return

    try:
        cursor = conn.cursor()

        # 동일 action 기록이 있으면 시간만 업데이트, 없으면 새로 삽입
        cursor.execute("SELECT id FROM log WHERE action = ?", (action,))
        row = cursor.fetchone()

        if row:
            cursor.execute(
                "UPDATE log SET logdate = CURRENT_TIMESTAMP, account = ?, userRole = ? WHERE id = ?",
                (user, userRole, row['id'])
            )
        else:
            cursor.execute(
                "INSERT INTO log (account, userRole, action) VALUES (?, ?, ?)",
                (user, userRole, action)
            )

        conn.commit()

    except Exception as e:
        logging.error(f"Error in updateLog: {e}")
        conn.rollback()
    finally:
        conn.close()


def get_mac_address():
    """지정된 네트워크 카드들의 MAC 주소 가져오기"""

    # 사용할 네트워크 인터페이스 이름들 지정 (우선순위 순으로)
    TARGET_INTERFACES = ['sw0ep', 'end1']  # 필요에 따라 변경 가능

    try:
        # 지정된 인터페이스들을 순서대로 확인
        network_interfaces = psutil.net_if_addrs()

        for interface_name in TARGET_INTERFACES:
            if interface_name in network_interfaces:
                for addr in network_interfaces[interface_name]:
                    if addr.family == psutil.AF_LINK:  # MAC 주소
                        mac = addr.address.replace('-', '').replace(':', '').lower()
                        if mac and mac != '000000000000':
                            return mac

        # 지정된 인터페이스들이 모두 없으면 uuid.getnode() 사용
        mac_int = uuid.getnode()
        mac_address = f'{mac_int:012x}'
        return mac_address

    except Exception as e:
        print(f"MAC 주소 가져오기 실패: {e}")
        # 예외 발생 시에도 uuid.getnode() 사용
        mac_int = uuid.getnode()
        mac_address = f'{mac_int:012x}'
        return mac_address

def get_ip_address():
    """지정된 네트워크 카드들의 IP 주소 가져오기"""

    TARGET_INTERFACES = ['sw0ep', 'end1']

    try:
        network_interfaces = psutil.net_if_addrs()

        for interface_name in TARGET_INTERFACES:
            if interface_name in network_interfaces:
                for addr in network_interfaces[interface_name]:
                    if addr.family == socket.AF_INET:
                        ip = addr.address
                        if ip and ip != '127.0.0.1':
                            return ip

        return '0.0.0.0'

    except Exception as e:
        print(f"IP 주소 가져오기 실패: {e}")
        return '0.0.0.0'

def getVersions():
    versionPath = '/home/root/versionInfo.txt'
    version_dict = {}
    if os.path.exists(versionPath):
        with open(versionPath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line:
                    key, value = line.split('=')
                    version_dict[key.strip()] = value.strip()
    return version_dict

VERSION_PATH = '/home/root/versionInfo.txt'

REDIS_TO_LOCAL = {
    "fw": "fw",
    "A35": "a35",
    "webserver": "web",
    "core": "core",
    "SmartSystems": "smartsystem",
    "mqClient": "mqClient",
}

LOCAL_TO_SERVICE = {
    "fw": None,
    "a35": "sv500A35.service",
    "web": "webserver.service",
    "core": "core.service",
    "smartsystem": "smartsystemsservice.service",
    "mqClient": "mqClient.service",
}

def _ver_tuple(v):
    try:
        return tuple(int(x) for x in v.split('.'))
    except (ValueError, AttributeError):
        return (0,)

def _latest(a, b):
    if not a:
        return b
    if not b:
        return a
    return a if _ver_tuple(a) >= _ver_tuple(b) else b

def _read_file_versions():
    d = {}
    if os.path.exists(VERSION_PATH):
        with open(VERSION_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line:
                    k, v = line.split('=', 1)
                    d[k.strip()] = v.strip()
    return d

def _read_redis_versions():
    d = {}
    if redis_state.client and redis_state.client.exists("version"):
        for rk, lk in REDIS_TO_LOCAL.items():
            if redis_state.client.hexists("version", rk):
                val = redis_state.client.hget("version", rk)
                if val:
                    d[lk] = val
    return d

async def _fetch_smart_api():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"http://{os_spec.restip}:5000/api/version")
            return r.json().get("Version")
    except Exception:
        return None

# 자기가 직접 hset하지 않는 외부 의존 컴포넌트만 getVersionNew가 Redis에 캐싱
SELF_HSET_EXEMPT = {"smartsystem", "mqClient"}

def _save_redis_version(local_key, value):
    """SmartSystems/mqClient 한정으로 version 해시에 저장.
    fw/a35/web/core는 각 컴포넌트가 시작 시 직접 hset하므로 덮어쓰지 않는다."""
    if local_key not in SELF_HSET_EXEMPT:
        return
    if not redis_state.client or not value:
        return
    redis_key = next((rk for rk, lk in REDIS_TO_LOCAL.items() if lk == local_key), None)
    if redis_key:
        redis_state.client.hset("version", redis_key, value)

async def getVersionNew():
    """버전정보 통합 조회.
    - smartsystem, mqClient: 서비스 미존재 시 "0.0.0"으로 dict 포함 + Redis 저장
    - smartsystem: API가 최신 권위 (매번 호출), 실패 시 Redis → "1.0.0" fallback
    - 그 외: versionInfo.txt vs Redis 최신값, 둘 다 없으면 "1.0.0"
    - SmartSystems/mqClient에 한해 Redis와 다르면 갱신
    """
    file_v = _read_file_versions()
    redis_v = _read_redis_versions()
    file_exists = bool(file_v)
    result = {}

    for lk in REDIS_TO_LOCAL.values():
        # smartsystem, mqClient는 서비스 존재 확인
        if lk in SELF_HSET_EXEMPT:
            svc = LOCAL_TO_SERVICE.get(lk)
            if svc and not service_exists(svc):
                result[lk] = "0.0.0"
                if redis_v.get(lk) != "0.0.0":
                    _save_redis_version(lk, "0.0.0")
                continue

        if lk == "smartsystem":
            api_v = await _fetch_smart_api()
            if api_v:
                value = api_v
                # API가 권위. Redis와 다르면 무조건 갱신 (다운그레이드 포함)
                if redis_v.get(lk) != value:
                    _save_redis_version(lk, value)
            else:
                # API 실패: Redis와 파일 중 최신값, 둘 다 없으면 "1.0.0". Redis 갱신 안 함
                value = _latest(file_v.get(lk), redis_v.get(lk)) or "1.0.0"
            result[lk] = value
            continue

        # 그 외: 파일 vs Redis 최신
        if file_exists:
            picked = _latest(file_v.get(lk), redis_v.get(lk))
        else:
            picked = redis_v.get(lk)

        if picked:
            result[lk] = picked
            if redis_v.get(lk) != picked:
                _save_redis_version(lk, picked)
            continue

        # 둘 다 없음 - fallback
        result[lk] = "1.0.0"
        _save_redis_version(lk, "1.0.0")

    return result

def save_post(data: Post, mode: int, idx:int):
    title = data.title
    context = data.context
    mtype = data.mtype
    utype = data.utype
    f_version = data.f_version
    a_version = data.a_version
    w_version = data.w_version
    c_version = data.c_version
    smart_version = data.smart_version
    mq_version = data.mq_version
    build_version = data.build_version
    today = date.today()
    formatted = today.strftime("%Y-%m-%d")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if mode == 0:
            cursor.execute(
                "INSERT INTO `maintenance` (title,context, mtype, utype, f_version, a_version, w_version,c_version, smart_version, mq_version, build_version, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (title, context, mtype, utype, f_version,a_version,w_version, c_version,smart_version, mq_version, build_version, formatted)
            )
        else:
            cursor.execute(
                "UPDATE `maintenance` SET title=?,context=?, mtype=?, utype=?, f_version=?, a_version=?, w_version=?,c_version=?, smart_version=?, mq_version=?, build_version=?, date=? where id=?",
                (title, context, mtype, utype, f_version, a_version, w_version, c_version,smart_version, mq_version, build_version, formatted, idx )
            )
        conn.commit()
        conn.close()
        return {"passOK": "1"}
    except Exception as e:
        print(f"SAVE_POST:{str(e)} - {DB_PATH}")
        return {"passOK": "0", "msg": str(e)}


def get_lastpost():
    last_record = {}
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
                        SELECT * FROM maintenance 
                        ORDER BY id DESC 
                        LIMIT 1
                    ''')
        last_record = cursor.fetchone()
        if last_record:
            flag = True
        else:
            flag = False
        conn.close()
    except Exception as e:
        print(str(e))
        flag = False
    if flag:
        return {"result": 1, "data": dict(last_record)}
    else:
        return {"result": 0}

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

def sysService(cmd, item):
    itemdict = {
      "Redis":"redis",
      "InfluxDB":"influxdb",
      "SmartSystems":"smartsystemsservice",
      "SmartAPI":"smartsystemsrestapiservice",
      "Core":"core",
      "WebServer":"webserver",
      "A35":"sv500A35",
      "MQTTClient":"mqClient",
      "frpc":"frpc",
      "frpc-restart-monitor" : "frpc-restart-monitor"
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