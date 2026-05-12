#!/bin/bash

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =================================================================
# 옵션 파싱
# Usage: ./restore.sh <backup_tar_file> [transfer_tar_file] [--number N]
# =================================================================
NUMBER=1
POSITIONAL=()

while [ "$#" -gt 0 ]; do
  case $1 in
    --number)
      NUMBER="$2"
      shift 2
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

if [ ${#POSITIONAL[@]} -eq 0 ]; then
    echo "Usage: ./restore.sh <backup_tar_file> [transfer_tar_file] [--number N]"
    echo "Example: ./restore.sh sites/site-A/backup.tar sites/site-A/transfer.tar --number 2"
    exit 1
fi

BACKUP_TAR="${POSITIONAL[0]}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMP_DIR="$SCRIPT_DIR/restore_temp"
DATA_DIR="$SCRIPT_DIR/data${NUMBER}"

# 컨테이너 이름
INFLUXDB_CONTAINER="sv500-influxdb-${NUMBER}"
REDIS_CONTAINER="sv500-redis-${NUMBER}"
WEB_CONTAINER="sv500-web-${NUMBER}"

# compose 파일 및 프로젝트명
COMPOSE_FILE="docker-compose.${NUMBER}.yml"
PROJECT_NAME="sv500-${NUMBER}"

log_info "Restore target : number=$NUMBER, project=$PROJECT_NAME"
log_info "Containers     : $INFLUXDB_CONTAINER / $REDIS_CONTAINER / $WEB_CONTAINER"

# tar 파일 존재 확인
if [ ! -f "$BACKUP_TAR" ]; then
    log_error "Backup file not found: $BACKUP_TAR"
    exit 1
fi

# =================================================================
# 1. 기존 임시 폴더 정리 및 tar 풀기
# =================================================================
log_info "1. Extracting backup file..."
sudo rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"
tar xf "$BACKUP_TAR" -C "$TEMP_DIR"

# 백업 폴더 이름 자동 탐지
BACKUP_DIR=$(ls -d "$TEMP_DIR"/*/ | head -1)
if [ -z "$BACKUP_DIR" ]; then
    log_error "Backup directory not found inside tar"
    exit 1
fi

log_info "Backup directory: $BACKUP_DIR"

# =================================================================
# 2. 모든 컨테이너 완전 중지
# =================================================================
log_info "2. Stopping all containers..."
cd "$SCRIPT_DIR"
docker compose -p $PROJECT_NAME -f $COMPOSE_FILE down 2>/dev/null || docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE down 2>/dev/null
sleep 2

# =================================================================
# 3. InfluxDB 데이터 완전 초기화 후 복원
# =================================================================
log_info "3. Restoring InfluxDB..."

if [ ! -d "${BACKUP_DIR}influxdb" ]; then
    log_error "influxdb directory not found in backup"
    exit 1
fi

# 데이터 디렉토리 완전 삭제 후 재생성
log_info "Clearing InfluxDB data directory..."
sudo rm -rf "$DATA_DIR/influxdb"
sudo mkdir -p "$DATA_DIR/influxdb"
sudo chmod 777 "$DATA_DIR/influxdb"

# config 파일 먼저 복사 (docker compose up 전에)
log_info "Preparing config files..."
sudo mkdir -p "$DATA_DIR/config"
if [ -d "${BACKUP_DIR}config" ]; then
    sudo cp -f "${BACKUP_DIR}config/"* "$DATA_DIR/config/" 2>/dev/null
    log_info "Config files copied to data/config"
fi

# influx restore --full은 일부 버킷 shard를 빠뜨리는 경우가 있어 파일 단위 복원만 사용
log_info "Stopping InfluxDB before file-level restore..."
docker compose -p $PROJECT_NAME -f $COMPOSE_FILE stop influxdb 2>/dev/null || docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE stop influxdb 2>/dev/null
sleep 3

log_info "Resetting InfluxDB data directory..."
sudo rm -rf "$DATA_DIR/influxdb"
sudo mkdir -p "$DATA_DIR/influxdb/engine/data"
sudo mkdir -p "$DATA_DIR/influxdb/engine/wal"

log_info "Restoring bolt and sqlite metadata..."
BOLT_GZ=$(ls "${BACKUP_DIR}influxdb"/*.bolt.gz 2>/dev/null | head -1)
SQLITE_GZ=$(ls "${BACKUP_DIR}influxdb"/*.sqlite.gz 2>/dev/null | head -1)
if [ -z "$BOLT_GZ" ] || [ -z "$SQLITE_GZ" ]; then
    log_error "bolt or sqlite file missing in backup. Aborting."
    exit 1
fi
sudo sh -c "gunzip -c '$BOLT_GZ' > '$DATA_DIR/influxdb/influxd.bolt'"
sudo sh -c "gunzip -c '$SQLITE_GZ' > '$DATA_DIR/influxdb/influxd.sqlite'"
log_info "  bolt   : $(basename "$BOLT_GZ")"
log_info "  sqlite : $(basename "$SQLITE_GZ")"

log_info "Extracting all shard tar.gz files..."
shopt -s nullglob
SHARD_FILES=("${BACKUP_DIR}influxdb"/*.tar.gz)
shopt -u nullglob
TOTAL=${#SHARD_FILES[@]}
log_info "Backup contains $TOTAL shard tar.gz files."

EXTRACTED=0
FAILED=0
for f in "${SHARD_FILES[@]}"; do
    if sudo tar xzf "$f" -C "$DATA_DIR/influxdb/engine/data/" 2>/dev/null; then
        EXTRACTED=$((EXTRACTED + 1))
    else
        FAILED=$((FAILED + 1))
        log_warn "  ✗ Failed to extract: $(basename "$f")"
    fi
done
log_info "Shard result: extracted=$EXTRACTED, failed=$FAILED, total=$TOTAL"

if [ "$TOTAL" -eq 0 ] || [ "$FAILED" -gt 0 ] || [ "$EXTRACTED" -ne "$TOTAL" ]; then
    log_error "❌ Shard extraction incomplete. Aborting restore."
    exit 1
fi

log_info "Restored bucket directories:"
sudo du -sh "$DATA_DIR/influxdb/engine/data/"*/ 2>/dev/null | sed 's/^/    /'

sudo chmod -R 777 "$DATA_DIR/influxdb"

log_info "Starting InfluxDB with restored data..."
docker compose -p $PROJECT_NAME -f $COMPOSE_FILE up -d influxdb 2>/dev/null || docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE up -d influxdb 2>/dev/null
log_info "Waiting for InfluxDB to start (12s)..."
sleep 12

PING=$(docker exec $INFLUXDB_CONTAINER influx ping 2>&1)
log_info "InfluxDB ping: $PING"

INFLUX_JSON="$DATA_DIR/config/influx.json"
if [ -f "$INFLUX_JSON" ]; then
    TOKEN_VAL=$(grep -oE '"token"[[:space:]]*:[[:space:]]*"[^"]+"' "$INFLUX_JSON" | sed -E 's/.*"([^"]+)"$/\1/')
    ORG_VAL=$(grep -oE '"org"[[:space:]]*:[[:space:]]*"[^"]+"' "$INFLUX_JSON" | sed -E 's/.*"([^"]+)"$/\1/')
    if [ -n "$TOKEN_VAL" ] && [ -n "$ORG_VAL" ]; then
        log_info "Buckets in restored InfluxDB (org=$ORG_VAL):"
        docker exec $INFLUXDB_CONTAINER influx bucket list --org "$ORG_VAL" --token "$TOKEN_VAL" --host http://localhost:8086 2>&1 | sed 's/^/    /'
    fi
fi

# =================================================================
# 4. Config 파일을 웹 서버 컨테이너에 복사
# =================================================================
log_info "4. Starting remaining containers and copying config..."

# Redis, Web 시작
docker compose -p $PROJECT_NAME -f $COMPOSE_FILE up -d 2>/dev/null || docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE up -d 2>/dev/null
sleep 5

# config 파일 웹 컨테이너에 복사
if [ -d "${BACKUP_DIR}config" ]; then
    for f in influx.json setup.json maintenance.db meterCal.bin user.db; do
        if [ -f "${BACKUP_DIR}config/$f" ]; then
            docker cp "${BACKUP_DIR}config/$f" $WEB_CONTAINER:/home/root/config/$f
            log_info "✅ $f copied to web container"
        fi
    done
fi

# 로그 파일 복사
if [ -d "${BACKUP_DIR}logs" ]; then
    log_info "Copying log files..."
    sudo mkdir -p "$DATA_DIR/logs"
    sudo cp -r "${BACKUP_DIR}logs/"* "$DATA_DIR/logs/" 2>/dev/null
    log_info "✅ Logs copied"
fi

# =================================================================
# 5. SmartSystems 데이터 복원 (Transfer.tar)
# =================================================================
if [ -n "${POSITIONAL[1]}" ] && [ -f "${POSITIONAL[1]}" ]; then
    log_info "5. Restoring SmartSystems data..."
    TRANSFER_TAR="${POSITIONAL[1]}"
    TRANSFER_TEMP="$SCRIPT_DIR/transfer_temp"
    sudo rm -rf "$TRANSFER_TEMP"
    mkdir -p "$TRANSFER_TEMP"
    tar xf "$TRANSFER_TAR" -C "$TRANSFER_TEMP"

    # transfer의 dbbackup은 main backup보다 일반적으로 더 완전한 스냅샷.
    # influx restore는 토큰 없이 401로 실패하므로 파일 단위 복원으로 재구성.
    if [ -d "$TRANSFER_TEMP/dbbackup" ]; then
        log_info "Found dbbackup in transfer — replacing InfluxDB state from dbbackup..."
        docker compose -p $PROJECT_NAME -f $COMPOSE_FILE stop influxdb 2>/dev/null || docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE stop influxdb 2>/dev/null
        sleep 3

        sudo rm -rf "$DATA_DIR/influxdb"
        sudo mkdir -p "$DATA_DIR/influxdb/engine/data"
        sudo mkdir -p "$DATA_DIR/influxdb/engine/wal"

        DB_BOLT=$(ls "$TRANSFER_TEMP/dbbackup"/*.bolt.gz 2>/dev/null | head -1)
        DB_SQLITE=$(ls "$TRANSFER_TEMP/dbbackup"/*.sqlite.gz 2>/dev/null | head -1)
        if [ -z "$DB_BOLT" ] || [ -z "$DB_SQLITE" ]; then
            log_error "dbbackup missing bolt/sqlite — aborting."
            exit 1
        fi
        sudo sh -c "gunzip -c '$DB_BOLT' > '$DATA_DIR/influxdb/influxd.bolt'"
        sudo sh -c "gunzip -c '$DB_SQLITE' > '$DATA_DIR/influxdb/influxd.sqlite'"
        log_info "  bolt   : $(basename "$DB_BOLT")"
        log_info "  sqlite : $(basename "$DB_SQLITE")"

        shopt -s nullglob
        DB_SHARDS=("$TRANSFER_TEMP/dbbackup"/*.tar.gz)
        shopt -u nullglob
        DB_TOTAL=${#DB_SHARDS[@]}
        log_info "dbbackup contains $DB_TOTAL shard tar.gz files."

        DB_EXTRACTED=0
        DB_FAILED=0
        for f in "${DB_SHARDS[@]}"; do
            if sudo tar xzf "$f" -C "$DATA_DIR/influxdb/engine/data/" 2>/dev/null; then
                DB_EXTRACTED=$((DB_EXTRACTED + 1))
            else
                DB_FAILED=$((DB_FAILED + 1))
                log_warn "  ✗ Failed: $(basename "$f")"
            fi
        done
        log_info "dbbackup shard result: extracted=$DB_EXTRACTED, failed=$DB_FAILED, total=$DB_TOTAL"

        if [ "$DB_TOTAL" -eq 0 ] || [ "$DB_FAILED" -gt 0 ] || [ "$DB_EXTRACTED" -ne "$DB_TOTAL" ]; then
            log_error "❌ dbbackup restore incomplete. Aborting."
            exit 1
        fi

        log_info "Final bucket directories after dbbackup restore:"
        sudo du -sh "$DATA_DIR/influxdb/engine/data/"*/ 2>/dev/null | sed 's/^/    /'

        sudo chmod -R 777 "$DATA_DIR/influxdb"

        log_info "Restarting InfluxDB with dbbackup data..."
        docker compose -p $PROJECT_NAME -f $COMPOSE_FILE up -d influxdb 2>/dev/null || docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE up -d influxdb 2>/dev/null
        sleep 10
        docker exec $INFLUXDB_CONTAINER influx ping 2>&1 || log_warn "InfluxDB not yet responsive"
    fi

    # 나머지 데이터 복사
    docker exec $WEB_CONTAINER mkdir -p /usr/local/smartsystems
    for dir in project log backup data processed gui; do
        if [ -d "$TRANSFER_TEMP/$dir" ]; then
            docker cp "$TRANSFER_TEMP/$dir" $WEB_CONTAINER:/usr/local/smartsystems/
            log_info "✅ $dir copied to SmartSystems"
        fi
    done

    # settings.json DB URL을 Docker 내부 주소로 변경
    log_info "Patching SmartSystems settings for Docker..."
    docker exec $WEB_CONTAINER sed -i 's|http://localhost:8086|http://influxdb:8086|g' /usr/local/smartsystems/project/settings.json 2>/dev/null && \
        log_info "✅ settings.json DBUrl patched (localhost → influxdb)" || log_warn "settings.json not found or patch failed"

    sudo rm -rf "$TRANSFER_TEMP"
else
    log_info "5. No Transfer.tar provided, skipping SmartSystems restore"
fi

# =================================================================
# 6. 서비스 재시작 (순서 중요: Redis → InfluxDB → Web)
# =================================================================
log_info "6. Restarting all services in order..."

docker restart $REDIS_CONTAINER
sleep 2

docker restart $INFLUXDB_CONTAINER
sleep 5

# Web 서버 재시작 (setup.json → Redis 로딩)
docker restart $WEB_CONTAINER
sleep 5

# =================================================================
# 7. 상태 확인
# =================================================================
log_info "7. Final status check..."
echo ""
docker ps --filter "name=sv500" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# InfluxDB 연결 확인
log_info "InfluxDB health:"
docker exec $INFLUXDB_CONTAINER influx ping 2>&1
echo ""

# InfluxDB 버킷 목록 확인 (토큰이 있으면)
if [ -f "${BACKUP_DIR}config/influx.json" ]; then
    log_info "influx.json content (for token reference):"
    cat "${BACKUP_DIR}config/influx.json"
    echo ""
fi

# =================================================================
# 8. 정리
# =================================================================
log_info "8. Cleaning up temp files..."
sudo rm -rf "$TEMP_DIR"

echo ""
log_info "✅ Restore complete!"
echo ""
OFFSET=$((NUMBER - 1))
WEB_PORT=$((4000 + OFFSET))
echo "Access web server at: http://<server-ip>:${WEB_PORT}"
echo ""
echo "If InfluxDB shows 401 errors, check that influx.json token"
echo "matches the restored InfluxDB instance."
echo ""