#!/bin/sh

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log functions
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
# 옵션 파싱
# Usage: ./install.sh [--local|--lte] [--rtc0|--rtc1|--nosavertc|--nosavertc1] [--switch|--noswitch]
#   --local/--lte : 네트워크 모드 (기본: local)
#   --rtc0        : rtc0 사용, 시간 저장/복원 O (default)
#   --rtc1        : rtc1 사용, 시간 저장/복원 O
#   --nosavertc   : rtc0 사용, 시간 저장/복원 X
#   --nosavertc1  : rtc1 사용, 시간 저장/복원 X
#   --switch      : 스위치 모드 (init-tsn.service 활성화)
#   --noswitch    : 일반 모드, init-tsn 비활성화 (default)
# (docker mode는 install.sh 대상 아님 — 컨테이너에서 직접 SV500_MODE=3 설정)
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

# RTC 디바이스 옵션 (DEVICE_MODE=1이면 /dev/rtc1, 그 외엔 기본)
if [ "$DEVICE_MODE" = "1" ]; then
    HWCLOCK_OPTS="-f /dev/rtc1"
else
    HWCLOCK_OPTS=""
fi

log_info "Install mode: network=$MODE, device=$DEVICE_MODE, switch=$SWITCH_MODE (hwclock opts: '$HWCLOCK_OPTS')"

# =================================================================
# 0. Create ntekadmin user and sudoers
# =================================================================
log_section "0. Create ntekadmin User"

ADMIN_USER="ntekadmin"
ADMIN_PASS="Ntek@dmin2026!"
ROOT_PASS="@dmin@Ntek2026!"

if id "$ADMIN_USER" &>/dev/null; then
    log_info "User $ADMIN_USER already exists, skipping..."
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

# ntekadmin을 root 그룹에 추가 (디렉토리 접근용)
usermod -aG root $ADMIN_USER 2>/dev/null || true

# ntekadmin을 influxdb 그룹에 추가 (백업 디렉토리 쓰기 권한용)
usermod -aG influxdb $ADMIN_USER 2>/dev/null || true

# /home/root 그룹 접근 허용 (ntekadmin이 서비스 경로 진입할 수 있도록)
chmod 750 /home/root 2>/dev/null || true

log_info "ntekadmin setup complete"

#######################################
# backup profile
cp /etc/profile /etc/profile.bak_$(date +%Y%m%d_%H%M%S)

#######################################
# change zh_CN.UTF-8 -> en_US.UTF-8
sed -i 's/zh_CN.UTF-8/en_US.UTF-8/g' /etc/profile

echo "1. Locale changed : zh_CN.UTF-8 → en_US.UTF-8"

#######################################
# Change timezone and  rtc disable
sudo timedatectl set-timezone Asia/Seoul
echo "2. Timezone changed : Asia/Seoul"

sudo timedatectl set-ntp true  
sudo systemctl restart systemd-timesyncd  
sleep 5  
sudo timedatectl set-local-rtc 0  
sudo hwclock --systohc --utc $HWCLOCK_OPTS
timedatectl status && hwclock -r $HWCLOCK_OPTS
timedatectl set-ntp false

echo "2.5. RTC Enable and NTP disable"
#######################################
# create rpmsg rules
cat <<EOF > /etc/udev/rules.d/99-rpmsg.rules
SUBSYSTEM=="tty", KERNEL=="ttyRPMSG*", ATTRS{name}=="rpmsg-tty", SYMLINK+="ttyRPMSG0"
EOF
udevadm control --reload-rules
udevadm trigger
echo "3. Creating udev rule file : /etc/udev/rules.d/99-rpmsg.rules"

# Check offline directory
OFFLINE_DIR="/home/root/offline_package"
PIP_PACKAGE_DIR="/home/root/offline_package/packages/pip"

# pip_download 디렉토리 확인
if [ ! -d "$PIP_PACKAGE_DIR" ]; then
    log_warn "pip directory not found, checking python directory..."
    PIP_PACKAGE_DIR="$OFFLINE_DIR/packages/python"
    if [ ! -d "$PIP_PACKAGE_DIR" ]; then
        log_error "No package directory found!"
        exit 1
    fi
fi

# =================================================================
# 1. System Basic Configuration
# =================================================================
log_section "1. System Basic Configuration"

log_info "Creating essential directories..."
sudo mkdir -p /usr/local/bin
sudo mkdir -p /usr/local/data
sudo mkdir -p /usr/local/influxdb2
sudo mkdir -p /var/log
sudo mkdir -p /usr/local/sv500/logs/web
sudo mkdir -p /usr/local/sv500/logs/core
sudo mkdir -p /usr/local/sv500/trendcsv

# /usr/local/sv500 자체는 755 (other +x 필요)
# influxdb 같은 외부 계정이 자기 소유 하위(backup) 로 들어가려면 부모 traverse 권한 필수
if [ -d /usr/local/sv500 ]; then
    chmod 755 /usr/local/sv500 2>/dev/null || true
fi
# /usr/local/sv500 은 backup(influxdb 소유) 등이 섞이므로 필요한 하위만 처리.
# 아래 4개 폴더는 ntekadmin/root 어느 쪽으로 만들어졌든 root:root + 775 로 통일
# (그래야 ntekadmin · core 가 그룹으로 일관 접근 가능)
for subdir in reports trendcsv logs train; do
    if [ -d "/usr/local/sv500/$subdir" ]; then
        chown -R root:root /usr/local/sv500/$subdir 2>/dev/null || true
        chmod -R 775       /usr/local/sv500/$subdir 2>/dev/null || true
    fi
done
# /home/root/* : 배포 시점 owner 유지, 권한만 설정
for d in /home/root/webserver /home/root/core /home/root/mqClient; do
    if [ -d "$d" ]; then
        chmod -R 770 "$d" 2>/dev/null || true
    fi
done
# config 는 775 (other read 필요)
if [ -d /home/root/config ]; then
    chmod -R 775 /home/root/config 2>/dev/null || true
fi

# 네트워크/시간동기 설정: webserver(ntekadmin, root 그룹)가 직접 접근.
#  - *.network      : 비교용 read (쓰기는 sudo 경유)
#  - timesyncd.conf : sudo 없이 직접 read/write
# ntekadmin 이 root 그룹 멤버이므로 그룹 권한만 부여. 실행 비트 불필요.
# 664 = owner rw / group rw / other r
chmod 664 /etc/systemd/network/*.network 2>/dev/null || true
chmod 664 /etc/systemd/timesyncd.conf    2>/dev/null || true

# LTE 모드일 경우에만 frp 압축 해제
if [ "$MODE" = "lte" ]; then
    tar -xzf frp_0.66.0_linux_arm64.tar.gz
    rm -f frp_0.66.0_linux_arm64.tar.gz
    log_info "FRP extracted (LTE mode)"
else
    log_info "Local mode: skipping FRP extraction"
fi

# Define variables
APP_DIR=/home/root/webserver
CORE_DIR=/home/root/core
REDIS_DIR=/home/root/bin
MAIN_FILE=main_linux.py
INFLUX_DATA_DIR=/usr/local/data/influxdb2
INFLUX_INSTALL_DIR=/usr/local/influxdb2

# === 공유 가상환경 설정 ===
SHARED_VENV_DIR=/home/root/shared_venv

# Enable network wait
sudo systemctl enable systemd-networkd-wait-online.service 2>/dev/null || true

# =================================================================
# 2. Install Shutdown Monitor
# =================================================================
log_section "2. Install Shutdown Monitor"

# Create shutdown-monitor.sh
cat > /usr/local/bin/shutdown-monitor.sh << 'EOF'
#!/bin/bash
#
# Abnormal shutdown detection and processing script
#

# Configuration
MARKER_FILE="/usr/local/sv500/clean_shutdown"
LOG_FILE="/var/log/shutdown-monitor.log"
PYTHON_DIRS="/home/root/webserver /home/root/core"
MAX_LOG_SIZE=10485760  # 10MB

# Log function
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Log file size management
manage_log_size() {
    if [ -f "$LOG_FILE" ]; then
        local size=$(stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)
        if [ "$size" -gt "$MAX_LOG_SIZE" ]; then
            mv "$LOG_FILE" "${LOG_FILE}.old"
            log_message "Log rotated - previous log saved as ${LOG_FILE}.old"
        fi
    fi
}

# Collect system information
collect_system_info() {
    local uptime_info=$(uptime -p 2>/dev/null || echo "unknown")
    local boot_time=$(uptime -s 2>/dev/null || echo "unknown")
    local disk_usage=$(df -h / | tail -1 | awk '{print $5}')
    local memory_usage=$(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')
    
    echo "Boot time: $boot_time, Uptime: $uptime_info, Disk: $disk_usage, Memory: $memory_usage"
}

# Clean pyc files (conditional - old files only)
clean_pyc_files() {
    local count=0
    for dir in $PYTHON_DIRS; do
        if [ -d "$dir" ]; then
            # Delete cache files older than 7 days
            local deleted=$(find "$dir" -name "*.pyc" -type f -mtime +7 -delete -print 2>/dev/null | wc -l)
            count=$((count + deleted))
        fi
    done
    echo "$count"
}

# Main logic
main() {
    manage_log_size
    system_info=$(collect_system_info)
    
    if [ -f "$MARKER_FILE" ]; then
        log_message "NORMAL SHUTDOWN - System was properly shut down"
        log_message "System info: $system_info"
        rm -f "$MARKER_FILE"
    else
        log_message "WARNING: ABNORMAL SHUTDOWN DETECTED - Power loss or system crash"
        log_message "System info: $system_info"
        
        # Clean only old pyc files
        log_message "Cleaning old Python cache files..."
        pyc_count=$(clean_pyc_files)
        if [ $pyc_count -gt 0 ]; then
            log_message "Removed $pyc_count old .pyc files"
        fi
        
        # Redis data integrity check
        if [ -f /var/lib/redis/dump.rdb ]; then
            log_message "Checking Redis data integrity..."
            redis-cli ping > /dev/null 2>&1 || {
                log_message "Redis check failed, backing up potentially corrupted data"
                mv /var/lib/redis/dump.rdb /var/lib/redis/dump.rdb.corrupted.$(date +%Y%m%d%H%M%S)
            }
        fi
    fi
    
    log_message "Boot sequence completed"
    log_message "----------------------------------------"
}

main
EOF

chmod +x /usr/local/bin/shutdown-monitor.sh

# Create shutdown-marker.service
# 마커는 영구 위치(/usr/local/sv500)에 — /var/run은 tmpfs라 reboot 시 휘발됨
# Conflicts + ExecStop 패턴: 부팅 시 active 유지 → 종료 target 진입 시 stop → ExecStop으로 마커 생성
cat > /etc/systemd/system/shutdown-marker.service << 'EOF'
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

# Create shutdown-monitor.service
cat > /etc/systemd/system/shutdown-monitor.service << 'EOF'
[Unit]
Description=Shutdown Monitor
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/shutdown-monitor.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# =================================================================
# 2.5 시스템 패키지 설치 (APT 패키지)
# =================================================================
log_section "2.5 시스템 패키지 설치"

# APT 패키지 디렉토리 확인
APT_PACKAGE_DIR="$OFFLINE_DIR/packages/apt"
if [ -d "$APT_PACKAGE_DIR" ]; then
    log_info "APT 패키지 설치 중..."
    
    # 의존성 순서대로 설치
    # 1. 기본 라이브러리
    dpkg -i $APT_PACKAGE_DIR/libgdbm6_*.deb 2>/dev/null || true
    dpkg -i $APT_PACKAGE_DIR/libgdbm-compat4_*.deb 2>/dev/null || true
    
    # 2. GCC 관련
    dpkg -i $APT_PACKAGE_DIR/gcc_12.3.0-r0_arm64.deb 2>/dev/null || true
    dpkg -i $APT_PACKAGE_DIR/g++_12.3.0-r0_arm64.deb 2>/dev/null || true
    
    # 3. Make
    dpkg -i $APT_PACKAGE_DIR/make_*.deb 2>/dev/null || true
    
    # 4. Python3 기본
    dpkg -i $APT_PACKAGE_DIR/python3_3.11.5-r0_arm64.deb 2>/dev/null || true
    dpkg -i $APT_PACKAGE_DIR/python3-db_*.deb 2>/dev/null || true
    
    # 5. Python3 개발 도구
    dpkg -i $APT_PACKAGE_DIR/python3-dev_*.deb 2>/dev/null || true
    
    # 6. Python3 라이브러리들
    dpkg -i $APT_PACKAGE_DIR/python3-doctest_*.deb 2>/dev/null || true
    dpkg -i $APT_PACKAGE_DIR/python3-gdbm_*.deb 2>/dev/null || true
    dpkg -i $APT_PACKAGE_DIR/python3-mailbox_*.deb 2>/dev/null || true
    dpkg -i $APT_PACKAGE_DIR/python3-modules_*.deb 2>/dev/null || true
    dpkg -i $APT_PACKAGE_DIR/python3-sqlite3_*.deb 2>/dev/null || true
    dpkg -i $APT_PACKAGE_DIR/python3-statistics_*.deb 2>/dev/null || true
    dpkg -i $APT_PACKAGE_DIR/python3-syslog_*.deb 2>/dev/null || true
    dpkg -i $APT_PACKAGE_DIR/python3-tkinter_*.deb 2>/dev/null || true
    dpkg -i $APT_PACKAGE_DIR/python3-venv_*.deb 2>/dev/null || true
    dpkg -i $APT_PACKAGE_DIR/python3-wheel_*.deb 2>/dev/null || true
    dpkg -i $APT_PACKAGE_DIR/python3-zoneinfo_*.deb 2>/dev/null || true
    dpkg -i $APT_PACKAGE_DIR/python3-smtpd_*.deb 2>/dev/null || true
    
    # 7. 모든 패키지 한번에 설치 (의존성 해결)
    log_info "APT 패키지 의존성 해결 중..."
    dpkg -i $APT_PACKAGE_DIR/*.deb 2>/dev/null || true
    
    # 8. 누락된 의존성 수정
    apt-get install -f -y 2>/dev/null || true
    
    log_info "✅ APT 패키지 설치 완료"
else
    log_warn "APT 패키지 디렉토리가 없습니다: $APT_PACKAGE_DIR"
fi

# =================================================================
# 3. Install InfluxDB 2.7.11 (Offline)
# =================================================================
log_section "3. Install InfluxDB 2.7.11"

# Stop existing services
sudo systemctl stop influxdb 2>/dev/null || true
sudo systemctl stop influxdb2-custom 2>/dev/null || true

# Create InfluxDB user
sudo useradd -r -s /bin/false influxdb 2>/dev/null || true

# Install InfluxDB (using offline package)
if [ -f "$OFFLINE_DIR/binaries/influxdb2-2.7.11_linux_arm64.tar.gz" ]; then
    log_info "Extracting InfluxDB..."
    
    mkdir -p /tmp/influx_temp
    tar xzf "$OFFLINE_DIR/binaries/influxdb2-2.7.11_linux_arm64.tar.gz" -C /tmp/influx_temp
    
    # Check actual structure and copy
    sudo mkdir -p $INFLUX_INSTALL_DIR
    
    # Find influxd executable
    if [ -f /tmp/influx_temp/influxdb2-2.7.11/usr/bin/influxd ]; then
        sudo cp -r /tmp/influx_temp/influxdb2-2.7.11/usr/bin/* $INFLUX_INSTALL_DIR/
    elif [ -f /tmp/influx_temp/usr/bin/influxd ]; then
        sudo cp -r /tmp/influx_temp/usr/bin/* $INFLUX_INSTALL_DIR/
    elif [ -f /tmp/influx_temp/influxd ]; then
        sudo cp -r /tmp/influx_temp/* $INFLUX_INSTALL_DIR/
    else
        log_error "influxd executable not found!"
        exit 1
    fi
    
    # Set execution permissions
    sudo chmod +x $INFLUX_INSTALL_DIR/influxd
    
    # Install CLI (if available)
    if [ -f "$OFFLINE_DIR/binaries/influxdb2-client-2.7.5-linux-arm64.tar.gz" ]; then
        log_info "Installing InfluxDB CLI..."
        cd /tmp
        tar xzf "$OFFLINE_DIR/binaries/influxdb2-client-2.7.5-linux-arm64.tar.gz"
        
        if [ -f influx ]; then
            sudo cp influx $INFLUX_INSTALL_DIR/
            sudo chmod +x $INFLUX_INSTALL_DIR/influx
            sudo chown influxdb:influxdb $INFLUX_INSTALL_DIR/influx
            
            # Create symbolic link for global use
            sudo ln -sf $INFLUX_INSTALL_DIR/influx /usr/local/bin/influx
            
            log_info "InfluxDB CLI (influx) installation complete"
        fi
        
        # Clean up temporary files
        rm -f influx LICENSE README.md
    fi
    
    # Clean up temporary directory
    rm -rf /tmp/influx_temp
    
    # Create data directory and set permissions
    sudo mkdir -p $INFLUX_DATA_DIR
    sudo chown -R influxdb:influxdb $INFLUX_INSTALL_DIR
    sudo chown -R influxdb:influxdb $INFLUX_DATA_DIR
    sudo chmod 755 $INFLUX_DATA_DIR
    
    log_info "✅ InfluxDB 2.7.11 installation complete"
else
    log_error "InfluxDB package not found: $OFFLINE_DIR/binaries/influxdb2-2.7.11_linux_arm64.tar.gz"
    exit 1
fi

# /usr/local/sv500/backup : influxdb 데몬 + influxdb 계정의 다른 프로세스가 파일 생성/접근
# owner=influxdb, mode 777 (cross-process 파일 생성/접근 보장)
mkdir -p /usr/local/sv500/backup/influxdb
chown -R influxdb:influxdb /usr/local/sv500/backup
chmod -R 777               /usr/local/sv500/backup

# InfluxDB systemd service file (with mount wait)
cat <<EOF | sudo tee /etc/systemd/system/influxdb.service > /dev/null
[Unit]
Description=InfluxDB 2.7.11
After=network.target local-fs.target
Wants=
RequiresMountsFor=/usr/local

[Service]
Type=simple
User=influxdb
Group=influxdb
Environment="INFLUXD_BOLT_PATH=$INFLUX_DATA_DIR/influxdb.bolt"
Environment="INFLUXD_ENGINE_PATH=$INFLUX_DATA_DIR/engine"
Environment="TMPDIR=/usr/local/sv500/backup/influxdb"
Environment="INFLUXD_STORAGE_CACHE_MAX_MEMORY_SIZE=134217728"
ExecStartPre=/bin/bash -c 'until [ -d $INFLUX_INSTALL_DIR ]; do sleep 1; done'
# TMPDIR 가 가리키는 디렉토리 보장 (없으면 backup 시 metadata snapshot 실패)
ExecStartPre=/bin/mkdir -p /usr/local/sv500/backup/influxdb
ExecStartPre=/bin/chown influxdb:influxdb /usr/local/sv500/backup/influxdb
ExecStart=$INFLUX_INSTALL_DIR/influxd
Restart=always
RestartSec=5
StartLimitInterval=300
StartLimitBurst=5

# Log limits
StandardOutput=journal
StandardError=journal
SyslogLevel=err

[Install]
WantedBy=multi-user.target
EOF

# =================================================================
# 4. Install and Optimize Redis
# =================================================================
log_section "4. Install and Optimize Redis"

# Prepare Redis directory
mkdir -p /etc/redis
mkdir -p /usr/local/data/redis

if [ -f "$REDIS_DIR/redis-server" ] && [ -f "$REDIS_DIR/redis-cli" ]; then
    chmod +x $REDIS_DIR/redis-server
    chmod +x $REDIS_DIR/redis-cli
    
    # Optimized Redis configuration
    cat <<EOF > /etc/redis/redis.conf
bind 127.0.0.1
port 6379
protected-mode no
daemonize no
dir /usr/local/data/redis
save ""
appendonly no
EOF
    
    cat <<EOF > /etc/systemd/system/redis.service
[Unit]
Description=Redis In-Memory Data Store
After=network.target

[Service]
ExecStart=$REDIS_DIR/redis-server /etc/redis/redis.conf
Restart=always

[Install]
WantedBy=multi-user.target
EOF
    
    log_info "✅ Redis configuration complete"
else
    log_error "Redis executable not found: $REDIS_DIR/redis-server"
fi

# =================================================================
# 5. Optimize System Logs
# =================================================================
log_section "5. Optimize System Logs"

sed -i 's/#SystemMaxUse=/SystemMaxUse=10M/' /etc/systemd/journald.conf
sed -i 's/#SystemMaxFileSize=/SystemMaxFileSize=2M/' /etc/systemd/journald.conf
sed -i 's/#MaxRetentionSec=/MaxRetentionSec=7d/' /etc/systemd/journald.conf

log_info "✅ System log optimization complete"

# =================================================================
# 6. Install Python Applications (공유 가상환경)
# =================================================================
log_section "6. Install Python Applications (Shared Virtual Environment)"

# Python runs as python3
PYTHON_CMD="python3"
log_info "Python version: $(python3 --version)"

# === 공유 가상환경 생성 ===
log_info "Creating shared virtual environment at $SHARED_VENV_DIR..."
$PYTHON_CMD -m venv $SHARED_VENV_DIR
source "$SHARED_VENV_DIR/bin/activate"

# Upgrade pip (offline)
log_info "Upgrading pip..."
$SHARED_VENV_DIR/bin/pip install --no-index --find-links $PIP_PACKAGE_DIR \
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
    
    # JSON에서 패키지 목록 추출
    DEPS=$(python3 -c "
import json
with open('$JSON_FILE') as f:
    data = json.load(f)
print(' '.join(data.get('dependencies', [])))
")
    
    log_info "Packages to install: $DEPS"
    
    # 각 패키지 설치 (의존성 포함)
    for package in $DEPS; do
        if [ -n "$package" ] && [ "$package" != "asyncio" ]; then
            log_info "Installing $package..."
            $SHARED_VENV_DIR/bin/pip install --no-index --find-links $PIP_PACKAGE_DIR "$package" 2>/dev/null || {
                log_warn "Failed to install $package, trying without deps..."
                $SHARED_VENV_DIR/bin/pip install --no-index --find-links $PIP_PACKAGE_DIR --no-deps "$package" 2>/dev/null || true
            }
        fi
    done
else
    log_error "pip_install.json not found!"
fi

# 설치 확인
log_info "Verifying installation..."
$SHARED_VENV_DIR/bin/pip list | grep -E "fastapi|uvicorn|pandas|influxdb|redis" || true

deactivate

log_info "✅ Shared virtual environment setup complete: $SHARED_VENV_DIR"

# === Webserver 서비스 설정 ===
if [ -d "$APP_DIR" ]; then
    log_info "Configuring webserver service..."
    
    # Create webserver service file (공유 venv 사용)
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
# webserver 가 (재)시작되면 frpc 터널을 다시 맺어 LTE→frpc SSH 세션을 복구한다.
# frpc 가 떠 있을 때만 재시작(try-restart 효과), 없으면 무시. webserver stop 시엔 건드리지 않음.
ExecStartPost=-/bin/sh -c 'systemctl is-active --quiet frpc && sudo /bin/systemctl restart frpc'
Restart=always
RestartSec=5
TimeoutStartSec=120
User=ntekadmin
Group=root
UMask=0007

[Install]
WantedBy=multi-user.target
EOF

    log_info "✅ Webserver service configured (SV500_MODE=$DEVICE_MODE)"
else
    log_warn "Webserver directory not found: $APP_DIR"
fi

# === Core 서비스 설정 ===
if [ -d "$CORE_DIR" ]; then
    log_info "Configuring Core service..."
    
    # Create Core service file (공유 venv 사용)
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

    log_info "✅ Core service configured (SV500_MODE=$DEVICE_MODE)"
else
    log_warn "Core directory not found: $CORE_DIR"
fi

# =================================================================
# 7. Boot Helper Script
# =================================================================
log_section "7. Creating Boot Helper Script"

# Generate startup-monitor.sh based on rtc/nosavertc options
# (별도 파일로 두지 않고 install.sh / update.sh 가 옵션에 맞게 생성)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
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

# Switch mode: TSN/STP daisy chain 초기화 (init-tsn.sh 부팅 시 1회 직접 실행) + 자동 부여된 관리 IP 제거
if [ "\$SWITCH_MODE" = "1" ]; then
    log "→ Switch mode: running init-tsn.sh"
    chmod +x /usr/local/bin/init-tsn.sh 2>/dev/null || true
    sh /usr/local/bin/init-tsn.sh >> "\$LOG" 2>&1 || true
    log "→ Switch mode: removing auto-assigned IP (192.168.0.10/32 on sw0ep)"
    ip addr del 192.168.0.10/32 dev sw0ep 2>/dev/null || true
fi

log "===== Boot logging done ====="
MONITOR_EOF
chmod +x /usr/local/bin/startup-monitor.sh
log_info "✅ startup-monitor.sh generated (DEVICE_MODE=$DEVICE_MODE NOSAVE_RTC=$NOSAVE_RTC)"

cat > /etc/systemd/system/startup-monitor.service << 'EOF'
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

# Install time-keeper (heartbeat for RTC reset recovery)
cp "$SCRIPT_DIR/save-time.sh" /usr/local/bin/save-time.sh
chmod +x /usr/local/bin/save-time.sh
cp "$SCRIPT_DIR/time-keeper.service" /etc/systemd/system/time-keeper.service
cp "$SCRIPT_DIR/time-keeper.timer"   /etc/systemd/system/time-keeper.timer
chmod 644 /etc/systemd/system/time-keeper.service /etc/systemd/system/time-keeper.timer
log_info "✅ time-keeper installed"

# Install init-tsn.sh (스위치 모드 TSN/STP daisy chain 초기화 — startup-monitor 가 부팅 시 1회 직접 실행)
cp "$SCRIPT_DIR/init-tsn.sh" /usr/local/bin/init-tsn.sh
chmod +x /usr/local/bin/init-tsn.sh
log_info "✅ init-tsn.sh installed (service 미사용 — startup-monitor 가 직접 실행)"

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

#######################################
# 8. register sv500A35.service

sudo chmod +x /home/root/SV500/fw_cortex_m33.sh
sudo chmod +x /home/root/bin/SV500_CA35
sudo chmod +x /home/root/mqClient/mqtt_publisher

SERVICE_NAME=sv500A35.service
SERVICE_PATH=/etc/systemd/system/$SERVICE_NAME

# service file 
cat <<EOF | sudo tee $SERVICE_PATH > /dev/null
[Unit]
Description=SV500A35 Service
After=network.target redis.service

[Service]
ExecStart=/home/root/bin/SV500_CA35
WorkingDirectory=/home/root/bin
Restart=always
User=root
TimeoutStopSec=10s
KillMode=mixed

[Install]
WantedBy=multi-user.target
EOF

# =================================================================
# 8.5 Enable and Start Services
# =================================================================
log_section "8. Enable and Start Services"

# Reload systemd
sudo systemctl daemon-reload
sudo systemctl restart systemd-journald

# Enable Shutdown Monitor
sudo systemctl enable shutdown-marker.service
sudo systemctl enable shutdown-monitor.service

# Enable main services
# 모두 enable. systemd 가 After= 체인으로 순서 보장:
#   redis/influxdb → startup-monitor → webserver → core / smartsystems*
sudo systemctl enable influxdb.service
sudo systemctl enable redis.service
sudo systemctl enable webserver.service
sudo systemctl enable core.service
sudo systemctl enable startup-monitor.service
sudo systemctl enable sv500A35.service

# time-keeper.timer: --nosavertc / --nosavertc1 이면 비활성
if [ "$NOSAVE_RTC" = "1" ]; then
    sudo systemctl disable time-keeper.timer 2>/dev/null || true
    log_info "✅ time-keeper disabled (nosavertc mode)"
else
    sudo systemctl enable time-keeper.timer
    log_info "✅ time-keeper enabled (RTC 복구 활성)"
fi

# rtc-sync.service: DEVICE_MODE=1 (--rtc1 / --nosavertc1) 에서만 enable
if [ "$DEVICE_MODE" = "1" ]; then
    sudo systemctl enable rtc-sync.service
    log_info "✅ rtc-sync enabled (boot 시 /dev/rtc1 → 시스템 클럭)"
else
    sudo systemctl disable rtc-sync.service 2>/dev/null || true
fi

# init-tsn.service 폐기: startup-monitor 가 부팅 시 init-tsn.sh 를 직접 실행 (기존 설치본이 있을 때만 정리)
if [ -f /etc/systemd/system/init-tsn.service ]; then
    sudo systemctl stop    init-tsn.service 2>/dev/null || true
    sudo systemctl disable init-tsn.service 2>/dev/null || true
    sudo rm -f /etc/systemd/system/init-tsn.service
    sudo systemctl daemon-reload
    log_info "✅ 기존 init-tsn.service 제거"
fi

# smartsystemsservice / smartsystemsrestapiservice 의 After= 보강 (drop-in override)
# iss installer 가 만든 unit 파일에 After= 가 빠져있을 수 있어 우리가 명시
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

sudo systemctl daemon-reload

# Start services
log_info "Starting services..."
sudo systemctl start redis
sudo systemctl start influxdb
if [ "$NOSAVE_RTC" = "0" ]; then
    sudo systemctl start time-keeper.timer
fi
sudo systemctl start startup-monitor.service
sudo systemctl start sv500A35.service 2>/dev/null || true
sudo systemctl start webserver.service



# configure the authority and register the service
# (sv500A35 는 위에서 enable 처리됨, systemd 가 After=redis 로 자동 기동)
sudo chmod 644 $SERVICE_PATH
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

echo "$SERVICE_NAME registered"

# Disable unnecessary services
sudo systemctl stop avahi-daemon 2>/dev/null || true
sudo systemctl disable avahi-daemon 2>/dev/null || true
sudo systemctl stop avahi-daemon.socket 2>/dev/null || true
sudo systemctl disable avahi-daemon.socket 2>/dev/null || true
sudo systemctl stop netdata 2>/dev/null || true
sudo systemctl disable netdata 2>/dev/null || true
# snmpd/snmptrapd: 외부 NMS 없는 환경. 시작 시 control connection 실패로 90초 timeout 발생
sudo systemctl stop snmpd 2>/dev/null || true
sudo systemctl disable snmpd 2>/dev/null || true
sudo systemctl stop snmptrapd 2>/dev/null || true
sudo systemctl disable snmptrapd 2>/dev/null || true

# =================================================================
# 9. Installation Complete
# =================================================================

rm -rf /home/root/offline_package

log_info "Installing Smart Systems..."
mv /home/root/iss /usr/local/sv500/iss
chmod +x /usr/local/sv500/iss/install.sh
sudo sh /usr/local/sv500/iss/install.sh --fresh

# =================================================================
# 10. FRP 터널링 & Firewall (모드에 따라 처리)
# =================================================================
log_section "10. FRP Tunnel & Firewall Setup"

if [ "$MODE" = "lte" ]; then
    log_info "LTE mode: Installing FRP tunnel and Firewall..."

    mv /home/root/firewall.sh /opt/firewall.sh
    chmod +x /opt/firewall.sh
    mv /home/root/firewall.service /etc/systemd/system/firewall.service

    sudo systemctl daemon-reload
    sudo systemctl enable firewall.service
    sudo systemctl start firewall.service

    log_info "✅ FRP & Firewall installed (LTE mode)"
else
    log_info "Local mode: Removing FRP and Firewall files..."
    rm -f /home/root/frp_0.66.0_linux_arm64.tar.gz
    rm -f /home/root/firewall.sh
    rm -f /home/root/firewall.service
    log_info "✅ FRP & Firewall skipped (Local mode)"
fi

echo ""
log_info "✅ All services installed and started!"
echo ""
echo "=== Installed Components ==="
echo "- InfluxDB 2.7.11 (/usr/local/influxdb2)"
echo "- Redis (with optimized configuration)"
echo "- FastAPI webserver"
echo "- SV500 Core"
echo "- Shutdown Monitor (abnormal shutdown detection)"
echo "- Install mode: $MODE"
if [ "$SWITCH_MODE" = "1" ]; then
echo "- Switch mode: init-tsn.service enabled"
fi
if [ "$MODE" = "lte" ]; then
echo "- FRP Tunnel & Firewall"
fi
echo ""
echo "=== Applied Optimizations ==="
echo "- Shared virtual environment: $SHARED_VENV_DIR"
echo "- Python bytecode generation disabled (PYTHONDONTWRITEBYTECODE=1)"
echo "- Mount wait configuration (RequiresMountsFor=/usr/local)"
echo "- Redis memory and performance optimization"
echo "- System log optimization"
echo ""
echo "=== Disk Space Saved ==="
echo "- Single shared venv instead of two separate venvs"
echo "- Estimated savings: ~300MB"
echo ""

# =================================================================
# 스크립트 자기 자신 삭제 (설치 완료 후 정리)
# =================================================================
log_info "Cleaning up install script..."
rm -f "$0"
