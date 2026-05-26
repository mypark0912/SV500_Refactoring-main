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
Type=notify
NotifyAccess=main
WorkingDirectory=$APP_DIR
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=PYTHONUNBUFFERED=1
ExecStart=$SHARED_VENV_DIR/bin/python3 $MAIN_FILE
Restart=always
RestartSec=5
TimeoutStartSec=120
User=ntekadmin
Group=root
UMask=0007

[Install]
WantedBy=multi-user.target
EOF
    log_info "✅ webserver.service updated (User=ntekadmin, Type=notify)"
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
Group=root
UMask=0007
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
# 4.5 Install Boot/RTC Helpers (startup-helper, time-keeper)
# =================================================================
log_section "4.5 Install Boot/RTC Helpers"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$SCRIPT_DIR/startup-helper.sh" ]; then
    cp "$SCRIPT_DIR/startup-helper.sh" /usr/local/bin/startup-helper.sh
    chmod +x /usr/local/bin/startup-helper.sh
    log_info "✅ startup-helper.sh updated"
else
    log_warn "startup-helper.sh not found in $SCRIPT_DIR"
fi

# startup-helper.service unit 재생성 (idempotent — 손상/누락 케이스에도 보장)
cat <<EOF | sudo tee /etc/systemd/system/startup-helper.service > /dev/null
[Unit]
Description=Startup Helper for Services
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/startup-helper.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
log_info "✅ startup-helper.service unit ensured"

if [ -f "$SCRIPT_DIR/save-time.sh" ]; then
    cp "$SCRIPT_DIR/save-time.sh" /usr/local/bin/save-time.sh
    chmod +x /usr/local/bin/save-time.sh
fi
if [ -f "$SCRIPT_DIR/time-keeper.service" ]; then
    cp "$SCRIPT_DIR/time-keeper.service" /etc/systemd/system/time-keeper.service
    chmod 644 /etc/systemd/system/time-keeper.service
fi
if [ -f "$SCRIPT_DIR/time-keeper.timer" ]; then
    cp "$SCRIPT_DIR/time-keeper.timer" /etc/systemd/system/time-keeper.timer
    chmod 644 /etc/systemd/system/time-keeper.timer
fi
log_info "✅ time-keeper installed"

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

    # frpc-restart-monitor.sh: 이미 설치된 장비만 갱신 (신규 생성은 안 함)
    if [ -f /home/root/frpc-restart-monitor.sh ]; then
        if [ -f /usr/local/bin/frpc-restart-monitor.sh ]; then
            cp /home/root/frpc-restart-monitor.sh /usr/local/bin/frpc-restart-monitor.sh
            chmod +x /usr/local/bin/frpc-restart-monitor.sh
            log_info "frpc-restart-monitor.sh updated"
            if systemctl is-active --quiet frpc-restart-monitor; then
                sudo systemctl restart frpc-restart-monitor
                sudo systemctl restart frpc 2>/dev/null || true
            fi
        else
            log_warn "frpc-restart-monitor not installed on this device, skipping update"
        fi
        rm -f /home/root/frpc-restart-monitor.sh
    else
        log_warn "frpc-restart-monitor.sh not found, skipping"
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
    rm -f /home/root/frpc-restart-monitor.sh
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

# ntekadmin을 influxdb 그룹에 추가 (백업 디렉토리 쓰기 권한용)
usermod -aG influxdb $ADMIN_USER 2>/dev/null || true

# /home/root 그룹 접근 허용 (ntekadmin이 서비스 경로 진입할 수 있도록)
chmod 750 /home/root 2>/dev/null || true

# 웹서버/core/mqClient 관련 디렉토리를 770 으로 일괄 지정
# (owner/group 모두 rwx, other 차단. ntekadmin 이 root 그룹 멤버라 정상 접근)
# ownership 도 root:root 로 강제 복구 — chmod 만으로는 잘못 잡힌 owner(예: influxdb)가 풀리지 않음
sudo chown -R root:root /usr/local/sv500 2>/dev/null || true
sudo chmod -R 770       /usr/local/sv500 2>/dev/null || true
sudo chown -R root:root /home/root/webserver 2>/dev/null || true
sudo chmod -R 770       /home/root/webserver 2>/dev/null || true
sudo chown -R root:root /home/root/core 2>/dev/null || true
sudo chmod -R 770       /home/root/core 2>/dev/null || true
sudo chown -R root:root /home/root/mqClient 2>/dev/null || true
sudo chmod -R 770       /home/root/mqClient 2>/dev/null || true
sudo chown -R root:root /home/root/config 2>/dev/null || true
sudo chmod -R 770       /home/root/config 2>/dev/null || true

# 네트워크/시간동기 설정: webserver(ntekadmin, root 그룹)가 직접 접근.
#  - *.network      : 비교용 read (쓰기는 sudo 경유)
#  - timesyncd.conf : sudo 없이 직접 read/write
# ntekadmin 이 root 그룹 멤버이므로 그룹 권한만 부여. 실행 비트 불필요.
# 664 = owner rw / group rw / other r
chmod 664 /etc/systemd/network/*.network 2>/dev/null || true
chmod 664 /etc/systemd/timesyncd.conf    2>/dev/null || true

# /usr/local/sv500/backup : core(root) 와 webserver(ntekadmin, root그룹) 가 공유하는 작업 디렉토리.
# 존재 시 그룹 쓰기 + setgid 부여 → ntekadmin 이 report input/progress/docx 기록 가능.
if [ -d /usr/local/sv500/backup ]; then
    chgrp -R root /usr/local/sv500/backup 2>/dev/null || true
    chmod -R g+w  /usr/local/sv500/backup 2>/dev/null || true
    find /usr/local/sv500/backup -type d -exec chmod g+s {} \; 2>/dev/null || true
    log_info "✅ Permissions granted: /usr/local/sv500/backup (group-writable + setgid)"
else
    log_info "ℹ️  /usr/local/sv500/backup not found (skip)"
fi

# InfluxDB 백업 디렉토리는 influxdb 사용자 소유로 복원
# (위 chown -R root:root + chgrp -R root /backup 가 덮어쓴 것을 되돌림)
if [ -d /usr/local/sv500/backup/influxdb ]; then
    sudo chown -R influxdb:influxdb /usr/local/sv500/backup/influxdb 2>/dev/null || true
    sudo chmod 775                  /usr/local/sv500/backup/influxdb 2>/dev/null || true
    log_info "✅ Ownership restored: /usr/local/sv500/backup/influxdb (influxdb:influxdb, 775)"
fi


log_section "6. Reload systemd and Restart Services"

sudo chmod +x /home/root/SV500/fw_cortex_m33.sh
sudo chmod +x /home/root/bin/SV500_CA35


sudo systemctl daemon-reload

# Enable 정책 조정 (webserver / sv500A35는 startup-helper가 시작하므로 disable)
sudo systemctl disable webserver.service 2>/dev/null || true
sudo systemctl disable sv500A35.service  2>/dev/null || true

# 불필요한 서비스 disable (snmpd: 시작 실패로 부팅 90초 timeout 유발)
sudo systemctl stop    snmpd      2>/dev/null || true
sudo systemctl disable snmpd      2>/dev/null || true
sudo systemctl stop    snmptrapd  2>/dev/null || true
sudo systemctl disable snmptrapd  2>/dev/null || true
log_info "✅ snmpd/snmptrapd disabled"

# startup-helper.service enable (idempotent — 이미 enable이면 무해)
sudo systemctl enable startup-helper.service 2>/dev/null || true
log_info "✅ startup-helper.service enabled"

# time-keeper.timer enable + start (RTC reset recovery용 heartbeat)
sudo systemctl enable time-keeper.timer 2>/dev/null || true
sudo systemctl start  time-keeper.timer 2>/dev/null || true
log_info "✅ time-keeper.timer enabled"

log_info "Starting sv500A35..."
sudo systemctl start sv500A35
sleep 3

log_info "Starting webserver..."
sudo systemctl restart webserver
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