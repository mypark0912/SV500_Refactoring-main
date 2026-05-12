#!/bin/bash

# =================================================================
# restore_with_config.sh
#
# restore.sh의 변형 버전.
# 백업 tar 안에 config/ 폴더가 없는 구버전을 복원할 때 사용.
# --config 옵션으로 외부 config 디렉토리를 따로 지정할 수 있음.
#
# Usage:
#   ./restore_with_config.sh <backup_tar> [transfer_tar] \
#       --number N --config <config_dir>
#
# Example:
#   ./restore_with_config.sh sites/site-A/backup.tar \
#       sites/site-A/transfer.tar \
#       --number 7 \
#       --config /home/ntekdev/config_site_A
# =================================================================

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =================================================================
# 옵션 파싱
# =================================================================
NUMBER=1
EXTERNAL_CONFIG=""
POSITIONAL=()

while [ "$#" -gt 0 ]; do
  case $1 in
    --number)
      NUMBER="$2"
      shift 2
      ;;
    --config)
      EXTERNAL_CONFIG="$2"
      shift 2
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

if [ ${#POSITIONAL[@]} -eq 0 ]; then
    echo "Usage: $0 <backup_tar_file> [transfer_tar_file] --number N [--config <config_dir>]"
    echo ""
    echo "Example:"
    echo "  $0 sites/site-A/backup.tar sites/site-A/transfer.tar \\"
    echo "      --number 7 --config /home/ntekdev/config_site_A"
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
ENV_FILE=".env${NUMBER}"
PROJECT_NAME="sv500-${NUMBER}"

log_info "Restore target  : number=$NUMBER, project=$PROJECT_NAME"
log_info "Containers      : $INFLUXDB_CONTAINER / $REDIS_CONTAINER / $WEB_CONTAINER"
log_info "Backup tar      : $BACKUP_TAR"
if [ -n "$EXTERNAL_CONFIG" ]; then
    log_info "External config : $EXTERNAL_CONFIG"
fi

# tar 파일 존재 확인
if [ ! -f "$BACKUP_TAR" ]; then
    log_error "Backup file not found: $BACKUP_TAR"
    exit 1
fi

# external config 디렉토리 확인 (지정된 경우)
if [ -n "$EXTERNAL_CONFIG" ] && [ ! -d "$EXTERNAL_CONFIG" ]; then
    log_error "External config directory not found: $EXTERNAL_CONFIG"
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
# 1.5. 백업에 config가 없으면 외부 config 주입
# =================================================================
if [ ! -d "${BACKUP_DIR}config" ]; then
    if [ -n "$EXTERNAL_CONFIG" ]; then
        log_warn "Backup has no config/ folder. Injecting external config..."
        sudo mkdir -p "${BACKUP_DIR}config"
        sudo cp -a "$EXTERNAL_CONFIG/." "${BACKUP_DIR}config/"
        log_info "✅ External config injected into backup tree:"
        ls -la "${BACKUP_DIR}config/" | sed 's/^/    /'
    else
        log_warn "Backup has no config/ folder and --config not provided."
        log_warn "Web server may not start with correct settings."
    fi
else
    log_info "Backup already contains config/ folder"
    if [ -n "$EXTERNAL_CONFIG" ]; then
        log_warn "External config provided but backup has its own — using backup's config"
    fi
fi

# =================================================================
# 2. 모든 컨테이너 완전 중지
# =================================================================
log_info "2. Stopping all containers..."
cd "$SCRIPT_DIR"
docker compose -p $PROJECT_NAME -f $COMPOSE_FILE down 2>/dev/null || \
docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE down 2>/dev/null
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

# config 파일 호스트 쪽에 미리 복사 (마운트 사용시 대비)
log_info "Preparing config files on host..."
sudo mkdir -p "$DATA_DIR/config"
if [ -d "${BACKUP_DIR}config" ]; then
    if sudo cp -a "${BACKUP_DIR}config/." "$DATA_DIR/config/"; then
        sudo chmod -R 777 "$DATA_DIR/config"
        log_info "✅ Config copied to $DATA_DIR/config:"
        ls -la "$DATA_DIR/config/" | sed 's/^/    /'
    else
        log_error "Failed to copy config to $DATA_DIR/config"
        exit 1
    fi
fi

# influx restore --full은 일부 버킷 shard를 빠뜨리는 경우가 있어 파일 단위 복원만 사용
log_info "Stopping InfluxDB before file-level restore..."
docker compose -p $PROJECT_NAME -f $COMPOSE_FILE --env-file "$ENV_FILE" stop influxdb 2>/dev/null || \
docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE --env-file "$ENV_FILE" stop influxdb 2>/dev/null
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
docker compose -p $PROJECT_NAME -f $COMPOSE_FILE --env-file "$ENV_FILE" up -d influxdb 2>/dev/null || \
docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE --env-file "$ENV_FILE" up -d influxdb 2>/dev/null
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
# 4. 나머지 컨테이너 기동 + config 파일을 웹 컨테이너에 복사
# =================================================================
log_info "4. Starting remaining containers and copying config..."

# Redis, Web 시작 (--env-file 명시)
docker compose -p $PROJECT_NAME -f $COMPOSE_FILE --env-file "$ENV_FILE" up -d 2>/dev/null || \
docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE --env-file "$ENV_FILE" up -d 2>/dev/null
sleep 5

# 컨테이너가 실제로 떴는지 확인
if ! docker ps --format '{{.Names}}' | grep -q "^${WEB_CONTAINER}$"; then
    log_error "Web container $WEB_CONTAINER failed to start!"
    log_error "Showing recent logs:"
    docker ps -a --filter "name=$WEB_CONTAINER"
    docker logs $WEB_CONTAINER --tail 50 2>&1 || true
    exit 1
fi

# config 파일 웹 컨테이너에 docker cp (마운트가 없어도 들어가도록)
if [ -d "${BACKUP_DIR}config" ]; then
    log_info "Copying config files into web container..."
    # 폴더 통째로 복사 — setup.json, influx.json, user.db 등 한 번에
    docker cp "${BACKUP_DIR}config/." $WEB_CONTAINER:/home/root/config/
    log_info "✅ Config folder copied to $WEB_CONTAINER:/home/root/config/"
    docker exec $WEB_CONTAINER ls -la /home/root/config/ | sed 's/^/    /'
fi

# 로그 파일 복사
if [ -d "${BACKUP_DIR}logs" ]; then
    log_info "Copying log files..."
    sudo mkdir -p "$DATA_DIR/logs"
    sudo cp -a "${BACKUP_DIR}logs/." "$DATA_DIR/logs/"
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

    # transfer의 dbbackup이 main backup보다 일반적으로 더 완전한 스냅샷.
    # influx restore는 토큰 없이 401로 실패하므로 파일 단위 복원으로 재구성.
    if [ -d "$TRANSFER_TEMP/dbbackup" ]; then
        log_info "Found dbbackup in transfer — replacing InfluxDB state from dbbackup..."
        docker compose -p $PROJECT_NAME -f $COMPOSE_FILE --env-file "$ENV_FILE" stop influxdb 2>/dev/null || \
        docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE --env-file "$ENV_FILE" stop influxdb 2>/dev/null
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
        docker compose -p $PROJECT_NAME -f $COMPOSE_FILE --env-file "$ENV_FILE" up -d influxdb 2>/dev/null || \
        docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE --env-file "$ENV_FILE" up -d influxdb 2>/dev/null
        sleep 10
        docker exec $INFLUXDB_CONTAINER influx ping 2>&1 || log_warn "InfluxDB not yet responsive"
    fi

    docker exec $WEB_CONTAINER mkdir -p /usr/local/smartsystems
    for dir in project log backup data processed gui; do
        if [ -d "$TRANSFER_TEMP/$dir" ]; then
            docker cp "$TRANSFER_TEMP/$dir" $WEB_CONTAINER:/usr/local/smartsystems/
            log_info "✅ $dir copied to SmartSystems"
        fi
    done

    log_info "Patching SmartSystems settings for Docker..."
    docker exec $WEB_CONTAINER sed -i 's|http://localhost:8086|http://influxdb:8086|g' \
        /usr/local/smartsystems/project/settings.json 2>/dev/null && \
        log_info "✅ settings.json DBUrl patched (localhost → influxdb)" || \
        log_warn "settings.json not found or patch failed"

    sudo rm -rf "$TRANSFER_TEMP"
else
    log_info "5. No Transfer.tar provided, skipping SmartSystems restore"
fi

# =================================================================
# 6. 서비스 재시작 (순서: Redis → InfluxDB → Web)
#    + setup.json을 Redis에 강제 푸시
# =================================================================
log_info "6. Restarting all services in order..."

docker restart $REDIS_CONTAINER
sleep 3

docker restart $INFLUXDB_CONTAINER
sleep 5

# === 핵심 추가 ===
# Redis가 깨끗한 상태인 지금 web을 시작하면 init_setup()이 디스크의 setup.json을 푸시함.
# 그러나 init_setup()은 "Redis에 이미 있으면 스킵" 이므로 확실히 비워둠.
log_info "Clearing stale System keys in Redis..."
docker exec $REDIS_CONTAINER redis-cli HDEL System setup >/dev/null
docker exec $REDIS_CONTAINER redis-cli HDEL System mode >/dev/null

# Web 재시작 → 부팅 중 init_setup()이 setup.json을 Redis로 푸시
docker restart $WEB_CONTAINER
log_info "Waiting for web server to boot (10s)..."
sleep 10

# 한 번 더 확실하게 — /upload 엔드포인트로 강제 푸시 (Service.restart=1 까지 세팅)
log_info "Pushing setup.json to Redis via /upload endpoint..."
UPLOAD_RESULT=$(docker exec $WEB_CONTAINER curl -s -X POST \
    http://localhost:4000/upload \
    -F "file=@/home/root/config/setup.json" 2>&1)
echo "    $UPLOAD_RESULT"

if echo "$UPLOAD_RESULT" | grep -q '"passOK":"1"'; then
    log_info "✅ setup.json pushed to Redis"
    # Service.restart=1 처리를 위해 한 번 더 재시작
    docker restart $WEB_CONTAINER
    sleep 5
else
    log_warn "setup.json Redis upload via /upload failed (init_setup may have handled it)"
fi

# =================================================================
# 7. 상태 확인
# =================================================================
log_info "7. Final status check..."
echo ""
docker ps --filter "name=sv500-${NUMBER}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

log_info "InfluxDB health:"
docker exec $INFLUXDB_CONTAINER influx ping 2>&1
echo ""

log_info "Redis System keys:"
docker exec $REDIS_CONTAINER redis-cli HKEYS System
SETUP_LEN=$(docker exec $REDIS_CONTAINER redis-cli HSTRLEN System setup)
log_info "Redis System.setup length: $SETUP_LEN bytes"
if [ "$SETUP_LEN" = "0" ]; then
    log_warn "⚠️  Redis System.setup is EMPTY — web menu may not load properly"
fi
echo ""

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
echo "If menu does not appear correctly, check:"
echo "  1) Redis: docker exec $REDIS_CONTAINER redis-cli HSTRLEN System setup"
echo "  2) Logs : docker logs $WEB_CONTAINER --tail 50"
echo "  3) Config: docker exec $WEB_CONTAINER ls -la /home/root/config/"
echo ""
