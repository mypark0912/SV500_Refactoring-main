import logging
import uuid, psutil, sqlite3, os
from pathlib import Path
from datetime import date
from pydantic import BaseModel

base_dir = Path(__file__).resolve().parent
SETTING_FOLDER = base_dir.parent.parent / "config"  # ⬅️ 두 단계 상위로
DB_PATH = os.path.join(SETTING_FOLDER, "maintenance.db")

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
                date TEXT
            )
        ''')
        conn.commit()

        return conn

    except Exception as e:
        logging.error(f"DB Connection Error: {str(e)} - {DB_PATH}")
        print(f"DB Connection Error: {str(e)} - {DB_PATH}")
        raise

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
    today = date.today()
    formatted = today.strftime("%Y-%m-%d")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if mode == 0:
            cursor.execute(
                "INSERT INTO `maintenance` (title,context, mtype, utype, f_version, a_version, w_version,c_version, smart_version,date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (title, context, mtype, utype, f_version,a_version,w_version, c_version,smart_version, formatted)
            )
        else:
            cursor.execute(
                "UPDATE `maintenance` SET title=?,context=?, mtype=?, utype=?, f_version=?, a_version=?, w_version=?,c_version=?, smart_version=?, date=? where id=?",
                (title, context, mtype, utype, f_version, a_version, w_version, c_version,smart_version, formatted, idx )
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