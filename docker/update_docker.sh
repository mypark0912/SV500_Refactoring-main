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
# Usage: ./update_docker.sh --number <N>
# =================================================================
NUMBER=""
while [ "$#" -gt 0 ]; do
  case $1 in
    --number)
      NUMBER="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 --number <N>"
      exit 1
      ;;
  esac
done

if [ -z "$NUMBER" ]; then
    log_error "--number is required"
    echo "Usage: $0 --number <N>"
    exit 1
fi

# 숫자인지 확인
if ! echo "$NUMBER" | grep -qE '^[0-9]+$'; then
    log_error "--number must be a positive integer"
    exit 1
fi

# =================================================================
# 기본 포트 (number=1 기준)
# =================================================================
BASE_INFLUX_PORT=8087
BASE_REDIS_PORT=6380
BASE_WEB_PORT=4000
BASE_SMART_PORT=5000

# number 값에 따라 포트 계산 (1이 기본값이므로 N-1 만큼 더함)
OFFSET=$((NUMBER - 1))
INFLUX_PORT=$((BASE_INFLUX_PORT + OFFSET))
REDIS_PORT=$((BASE_REDIS_PORT + OFFSET))
WEB_PORT=$((BASE_WEB_PORT + OFFSET))
SMART_PORT=$((BASE_SMART_PORT + OFFSET))
DATA_DIR="./data${NUMBER}"
PROJECT_NAME="sv500-${NUMBER}"

log_info "Number   : $NUMBER"
log_info "Project  : $PROJECT_NAME"
log_info "Ports    : InfluxDB=$INFLUX_PORT, Redis=$REDIS_PORT, Web=$WEB_PORT, SmartSystems=$SMART_PORT"
log_info "Data dir : $DATA_DIR"

# =================================================================
# .env 파일 생성
# =================================================================
ENV_FILE=".env${NUMBER}"

cat > "$ENV_FILE" <<EOF
PROJECT_NAME=${PROJECT_NAME}
INFLUX_PORT=${INFLUX_PORT}
REDIS_PORT=${REDIS_PORT}
WEB_PORT=${WEB_PORT}
SMART_PORT=${SMART_PORT}
DATA_DIR=${DATA_DIR}
EOF

log_info "✅ Generated $ENV_FILE"

# =================================================================
# docker-compose.yml 에서 container_name 을 PROJECT_NAME 기반으로 치환
# =================================================================
COMPOSE_FILE="docker-compose.yml"
TEMP_COMPOSE="docker-compose.${NUMBER}.yml"

sed \
    -e "s/container_name: sv500-influxdb/container_name: sv500-influxdb-${NUMBER}/g" \
    -e "s/container_name: sv500-redis/container_name: sv500-redis-${NUMBER}/g" \
    -e "s/container_name: sv500-web/container_name: sv500-web-${NUMBER}/g" \
    -e "s|\${INFLUX_PORT:-8087}|${INFLUX_PORT}|g" \
    -e "s|\${REDIS_PORT:-6380}|${REDIS_PORT}|g" \
    -e "s|\${WEB_PORT:-4000}|${WEB_PORT}|g" \
    -e "s|\${SMART_PORT:-5000}|${SMART_PORT}|g" \
    -e "s|\${DATA_DIR:-./data}|${DATA_DIR}|g" \
    -e "s|\${DATA_DIR}|${DATA_DIR}|g" \
    "$COMPOSE_FILE" > "$TEMP_COMPOSE"

log_info "✅ Generated $TEMP_COMPOSE"

# =================================================================
# 데이터 디렉토리 생성
# =================================================================
mkdir -p "$DATA_DIR/influxdb"
mkdir -p "$DATA_DIR/logs"
mkdir -p "$DATA_DIR/trendcsv"
mkdir -p "$DATA_DIR/smartsystems"
log_info "✅ Data directories created: $DATA_DIR"

# =================================================================
# docker compose 빌드 및 실행
# =================================================================
log_info "Building containers..."
docker compose -p "$PROJECT_NAME" -f "$TEMP_COMPOSE" --env-file "$ENV_FILE" build

log_info "Starting containers with project: $PROJECT_NAME ..."
docker compose -p "$PROJECT_NAME" -f "$TEMP_COMPOSE" --env-file "$ENV_FILE" up -d

echo ""
log_info "✅ Done!"
echo ""
echo "=== Summary ==="
echo "- Project     : $PROJECT_NAME"
echo "- InfluxDB    : http://localhost:$INFLUX_PORT"
echo "- Redis       : localhost:$REDIS_PORT"
echo "- Web         : http://localhost:$WEB_PORT"
echo "- SmartSystems: http://localhost:$SMART_PORT"
echo "- Data dir    : $DATA_DIR"
echo "- Compose     : $TEMP_COMPOSE"
echo "- Env file    : $ENV_FILE"
echo ""
echo "=== Container Names ==="
echo "- sv500-influxdb-${NUMBER}"
echo "- sv500-redis-${NUMBER}"
echo "- sv500-web-${NUMBER}"
echo ""
echo "To stop:"
echo "  docker compose -p $PROJECT_NAME -f $TEMP_COMPOSE down"
echo ""