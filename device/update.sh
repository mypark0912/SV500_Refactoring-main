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
# 옵션 파싱 (기본값: local --rtc0)
# Usage: ./update.sh [--local|--lte] [--rtc0|--rtc1|--nosavertc|--nosavertc1] [--switch|--noswitch]
#   --rtc0       : rtc0 사용, 시간 저장/복원 O (default)
#   --rtc1       : rtc1 사용, 시간 저장/복원 O
#   --nosavertc  : rtc0 사용, 시간 저장/복원 X
#   --nosavertc1 : rtc1 사용, 시간 저장/복원 X
#   --switch     : 스위치 모드 (init-tsn.service 활성화)
#   --noswitch   : 일반 모드, init-tsn 비활성화 (default)
# (docker mode는 update.sh 대상 아님 — 컨테이너에서 직접 SV500_MODE=3 설정)
# =================================================================
MODE="local"
DEVICE_MODE=0   # 0=linux rtc0, 1=linux rtc1 (webserver SV500_MODE와 일치)
NOSAVE_RTC=0    # 1이면 time-keeper 제외 + startup-monitor 의 RTC 복구도 skip
SWITCH_MODE=0   # 1이면 스위치 모드 (init-tsn.service enable)
while [ "$#" -gt 0 ]; do
  case $1 in
    --lte)
      MODE="lte"
      ;;
    --local)
      MODE="local"
      ;;
    --rtc0)
      DEVICE_MODE=0; NOSAVE_RTC=0
      ;;
    --rtc1)
      DEVICE_MODE=1; NOSAVE_RTC=0
      ;;
    --nosavertc)
      DEVICE_MODE=0; NOSAVE_RTC=1
      ;;
    --nosavertc1)
      DEVICE_MODE=1; NOSAVE_RTC=1
      ;;
    --switch)
      SWITCH_MODE=1
      ;;
    --noswitch)
      SWITCH_MODE=0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--local|--lte] [--rtc0|--rtc1|--nosavertc|--nosavertc1] [--switch|--noswitch]"
      exit 1
      ;;
  esac
  shift
done

# RTC 디바이스 옵션
if [ "$DEVICE_MODE" = "1" ]; then
    HWCLOCK_OPTS="-f /dev/rtc1"
else
    HWCLOCK_OPTS=""
fi

log_info "Update mode: network=$MODE, device=$DEVICE_MODE, switch=$SWITCH_MODE (hwclock opts: '$HWCLOCK_OPTS')"

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
After=startup-monitor.service redis.service
Wants=influxdb.service

[Service]
Type=notify
NotifyAccess=main
WorkingDirectory=$APP_DIR
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=PYTHONUNBUFFERED=1
Environment=SV500_MODE=$DEVICE_MODE
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
    log_info "✅ webserver.service updated (User=ntekadmin, Type=notify, SV500_MODE=$DEVICE_MODE)"
else
    log_warn "Webserver directory not found: $APP_DIR — skipping service update"
fi

# --- core.service ---
if [ -d "$CORE_DIR" ]; then
    log_info "Updating core.service ..."
    cat <<EOF > /etc/systemd/system/core.service
[Unit]
Description=SV500 Core
After=webserver.service influxdb.service
Wants=smartsystemsrestapiservice.service

[Service]
ExecStart=$SHARED_VENV_DIR/bin/python3 main.py
WorkingDirectory=$CORE_DIR
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=SV500_MODE=$DEVICE_MODE
Restart=always
User=root
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    log_info "✅ core.service updated (After=webserver,influxdb / Wants=smartsystemsrestapiservice / SV500_MODE=$DEVICE_MODE)"
else
    log_warn "Core directory not found: $CORE_DIR — skipping service update"
fi

# =================================================================
# 4.5 Install Boot Orchestrator (startup-monitor, time-keeper)
# =================================================================
log_section "4.5 Install Boot Orchestrator"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 옛 startup-helper 잔재 정리 (startup-monitor 로 일원화됨)
sudo systemctl stop    startup-helper.service 2>/dev/null || true
sudo systemctl disable startup-helper.service 2>/dev/null || true
sudo rm -f /etc/systemd/system/startup-helper.service
sudo rm -f /usr/local/bin/startup-helper.sh

# startup-monitor.sh 는 별도 파일 안 두고 옵션에 맞게 직접 생성
cat > /usr/local/bin/startup-monitor.sh <<MONITOR_EOF
#!/bin/bash
# Auto-generated by install.sh / update.sh
# DEVICE_MODE=$DEVICE_MODE  NOSAVE_RTC=$NOSAVE_RTC  SWITCH_MODE=$SWITCH_MODE  HWCLOCK_OPTS="$HWCLOCK_OPTS"

NOSAVE_RTC=$NOSAVE_RTC
SWITCH_MODE=$SWITCH_MODE
HWCLOCK_OPTS="$HWCLOCK_OPTS"

LOG="/usr/local/sv500/logs/startup-monitor.log"
TIME_FILE="/usr/local/sv500/last_known_time"
MARKER="/usr/local/sv500/clean_shutdown"
RESET_THRESHOLD=86400          # 24h
MIN_VALID_EPOCH=1704067200     # 2024-01-01

log() { echo "[\$(date '+%Y-%m-%d %H:%M:%S')] \$*" >> "\$LOG"; }

while ! mountpoint -q /usr/local; do
    sleep 1
done

mkdir -p "\$(dirname "\$LOG")"

log "===== Boot started (NOSAVE_RTC=\$NOSAVE_RTC HWCLOCK_OPTS='\$HWCLOCK_OPTS') ====="

# Signal A: system time
NOW=\$(date +%s)
log "A. system time : \$(date) (epoch=\$NOW)"

# Signal B: hardware RTC value
HW_RTC=\$(hwclock -r \$HWCLOCK_OPTS 2>/dev/null || echo "N/A")
log "B. hwclock -r  : \$HW_RTC"

# Signal C: last known time (only when save/restore enabled)
LAST_KNOWN=0
if [ "\$NOSAVE_RTC" = "1" ]; then
    log "C. RTC recovery: disabled (nosavertc mode)"
elif [ -f "\$TIME_FILE" ]; then
    LAST_KNOWN=\$(cat "\$TIME_FILE" 2>/dev/null || echo 0)
    log "C. last_known  : \$(date -d @\$LAST_KNOWN 2>/dev/null || echo invalid) (epoch=\$LAST_KNOWN)"
else
    log "C. last_known  : <file not found>"
fi

# Signal D: clean shutdown marker
if [ -f "\$MARKER" ]; then
    SHUTDOWN_KIND="clean"
    rm -f "\$MARKER"
else
    SHUTDOWN_KIND="UNEXPECTED"
fi
log "D. prev shutdown: \$SHUTDOWN_KIND"

# Reset detection (only when save/restore enabled)
RESET_DETECTED=0
if [ "\$NOSAVE_RTC" != "1" ]; then
    if [ "\$LAST_KNOWN" -gt 0 ]; then
        DIFF=\$((LAST_KNOWN - NOW))
        if [ "\$DIFF" -gt "\$RESET_THRESHOLD" ]; then
            log "→ RTC RESET DETECTED: system time is \${DIFF}s (>=24h) before last_known"
            RESET_DETECTED=1
        else
            log "→ Time looks consistent (diff=\${DIFF}s vs last_known)"
        fi
    elif [ "\$NOW" -lt "\$MIN_VALID_EPOCH" ]; then
        log "→ RTC RESET SUSPECTED: no last_known and system time before 2024-01-01"
    fi
fi

# Time recovery
TIME_RECOVERED=0
if [ "\$RESET_DETECTED" = "1" ] && [ "\$LAST_KNOWN" -gt 0 ]; then
    log "→ Restoring time from last_known"
    date -s "@\$LAST_KNOWN" >/dev/null 2>&1
    hwclock --systohc \$HWCLOCK_OPTS 2>/dev/null || true
    log "   restored system : \$(date)"
    log "   restored hwclock: \$(hwclock -r \$HWCLOCK_OPTS 2>/dev/null || echo N/A)"
    TIME_RECOVERED=1
fi

# Prepare Redis runtime directory
mkdir -p /var/run/redis
chown redis:redis /var/run/redis 2>/dev/null || true

# Restart redis/influxdb if time was recovered
if [ "\$TIME_RECOVERED" = "1" ]; then
    log "→ Restarting redis and influxdb to apply corrected time"
    systemctl restart redis 2>/dev/null || true
    systemctl restart influxdb 2>/dev/null || true
fi

# Switch mode: 자동 부여된 관리 IP 제거 후 네트워크 재시작
if [ "\$SWITCH_MODE" = "1" ]; then
    log "→ Switch mode: removing auto-assigned IP (192.168.0.10/32 on sw0ep)"
    ip addr del 192.168.0.10/32 dev sw0ep 2>/dev/null || true
    log "→ Restarting systemd-networkd"
    systemctl restart systemd-networkd 2>/dev/null || true
fi

log "===== Boot logging done ====="
MONITOR_EOF
chmod +x /usr/local/bin/startup-monitor.sh
log_info "✅ startup-monitor.sh generated (DEVICE_MODE=$DEVICE_MODE NOSAVE_RTC=$NOSAVE_RTC)"

# startup-monitor.service unit 재생성 (boot 로깅 + RTC 복구)
# After=multi-user.target 은 cycle 만들기 때문에 절대 쓰면 안 됨
# After=redis/influxdb 도 불필요 (스크립트가 systemctl restart 만 호출, ping 안 함)
cat <<EOF | sudo tee /etc/systemd/system/startup-monitor.service > /dev/null
[Unit]
Description=Boot Logger and RTC Recovery
After=network.target local-fs.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/startup-monitor.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
log_info "✅ startup-monitor.service unit ensured"

# influxdb.service drop-in: TMPDIR 디렉토리 자동 생성 보장
# (TMPDIR=/usr/local/sv500/backup/influxdb 가 없으면 backup metadata snapshot 실패)
sudo mkdir -p /etc/systemd/system/influxdb.service.d
sudo tee /etc/systemd/system/influxdb.service.d/tmpdir.conf > /dev/null <<'DROPIN'
[Service]
ExecStartPre=/bin/mkdir -p /usr/local/sv500/backup/influxdb
ExecStartPre=/bin/chown influxdb:influxdb /usr/local/sv500/backup/influxdb
DROPIN
log_info "✅ influxdb.service drop-in (TMPDIR auto-create) 적용"

# shutdown-marker.service 재생성 — 마커를 /usr/local/sv500 (영구) 으로 이동
# (이전 버전은 /var/run에 마커 → tmpfs라 reboot 시 휘발 → 항상 UNEXPECTED 판정)
# Conflicts + ExecStop 패턴: 부팅 시 active 유지 → 종료 target 진입 시 stop → ExecStop으로 마커 생성
cat <<EOF | sudo tee /etc/systemd/system/shutdown-marker.service > /dev/null
[Unit]
Description=Create clean shutdown marker
DefaultDependencies=no
Before=shutdown.target reboot.target halt.target
Conflicts=shutdown.target reboot.target halt.target
RequiresMountsFor=/usr/local

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/true
ExecStop=/bin/touch /usr/local/sv500/clean_shutdown

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable shutdown-marker.service 2>/dev/null || true
log_info "✅ shutdown-marker.service ensured (marker at /usr/local/sv500/clean_shutdown)"

# shutdown-monitor.sh의 MARKER_FILE 경로도 일치시킴 (기존 설치본 patch)
if [ -f /usr/local/bin/shutdown-monitor.sh ]; then
    sudo sed -i 's|MARKER_FILE="/var/run/clean_shutdown"|MARKER_FILE="/usr/local/sv500/clean_shutdown"|' /usr/local/bin/shutdown-monitor.sh
    log_info "✅ shutdown-monitor.sh MARKER_FILE path updated"
fi

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

# Install init-tsn (스위치 모드 TSN/STP daisy chain 초기화 — systemd-networkd 이후 1회 실행)
if [ -f "$SCRIPT_DIR/init-tsn.sh" ]; then
    cp "$SCRIPT_DIR/init-tsn.sh" /usr/local/bin/init-tsn.sh
    chmod +x /usr/local/bin/init-tsn.sh
fi
if [ -f "$SCRIPT_DIR/init-tsn.service" ]; then
    cp "$SCRIPT_DIR/init-tsn.service" /etc/systemd/system/init-tsn.service
    chmod 644 /etc/systemd/system/init-tsn.service
fi
log_info "✅ init-tsn installed"

# Install rtc-sync (DEVICE_MODE=1 → boot 시 /dev/rtc1 → 시스템 클럭 초기화)
# 기본 systemd는 /dev/rtc0 에서 클럭을 가져오므로 rtc1 사용 시 반드시 필요
if [ "$DEVICE_MODE" = "1" ]; then
    cat <<'EOF' | sudo tee /usr/local/bin/rtc-sync.sh > /dev/null
#!/bin/sh
# Sync /dev/rtc1 hardware clock to system clock at boot.
RTC_DEV="/dev/rtc1"
LOG_DIR="/usr/local/sv500/logs"
LOG_FILE="$LOG_DIR/rtc-sync.log"
mkdir -p "$LOG_DIR" 2>/dev/null || true
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE" 2>/dev/null; }
[ -e "$RTC_DEV" ] || { log "skip: $RTC_DEV not found"; exit 0; }
BEFORE=$(date '+%Y-%m-%d %H:%M:%S')
HW=$(hwclock -r -f "$RTC_DEV" 2>/dev/null || echo "N/A")
if /sbin/hwclock --hctosys -f "$RTC_DEV" 2>/dev/null; then
    log "ok: sys($BEFORE) <- rtc($HW) => sys($(date '+%Y-%m-%d %H:%M:%S'))"
else
    log "fail: hwclock --hctosys -f $RTC_DEV"
    exit 1
fi
EOF
    sudo chmod +x /usr/local/bin/rtc-sync.sh

    cat <<EOF | sudo tee /etc/systemd/system/rtc-sync.service > /dev/null
[Unit]
Description=Sync RTC1 to system clock at boot
DefaultDependencies=no
Before=sysinit.target time-sync.target
After=local-fs.target
ConditionPathExists=/dev/rtc1

[Service]
Type=oneshot
ExecStart=/usr/local/bin/rtc-sync.sh
RemainAfterExit=yes

[Install]
WantedBy=sysinit.target
EOF
    sudo chmod 644 /etc/systemd/system/rtc-sync.service
    log_info "✅ rtc-sync installed (RTC1 → system clock at boot)"
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
# iss 패키지가 업로드된 경우에만 교체 (업데이트 시 항상 올라오지는 않음)
if [ -d /home/root/iss ]; then
    rm -rf /usr/local/sv500/iss
    mv /home/root/iss /usr/local/sv500/iss
fi
if [ -f /usr/local/sv500/iss/install.sh ]; then
    sudo chmod +x /usr/local/sv500/iss/install.sh
fi

# ntekadmin을 root 그룹에 추가 (디렉토리 접근용)
usermod -aG root $ADMIN_USER 2>/dev/null || true

# ntekadmin을 influxdb 그룹에 추가 (백업 디렉토리 쓰기 권한용)
usermod -aG influxdb $ADMIN_USER 2>/dev/null || true

# /home/root 그룹 접근 허용 (ntekadmin이 서비스 경로 진입할 수 있도록)
chmod 750 /home/root 2>/dev/null || true

# /usr/local/sv500 자체는 755 (other +x 필요)
# influxdb 같은 외부 계정이 자기 소유 하위(backup) 로 들어가려면 부모 traverse 권한 필수
if [ -d /usr/local/sv500 ]; then
    sudo chmod 755 /usr/local/sv500 2>/dev/null || true
fi
# /usr/local/sv500 은 backup(influxdb 소유) 등이 섞여있으므로 통째로 휩쓸지 않음.
# 아래 4개 폴더는 ntekadmin/root 어느 쪽으로 만들어졌든 root:root + 775 로 통일
# (그래야 ntekadmin · core 가 그룹으로 일관 접근 가능)
for subdir in reports trendcsv logs train; do
    if [ -d "/usr/local/sv500/$subdir" ]; then
        sudo chown -R root:root /usr/local/sv500/$subdir 2>/dev/null || true
        sudo chmod -R 775       /usr/local/sv500/$subdir 2>/dev/null || true
    fi
done
# /home/root/* : 배포 시점 owner 유지, 권한만 설정
for d in /home/root/webserver /home/root/core /home/root/mqClient; do
    if [ -d "$d" ]; then
        sudo chmod -R 770 "$d" 2>/dev/null || true
    fi
done
# config 는 775 (other read 필요)
if [ -d /home/root/config ]; then
    sudo chmod -R 775 /home/root/config 2>/dev/null || true
fi

# 네트워크/시간동기 설정: webserver(ntekadmin, root 그룹)가 직접 접근.
#  - *.network      : 비교용 read (쓰기는 sudo 경유)
#  - timesyncd.conf : sudo 없이 직접 read/write
# ntekadmin 이 root 그룹 멤버이므로 그룹 권한만 부여. 실행 비트 불필요.
# 664 = owner rw / group rw / other r
chmod 664 /etc/systemd/network/*.network 2>/dev/null || true
chmod 664 /etc/systemd/timesyncd.conf    2>/dev/null || true

# /usr/local/sv500/backup : influxdb 데몬 + influxdb 계정의 다른 프로세스가 파일 생성/접근
# 없으면 무조건 만들어야 함 (influxd 의 TMPDIR 가 이걸 가리켜서 없으면 backup 실패)
# owner=influxdb, mode 777 (cross-process 파일 생성/접근 보장)
sudo mkdir -p /usr/local/sv500/backup/influxdb
sudo chown -R influxdb:influxdb /usr/local/sv500/backup 2>/dev/null || true
sudo chmod -R 777               /usr/local/sv500/backup 2>/dev/null || true
log_info "✅ Permissions set: /usr/local/sv500/backup (influxdb:influxdb, 777)"


log_section "6. Reload systemd and Restart Services"

sudo chmod +x /home/root/SV500/fw_cortex_m33.sh
sudo chmod +x /home/root/bin/SV500_CA35


sudo systemctl daemon-reload

# Enable 정책: 모든 핵심 서비스 enable.
# systemd 가 After= 체인으로 순서 보장:
#   redis/influxdb → startup-monitor → webserver → core / smartsystems*
sudo systemctl enable  webserver.service       2>/dev/null || true
sudo systemctl enable  core.service            2>/dev/null || true
sudo systemctl enable  startup-monitor.service 2>/dev/null || true
sudo systemctl enable  sv500A35.service        2>/dev/null || true

# smartsystemsservice / smartsystemsrestapiservice: iss installer 가 만든 unit 파일에
# 우리가 원하는 After= 가 없을 수 있어 drop-in override 로 보강
for sname in smartsystemsservice smartsystemsrestapiservice; do
    spath="/etc/systemd/system/${sname}.service"
    if [ -f "$spath" ]; then
        sudo mkdir -p "${spath}.d"
        if [ "$sname" = "smartsystemsservice" ]; then
            sudo tee "${spath}.d/override.conf" > /dev/null <<'DROPIN'
[Unit]
After=
After=webserver.service smartsystemsrestapiservice.service influxdb.service
DROPIN
        else
            sudo tee "${spath}.d/override.conf" > /dev/null <<'DROPIN'
[Unit]
After=
After=webserver.service influxdb.service
DROPIN
        fi
        log_info "✅ ${sname}.service drop-in override 적용"
    fi
done

# 불필요한 서비스 disable (snmpd: 시작 실패로 부팅 90초 timeout 유발)
sudo systemctl stop    snmpd      2>/dev/null || true
sudo systemctl disable snmpd      2>/dev/null || true
sudo systemctl stop    snmptrapd  2>/dev/null || true
sudo systemctl disable snmptrapd  2>/dev/null || true
log_info "✅ snmpd/snmptrapd disabled"

# --nosavertc 옵션: time-keeper 만 토글 (startup-monitor 는 last_known_time 파일 유무로 자동 분기)
if [ "$NOSAVE_RTC" = "1" ]; then
    sudo systemctl stop    time-keeper.timer 2>/dev/null || true
    sudo systemctl disable time-keeper.timer 2>/dev/null || true
    log_info "✅ time-keeper disabled (startup-monitor 가 RTC 복구 skip)"
else
    sudo systemctl enable  time-keeper.timer 2>/dev/null || true
    sudo systemctl start   time-keeper.timer 2>/dev/null || true
    log_info "✅ time-keeper enabled (startup-monitor 가 RTC 복구 수행)"
fi

# rtc-sync.service: DEVICE_MODE=1 (--rtc1 / --nosavertc1) 에서만 enable
if [ "$DEVICE_MODE" = "1" ]; then
    sudo systemctl enable rtc-sync.service 2>/dev/null || true
    log_info "✅ rtc-sync enabled (boot 시 /dev/rtc1 → 시스템 클럭)"
else
    sudo systemctl disable rtc-sync.service 2>/dev/null || true
fi

# init-tsn.service: SWITCH_MODE=1 (--switch) 에서만 enable
if [ "$SWITCH_MODE" = "1" ]; then
    sudo systemctl enable init-tsn.service 2>/dev/null || true
    sudo systemctl start  init-tsn.service 2>/dev/null || true
    log_info "✅ init-tsn enabled (스위치 모드 — systemd-networkd 이후 1회 실행)"
else
    sudo systemctl stop    init-tsn.service 2>/dev/null || true
    sudo systemctl disable init-tsn.service 2>/dev/null || true
fi

sudo systemctl daemon-reload

log_info "Restarting services (systemd 가 After= 체인으로 순서 보장)..."
sudo systemctl restart startup-monitor.service
sleep 1
sudo systemctl restart sv500A35.service 2>/dev/null || true
sudo systemctl restart webserver.service
sleep 3
sudo systemctl restart core.service
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