from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from states.global_state import init_redis, redis_state, os_spec, cleanup_global_resources, SETTING_FOLDER
from starlette.middleware.base import BaseHTTPMiddleware
import mimetypes, os, logging, socket
from pathlib import Path
from routes import api_router
from contextlib import asynccontextmanager
import uvicorn, time, sys
from utils.RedisBinary import BinaryDataProcessor, register_waveform_config
from utils.MaxMinDataHandler import MaxMinDataHandler
from routes.setting import init_setup

sys.dont_write_bytecode = True

# ✅ MIME 타입 추가 (JS 파일 올바르게 제공)
mimetypes.add_type("application/javascript", ".js")

base_dir = Path(__file__).resolve().parent
# SETTING_FOLDER = base_dir.parent / "config"  # ⬅️ 두 단계 상위로
dist_dir = base_dir / "frontend" / "dist"
index_file = dist_dir / "index.html"


# 로그 디렉토리 설정
LOG_DIR = os_spec.logpath #"/home/root/logs"
LOG_FILE = "webserver"
MAX_LOG_SIZE_MB = 10

def setup_logging():
    """날짜별 로그 파일 생성 및 자동 관리 설정"""
    import logging.handlers
    import os
    from datetime import datetime
    
    # 로그 디렉토리 생성
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # 로거 설정
    logger = logging.getLogger()
    logger.setLevel(logging.WARNING)
    
    # 기존 핸들러 제거
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    
    # 날짜별 로그 파일 핸들러 생성
    log_filename = os.path.join(LOG_DIR, f"{LOG_FILE}_{datetime.now().strftime('%Y%m%d')}.log")
    
    # TimedRotatingFileHandler 사용 (매일 자정에 새 파일 생성, 30일 보관)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_filename,
        when='midnight',        # 매일 자정에 로테이션
        interval=1,            # 1일 간격
        backupCount=30,        # 최근 30일 파일만 보관 (31일째 되면 가장 오래된 파일 자동 삭제)
        encoding='utf-8'
    )
    
    # 로그 포맷 설정
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(file_handler)
    
    # 콘솔 출력도 추가 (선택사항)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# 로그 설정 초기화
setup_logging()

def init_binary_processor():
    """바이너리 프로세서 초기화"""
    if redis_state.client:
        # BinaryDataProcessor 생성
        redis_state.processor = BinaryDataProcessor(redis_state.client, db_num=0)

        # Waveform 설정 등록
        register_waveform_config(redis_state.processor)

        logging.info(f"Binary processor initialized with {len(redis_state.processor.configs)} configurations")
    else:
        logging.error("Redis client not initialized, cannot create binary processor")

def sd_notify(message: str) -> None:
    """systemd Type=notify 소켓으로 상태 전송. NOTIFY_SOCKET 없으면 무시."""
    addr = os.environ.get("NOTIFY_SOCKET")
    if not addr:
        return
    if addr[0] == "@":
        addr = "\0" + addr[1:]  # abstract namespace
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
            sock.connect(addr)
            sock.sendall(message.encode())
    except Exception as e:
        logging.warning(f"sd_notify failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(SETTING_FOLDER, exist_ok=True)  # 폴더가 없으면 생성
    # file_path = os.path.join(SETTING_FOLDER, 'influx.json')
    # if os.path.exists(file_path):
    #     init_influx()
    init_redis()
    init_setup()
    # await http_state.initialize()

    if redis_state.binary_client:
        redis_state.processor = BinaryDataProcessor(redis_state.binary_client, db_num=1)

        # MaxMinDataHandler 초기화 (필요한 경우)
        redis_state.handler = MaxMinDataHandler(redis_state.processor)

        # 모든 processor 설정 등록
        from utils.binary_config import setup_all_processors
        setup_all_processors(redis_state.processor)

        logging.info("Binary processor and handler initialized")

    sd_notify("READY=1")
    logging.warning("systemd READY=1 sent")

    yield  # 앱 실행

    await cleanup_global_resources()
    from routes.api import cleanup_executor
    cleanup_executor()
    # executor.shutdown(wait=True)
    # if influx_state.client:
    #     influx_state.client.close()
    # if redis_state.client:
    #     redis_state.client.close()
    # if http_state:
    #     http_state.close()

#app = FastAPI()
app = FastAPI(lifespan=lifespan)
#app.add_middleware(SessionMiddleware, secret_key="nteksystem2025_sv500")
app.add_middleware(
    SessionMiddleware,
    secret_key="nteksystem2025_sv500",
    # secret_key=secrets.token_urlsafe(32),
    same_site="lax",
    max_age=60*60   #60 * 15  # 👈 5분 (초 단위)
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000"],  # ✅ Vue.js 개발 서버 주소 (Vite 기본 포트)
    allow_credentials=True,  # ✅ 쿠키를 허용해야 세션이 유지됨!
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)
class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheMiddleware)

app.include_router(api_router)

@app.middleware("http")
async def combined_middleware(request: Request, call_next):
    print(f"📡 요청 감지됨: {request.method} {request.url.path}")

    if ("session" in request.scope and
            request.url.path.startswith("/api/")):
        try:
            if "user" in request.session:
                user = request.session.get("user")
                userRole = request.session.get("userRole")
                request.session["user"] = user
                request.session["userRole"] = userRole
        except:
            pass

    response = await call_next(request)
    return response

# ✅ `index.html`이 존재하는지 확인
if not index_file.is_file():
    raise RuntimeError(f"❌ Vue 빌드 파일이 없습니다: {index_file}")

# ✅ `/assets/...` 정적 파일 서빙 (Flask `send_from_directory(dist, path)` 대체)
app.mount("/assets", StaticFiles(directory=str(dist_dir / "assets")), name="assets")

# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     print(f"📡 요청 감지됨: {request.method} {request.url.path}")
#     response = await call_next(request)
#     return response

@app.get("/items/{item_id}", summary="Get an item", description="Get item by ID")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

# ✅ `/` 요청을 `index.html`로 제공 (Flask의 `send_from_directory()`와 동일한 동작)
@app.get("/")
async def serve_root():
    print(f"📂 루트 요청 감지됨 → {index_file}")
    if not index_file.is_file():
        print("❌ index.html 파일이 존재하지 않음!")
        return JSONResponse(content={"error": "index.html not found"}, status_code=404)

    return FileResponse(str(index_file), media_type="text/html")


# ✅ Vue Router history 모드 지원 (API 제외 모든 요청을 `index.html`로 리디렉션)
@app.get("/{path:path}")
async def catch_all(path: str):
    print(f"📂 요청된 경로: {path}")

    # ✅ `/api/...` 요청은 FastAPI에서 기본적으로 처리되도록 예외 처리
    print(f"📂 Vue Router 요청: {path}")
    if path.startswith("api/"):
        pass

    static_file_path = dist_dir / path

    # ✅ 정적 파일 요청(`/assets/...`)은 그대로 제공
    if static_file_path.exists() and static_file_path.is_file():
        return FileResponse(str(static_file_path))

    # ✅ Vue Router history 모드 지원 → 모든 경로를 `index.html`로 리디렉션
    print(f"📂 Vue Router 요청: {path} → {index_file}")
    return FileResponse(str(index_file), media_type="text/html")

if __name__ == '__main__':
    # uvicorn.run(app, host="0.0.0.0", port=4000)
    uvicorn.run(
        app,  # 모듈명:FastAPI 인스턴스 이름
        host="0.0.0.0",
        port=4000,
        workers=1,  # 워커 1개로 고정 (메모리 절약)
        http="httptools",  # 경량 HTTP 파서
    )

# if __name__ == '__main__':
#     uvicorn.run(
#         "main_fast:app",  # 모듈명:FastAPI 인스턴스 이름
#         host="0.0.0.0",
#         port=443,  # 일반적으로 HTTPS는 443이나 권한 문제로 8443 사용
#         workers=1,  # 워커 1개로 고정 (메모리 절약)
#         http="httptools",  # 경량 HTTP 파서
#         ssl_keyfile="key.pem",     # 개인키 경로
#         ssl_certfile="cert.pem",   # 인증서 경로
#     )


