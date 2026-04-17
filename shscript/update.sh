#!/bin/sh

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo ""
    echo "=================================================="
    echo " $1"
    echo "=================================================="
}

# =================================================================
# 옵션 파싱 (기본값: local)
# Usage: ./update_shared_venv.sh [--local|--lte]
# =================================================================
MODE="local"
while [ "$#" -gt 0 ]; do
  case $1 in
    --lte)
      MODE="lte"
      ;;
    --local)
      MODE="local"
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--local|--lte]"
      exit 1
      ;;
  esac
  shift
done

log_info "Update mode: $MODE"

# =================================================================
# 0. ntekadmin 사용자 확인 및 생성
# =================================================================
log_section "0. Check ntekadmin User"

ADMIN_USER="ntekadmin"
ADMIN_PASS="Ntek@dmin2026!"
ROOT_PASS="@dmin@Ntek2026!"

if id "$ADMIN_USER" &>/dev/null; then
    log_info "User $ADMIN_USER already exists"
else
    log_info "Creating user $ADMIN_USER..."
    useradd -m -s /bin/bash "$ADMIN_USER"
    echo "$ADMIN_USER:$ADMIN_PASS" | chpasswd
    log_info "User $ADMIN_USER created (change password after first login)"
fi

# root 비밀번호 설정 (매번 덮어써서 일관성 유지)
echo "root:$ROOT_PASS" | chpasswd
log_info "root password set"

# sudoers 설정
SUDOERS_SRC="$(dirname "$0")/sv500-sudoers"
SUDOERS_DST="/etc/sudoers.d/sv500-web"

if [ -f "$SUDOERS_SRC" ]; then
    cp "$SUDOERS_SRC" "$SUDOERS_DST"
    chmod 440 "$SUDOERS_DST"
    chown root:root "$SUDOERS_DST"
    log_info "Sudoers file installed: $SUDOERS_DST"
    # 업로드본 정리 (이미 /etc/sudoers.d/ 에 복사 완료)
    rm -f "$SUDOERS_SRC"
else
    log_warn "Sudoers file not found: $SUDOERS_SRC"
fi

# =================================================================
# 경로 정의
# =================================================================
APP_DIR=/home/root/webserver
CORE_DIR=/home/root/core
SHARED_VENV_DIR=/home/root/shared_venv
MAIN_FILE=main_linux.py

OFFLINE_DIR="/home/root/offline_package"
PIP_PACKAGE_DIR="/home/root/offline_package/packages/pip"

# =================================================================
# shared_venv 존재 여부 확인
# =================================================================
if [ -d "$SHARED_VENV_DIR" ]; then
    log_info "shared_venv already exists → Skipping venv steps (sections 2, 3)"
    SKIP_VENV=true
else
    log_info "shared_venv not found → Will create shared_venv (fresh)"
    SKIP_VENV=false

    # pip 패키지 디렉토리 확인 (venv 설치 시에만 필요)
    if [ ! -d "$PIP_PACKAGE_DIR" ]; then
        log_warn "pip directory not found, checking python directory..."
        PIP_PACKAGE_DIR="$OFFLINE_DIR/packages/python"
        if [ ! -d "$PIP_PACKAGE_DIR" ]; then
            log_error "No package directory found! Cannot install pip packages."
            exit 1
        fi
    fi
fi

# =================================================================
# 1. 서비스 중지
# =================================================================
log_section "1. Stop Services"

log_info "Stopping webserver and core services..."
sudo systemctl stop webserver 2>/dev/null || true
sudo systemctl stop core 2>/dev/null || true
sleep 2
log_info "✅ Services stopped"

# =================================================================
# 2. 기존 개별 venv 삭제 (폴더 존재 시 무조건 삭제)
# =================================================================
log_section "2. Remove Old Virtual Environments"

if [ -d "$APP_DIR/venv" ]; then
    log_info "Removing $APP_DIR/venv ..."
    rm -rf "$APP_DIR/venv"
    log_info "✅ Removed $APP_DIR/venv"
else
    log_warn "$APP_DIR/venv not found, skipping"
fi

if [ -d "$CORE_DIR/venv" ]; then
    log_info "Removing $CORE_DIR/venv ..."
    rm -rf "$CORE_DIR/venv"
    log_info "✅ Removed $CORE_DIR/venv"
else
    log_warn "$CORE_DIR/venv not found, skipping"
fi

# =================================================================
# 3. 공유 가상환경 생성 및 패키지 설치 (shared_venv 없을 때만)
# =================================================================
if [ "$SKIP_VENV" = false ]; then

log_section "3. Create Shared Virtual Environment"

log_info "Creating shared virtual environment at $SHARED_VENV_DIR ..."
python3 -m venv "$SHARED_VENV_DIR"
source "$SHARED_VENV_DIR/bin/activate"

# pip 업그레이드 (오프라인)
log_info "Upgrading pip..."
"$SHARED_VENV_DIR/bin/pip" install --no-index --find-links "$PIP_PACKAGE_DIR" \
    pip setuptools wheel 2>/dev/null || log_warn "pip upgrade failed"

# pip_install.json 파일 찾기
JSON_FILE=""
if [ -f "$OFFLINE_DIR/configs/pip_install.json" ]; then
    JSON_FILE="$OFFLINE_DIR/configs/pip_install.json"
    log_info "Found: $OFFLINE_DIR/configs/pip_install.json"
elif [ -f "$APP_DIR/pip_install.json" ]; then
    JSON_FILE="$APP_DIR/pip_install.json"
    log_info "Found: $APP_DIR/pip_install.json"
elif [ -f "$CORE_DIR/pip_install.json" ]; then
    JSON_FILE="$CORE_DIR/pip_install.json"
    log_info "Found: $CORE_DIR/pip_install.json"
fi

if [ -n "$JSON_FILE" ]; then
    log_info "Installing packages from pip_install.json..."

    DEPS=$(python3 -c "
import json
with open('$JSON_FILE') as f:
    data = json.load(f)
print(' '.join(data.get('dependencies', [])))
")

    log_info "Packages to install: $DEPS"

    for package in $DEPS; do
        if [ -n "$package" ] && [ "$package" != "asyncio" ]; then
            log_info "Installing $package..."
            "$SHARED_VENV_DIR/bin/pip" install --no-index --find-links "$PIP_PACKAGE_DIR" "$package" 2>/dev/null || {
                log_warn "Failed to install $package, trying without deps..."
                "$SHARED_VENV_DIR/bin/pip" install --no-index --find-links "$PIP_PACKAGE_DIR" --no-deps "$package" 2>/dev/null || true
            }
        fi
    done
else
    log_error "pip_install.json not found! pip packages were not installed."
fi

# 설치 확인
log_info "Verifying installation..."
"$SHARED_VENV_DIR/bin/pip" list | grep -E "fastapi|uvicorn|pandas|influxdb|redis" || true

deactivate

log_info "✅ Shared virtual environment setup complete: $SHARED_VENV_DIR"

fi # SKIP_VENV

# 오프라인 패키지 폴더 삭제 (shared_venv 존재 여부와 무관하게 항상 삭제)
if [ -d "$OFFLINE_DIR" ]; then
    log_info "Removing offline package directory..."
    rm -rf "$OFFLINE_DIR"
    log_info "✅ Removed $OFFLINE_DIR"
fi

# =================================================================
# 4. 서비스 파일 업데이트 (ExecStart 경로 수정)
# =================================================================
log_section "4. Update Service Files"

# --- webserver.service ---
if [ -d "$APP_DIR" ]; then
    log_info "Updating webserver.service ..."
    cat <<EOF > /etc/systemd/system/webserver.service
[Unit]
Description=FastAPI Web Server
After=network.target redis.service influxdb.service
Wants=redis.service

[Service]
WorkingDirectory=$APP_DIR
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=PYTHONUNBUFFERED=1
ExecStart=$SHARED_VENV_DIR/bin/python3 $MAIN_FILE
Restart=always
RestartSec=5
User=ntekadmin

[Install]
WantedBy=multi-user.target
EOF
    log_info "✅ webserver.service updated (User=ntekadmin)"
else
    log_warn "Webserver directory not found: $APP_DIR — skipping service update"
fi

# --- core.service ---
if [ -d "$CORE_DIR" ]; then
    log_info "Updating core.service ..."
    cat <<EOF > /etc/systemd/system/core.service
[Unit]
Description=SV500 Core
After=network.target influxdb.service redis.service webserver.service
Wants=

[Service]
ExecStartPre=/bin/sleep 5
ExecStart=$SHARED_VENV_DIR/bin/python3 main.py
WorkingDirectory=$CORE_DIR
Environment=PYTHONDONTWRITEBYTECODE=1
Restart=always
User=ntekadmin
SyslogLevel=err
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    log_info "✅ core.service updated (User=ntekadmin)"
else
    log_warn "Core directory not found: $CORE_DIR — skipping service update"
fi

# =================================================================
# 5. FRP 터널링 & Firewall (모드에 따라 처리)
# =================================================================
log_section "5. FRP Tunnel & Firewall Setup"

if [ "$MODE" = "lte" ]; then
    log_info "LTE mode: Installing FRP tunnel and Firewall..."

    if [ -f /home/root/firewall.sh ]; then
        mv /home/root/firewall.sh /opt/firewall.sh
        chmod +x /opt/firewall.sh
    else
        log_warn "firewall.sh not found, skipping"
    fi

    if [ -f /home/root/firewall.service ]; then
        mv /home/root/firewall.service /etc/systemd/system/firewall.service
    else
        log_warn "firewall.service not found, skipping"
    fi

    sudo systemctl daemon-reload
    sudo systemctl enable firewall.service 2>/dev/null || true
    sudo systemctl start firewall.service 2>/dev/null || true

    log_info "✅ FRP & Firewall installed (LTE mode)"
else
    log_info "Local mode: Removing FRP and Firewall files..."
    rm -f /home/root/frp_0.66.0_linux_arm64.tar.gz
    rm -f /home/root/firewall.sh
    rm -f /home/root/firewall.service
    log_info "✅ FRP & Firewall skipped (Local mode)"
fi

# =================================================================
# 6. systemd 리로드 및 서비스 재시작
# =================================================================
rm -rf /usr/local/sv500/iss
mv /home/root/iss /usr/local/sv500/iss
sudo chmod +x /home/root/SV500/install.sh

# ntekadmin을 root 그룹에 추가 (디렉토리 접근용)
usermod -aG root $ADMIN_USER 2>/dev/null || true

# /home/root 그룹 접근 허용 (ntekadmin이 서비스 경로 진입할 수 있도록)
chmod 750 /home/root 2>/dev/null || true

# 웹서버/core/mqClient 관련 디렉토리를 770 으로 일괄 지정
# (owner/group 모두 rwx, other 차단. ntekadmin 이 root 그룹 멤버라 정상 접근)
chmod -R 770 /usr/local/sv500 2>/dev/null || true
chmod -R 770 /home/root/webserver 2>/dev/null || true
chmod -R 770 /home/root/core 2>/dev/null || true
chmod -R 770 /home/root/mqClient 2>/dev/null || true

# config 폴더 및 db/json/csv 파일에 그룹 쓰기 권한 부여
# (기존 root 소유 파일을 ntekadmin 이 root 그룹 멤버로 쓸 수 있도록)
# SQLite 가 .db-journal / .db-wal 파일 생성하려면 디렉토리 g+w 필수
if [ -d /home/root/config ]; then
    chmod 775 /home/root/config 2>/dev/null || true
    find /home/root/config -maxdepth 1 -type f \
        \( -name "*.db" -o -name "*.json" -o -name "*.csv" \) \
        -exec chmod g+w {} \; 2>/dev/null || true
    log_info "✅ Group write permission granted to /home/root/config (folder + db/json/csv)"
fi

log_section "6. Reload systemd and Restart Services"

sudo chmod +x /home/root/SV500/fw_cortex_m33.sh
sudo chmod +x /home/root/bin/SV500_CA35


sudo systemctl daemon-reload
log_info "Starting sv500A35..."
sudo systemctl start sv500A35
sleep 3

log_info "Starting webserver..."
sudo systemctl start webserver
sleep 3

log_info "Starting core..."
sudo systemctl start core
sleep 2

# 상태 확인
log_info "Service status:"
systemctl is-active webserver && log_info "✅ webserver: running" || log_warn "⚠️  webserver: not running"
systemctl is-active core     && log_info "✅ core:      running" || log_warn "⚠️  core:      not running"

# =================================================================
# 완료
# =================================================================
echo ""
log_info "✅ Update complete!"
echo ""
echo "=== Summary ==="
if [ "$SKIP_VENV" = false ]; then
echo "- Removed : $APP_DIR/venv"
echo "- Removed : $CORE_DIR/venv"
echo "- Created : $SHARED_VENV_DIR"
echo "- Removed : $OFFLINE_DIR"
else
echo "- shared_venv : already existed (skipped)"
fi
echo "- Updated : /etc/systemd/system/webserver.service"
echo "- Updated : /etc/systemd/system/core.service"
echo "- Update mode: $MODE"
if [ "$MODE" = "lte" ]; then
echo "- FRP Tunnel & Firewall: applied"
fi
echo ""

# =================================================================
# 스크립트 자기 자신 삭제 (업데이트 완료 후 정리)
# =================================================================
log_info "Cleaning up update script..."
rm -f "$0"