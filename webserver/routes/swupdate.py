"""
swupdate.py — 웹 업로드 SW 업데이트 적용자 (Python).

Go 기기 웹서버(swupdate.go)의 Python 판. Python 장비용.
통합서버 packager.py 와 동일 규약:
  - 무결성: 파일 SHA-256 + manifest HMAC-SHA256
  - canonical = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",",":"))
    → 반드시 표준 json (ujson 아님). 그래야 packager 서명과 일치.

흐름:
  1) POST /swupdate/upload — 패키지(.tar.gz) 업로드 → staged 추출 → HMAC+해시 검증 (러너 안 돔)
  2) POST /swupdate/apply  — systemd-run 러너(웹서버 cgroup 밖) → updateSW.sh → 정리 → reboot

경로(Go 와 동일):
  /usr/local/sv500/swupdate/{incoming.tar.gz, staged/, hmac.key, staged/updateSW.sh}
"""
from fastapi import APIRouter, UploadFile, File
import os
import json   # 표준 json — packager.py 와 canonical 일치 (ujson 금지)
import hmac
import hashlib
import shutil
import tarfile
import logging
import subprocess

router = APIRouter()
logger = logging.getLogger(__name__)

SW_BASE = "/usr/local/sv500/swupdate"
SW_INCOMING = os.path.join(SW_BASE, "incoming.tar.gz")
SW_STAGED = os.path.join(SW_BASE, "staged")
SW_HMAC_KEY = os.path.join(SW_BASE, "hmac.key")
SW_SCRIPT = os.path.join(SW_STAGED, "updateSW.sh")
SW_MAX_UPLOAD = 1 << 30          # 1GiB 상한
_CHUNK = 4 * 1024 * 1024


# ----------------------------------------------------------------------------
# 검증 유틸 (packager.py 와 동일)
# ----------------------------------------------------------------------------
def _load_hmac_key() -> bytes:
    try:
        with open(SW_HMAC_KEY, "r", encoding="utf-8") as f:
            k = f.read().strip()
    except OSError:
        raise ValueError(f"HMAC 키 없음({SW_HMAC_KEY}) — 통합서버와 동일 키 주입 필요")
    if not k:
        raise ValueError("HMAC 키 비어있음")
    return k.encode("utf-8")


def _canonical(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_extract(tar_path: str, dest: str):
    """tar.gz 안전 추출 (path traversal 차단, 링크 무시)."""
    dest_abs = os.path.realpath(dest)
    os.makedirs(dest_abs, exist_ok=True)
    with tarfile.open(tar_path, "r:gz") as tar:
        for m in tar.getmembers():
            if m.issym() or m.islnk():
                continue
            target = os.path.realpath(os.path.join(dest_abs, m.name))
            if target != dest_abs and not target.startswith(dest_abs + os.sep):
                raise ValueError(f"잘못된 경로(탈출 시도): {m.name}")
            tar.extract(m, dest_abs)


def _verify(staged: str):
    """manifest HMAC + 파일별 SHA-256 검증. 실패 시 ValueError."""
    mf_path = os.path.join(staged, "manifest.json")
    if not os.path.isfile(mf_path):
        raise ValueError("manifest.json 없음")
    with open(mf_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # (a) HMAC 검증 — "hmac" 제외 본문 canonical
    sig = manifest.get("hmac")
    if not sig:
        raise ValueError("manifest 에 hmac 없음")
    body = dict(manifest)
    body.pop("hmac", None)
    key = _load_hmac_key()
    calc = hmac.new(key, _canonical(body), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc, str(sig)):
        raise ValueError("서명(HMAC) 불일치 — 변조되었거나 키가 다릅니다")

    # (b) 파일별 SHA-256
    files = manifest.get("files") or {}
    if not files:
        raise ValueError("manifest 에 files 없음")
    for rel, want in files.items():
        p = os.path.join(staged, rel)
        if not os.path.isfile(p):
            raise ValueError(f"파일 누락: {rel}")
        if _sha256_file(p).lower() != str(want).lower():
            raise ValueError(f"해시 불일치: {rel}")


def _cleanup():
    shutil.rmtree(SW_STAGED, ignore_errors=True)
    try:
        os.remove(SW_INCOMING)
    except OSError:
        pass


# ----------------------------------------------------------------------------
# 라우트
# ----------------------------------------------------------------------------
@router.post("/upload")
async def sw_upload(file: UploadFile = File(...)):
    """패키지 업로드 + 검증 + 스테이징 (러너는 /apply 에서)."""
    if not file or not file.filename:
        return {"success": False, "error": "업로드 파일이 없습니다."}
    try:
        os.makedirs(SW_BASE, exist_ok=True)
        # 이전 잔재 정리
        shutil.rmtree(SW_STAGED, ignore_errors=True)
        try:
            os.remove(SW_INCOMING)
        except OSError:
            pass

        # 업로드 저장 (스트리밍, 상한 체크)
        total = 0
        with open(SW_INCOMING, "wb") as out:
            while True:
                chunk = await file.read(_CHUNK)
                if not chunk:
                    break
                total += len(chunk)
                if total > SW_MAX_UPLOAD:
                    raise ValueError("파일이 너무 큽니다 (>1GiB)")
                out.write(chunk)

        # 추출 → 검증
        _safe_extract(SW_INCOMING, SW_STAGED)
        _verify(SW_STAGED)

        if not os.path.isfile(SW_SCRIPT):
            _cleanup()
            return {"success": False, "error": "updateSW.sh 가 패키지에 없습니다."}
        os.chmod(SW_SCRIPT, 0o755)

        return {"success": True, "message": "패키지 검증·준비 완료."}
    except ValueError as e:
        _cleanup()
        return {"success": False, "error": f"무결성 검증 실패: {e}"}
    except Exception as e:
        logger.exception("sw_upload 실패")
        _cleanup()
        return {"success": False, "error": f"업로드 실패: {e}"}


@router.post("/apply")
async def sw_apply():
    """스테이징·검증된 패키지 적용. SmartSystem 업데이트가 끝난 뒤(러너 전) 호출.
    updateSW.sh 를 웹서버 cgroup 밖(systemd-run)에서 실행 → 정리 → reboot."""
    if not os.path.isfile(SW_SCRIPT):
        return {"success": False, "error": "준비된 패키지가 없습니다. 먼저 업로드하세요."}
    os.chmod(SW_SCRIPT, 0o755)

    run_script = "{s}; rm -rf {st} {inc}; systemctl reboot".format(
        s=SW_SCRIPT, st=SW_STAGED, inc=SW_INCOMING)
    try:
        subprocess.run(
            ["sudo", "systemd-run", "--no-block", "--collect",
             "--unit=sv500-swupdate", "/bin/sh", "-c", run_script],
            check=True, timeout=20)
    except Exception as e:
        return {"success": False, "error": f"적용 시작 실패: {e}"}

    return {"success": True, "message": "업데이트를 적용합니다. 곧 재부팅됩니다."}
