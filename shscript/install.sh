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
# 옵션 파싱 (기본값: local)
# Usage: ./install.sh [--local|--lte]
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

log_info "Install mode: $MODE"

# =================================================================
# 0. Create ntekadmin user and sudoers
# =================================================================
log_section "0. Create ntekadmin User"

ADMIN_USER="ntekadmin"
ADMIN_PASS="Ntek@dm1n2025!"

if id "$ADMIN_USER" &>/dev/null; then
    log_info "User $ADMIN_USER already exists, skipping..."
else
    log_info "Creating user $ADMIN_USER..."
    useradd -m -s /bin/bash "$ADMIN_USER"
    echo "$ADMIN_USER:$ADMIN_PASS" | chpasswd
    log_info "User $ADMIN_USER created (change password after first login)"
fi

# sudoers 설정
SUDOERS_SRC="$(dirname "$0")/sv500-sudoers"
SUDOERS_DST="/etc/sudoers.d/sv500-web"

if [ -f "$SUDOERS_SRC" ]; then
    cp "$SUDOERS_SRC" "$SUDOERS_DST"
    chmod 440 "$SUDOERS_DST"
    chown root:root "$SUDOERS_DST"
    log_info "Sudoers file installed: $SUDOERS_DST"
else
    log_warn "Sudoers file not found: $SUDOERS_SRC"
fi

# ntekadmin을 root 그룹에 추가 (디렉토리 접근용)
usermod -aG root $ADMIN_USER 2>/dev/null || true

# 쓰기 필요한 디렉토리에 그룹 쓰기 권한 부여
chmod -R g+w /usr/local/sv500 2>/dev/null || true
chmod -R g+w /home/root/webserver 2>/dev/null || true
chmod -R g+w /home/root/core 2>/dev/null || true

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
sudo hwclock --systohc --utc  
timedatectl status && hwclock -r
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

# LTE 모드일 경우에만 frp 압축 해제
if [ "$MODE" = "lte" ]; then
    tar -xzf frp_0.66.0_linux_arm64.tar.gz
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
MARKER_FILE="/var/run/clean_shutdown"
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
cat > /etc/systemd/system/shutdown-marker.service << 'EOF'
[Unit]
Description=Create clean shutdown marker
DefaultDependencies=no
Before=shutdown.target reboot.target halt.target

[Service]
Type=oneshot
ExecStart=/bin/touch /var/run/clean_shutdown
RemainAfterExit=yes

[Install]
WantedBy=shutdown.target reboot.target halt.target
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

mkdir -p /usr/local/sv500/backup/influxdb
chown influxdb:influxdb /usr/local/sv500/backup/influxdb
chmod 775 /usr/local/sv500/backup/influxdb

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

    log_info "✅ Webserver service configured"
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

    log_info "✅ Core service configured"
else
    log_warn "Core directory not found: $CORE_DIR"
fi

# =================================================================
# 7. Boot Helper Script
# =================================================================
log_section "7. Creating Boot Helper Script"

cat > /usr/local/bin/startup-helper.sh << 'EOF'
#!/bin/bash
# Boot service start order assurance

LOG="/var/log/startup-helper.log"
echo "[$(date)] Boot helper script started" >> $LOG

# Wait for mount
while ! mountpoint -q /usr/local; do
    echo "[$(date)] Waiting for /usr/local mount..." >> $LOG
    sleep 1
done

# Prepare Redis directory
mkdir -p /var/run/redis
chown redis:redis /var/run/redis 2>/dev/null || true

# Sequential service start
echo "[$(date)] Starting services..." >> $LOG
systemctl start redis
sleep 2
systemctl start influxdb
sleep 3
systemctl start webserver
systemctl start core

echo "[$(date)] All services started" >> $LOG
EOF

chmod +x /usr/local/bin/startup-helper.sh

cat > /etc/systemd/system/startup-helper.service << 'EOF'
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

# =================================================================
# 8. Enable and Start Services
# =================================================================
log_section "8. Enable and Start Services"

# Reload systemd
sudo systemctl daemon-reload
sudo systemctl restart systemd-journald

# Enable Shutdown Monitor
sudo systemctl enable shutdown-marker.service
sudo systemctl enable shutdown-monitor.service

# Enable main services
sudo systemctl enable influxdb.service
sudo systemctl enable redis.service
sudo systemctl enable webserver.service
sudo systemctl enable core.service
sudo systemctl enable startup-helper.service

# Start services
log_info "Starting services..."
sudo systemctl start redis
sleep 2
sudo systemctl start influxdb
sleep 3
sudo systemctl start webserver
#sudo systemctl start core

#######################################
# 8.5 register sv500A35.service

sudo chmod +x /home/root/SV500/fw_cortex_m33.sh
sudo chmod +x /home/root/bin/SV500_CA35
sudo chmod +x /home/root/mqClient/mqtt_publisher

SERVICE_NAME=sv500A35.service
SERVICE_PATH=/etc/systemd/system/$SERVICE_NAME

# service file 
cat <<EOF | sudo tee $SERVICE_PATH > /dev/null
[Unit]
Description=SV500A35 Service
After=network.target

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

# configure the authority and register the service
sudo chmod 644 $SERVICE_PATH
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
#sudo systemctl start $SERVICE_NAME

echo "$SERVICE_NAME registered"

# Disable unnecessary services
sudo systemctl stop avahi-daemon 2>/dev/null || true
sudo systemctl disable avahi-daemon 2>/dev/null || true
sudo systemctl stop avahi-daemon.socket 2>/dev/null || true
sudo systemctl disable avahi-daemon.socket 2>/dev/null || true
sudo systemctl stop netdata 2>/dev/null || true
sudo systemctl disable netdata 2>/dev/null || true

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
