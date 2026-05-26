#!/bin/bash
# Boot orchestrator (no-RTC-save variant):
#   1. Log RTC signals (system time / hwclock / shutdown marker)
#   2. Wait until redis/influxdb are ready
#   3. Start webserver (Type=notify, blocks until READY=1)
#   4. Start sv500A35
#
# startup-helper.sh 와 비교:
#   - last_known_time 파일 의존 없음 (time-keeper 안 쓰는 환경용)
#   - 시간 복구 로직 없음
#   - redis/influxdb 재시작 없음

LOG="/var/log/startup-helper.log"
MARKER="/usr/local/sv500/clean_shutdown"
REDIS_CLI="/home/root/bin/redis-cli"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"; }

# Ensure /usr/local is mounted
while ! mountpoint -q /usr/local; do
    sleep 1
done

log "===== Boot started (monitor, no-save-rtc) ====="

# ── Signal A: system time ─────────────────────────────────────────
NOW=$(date +%s)
log "A. system time : $(date) (epoch=$NOW)"

# ── Signal B: hardware RTC value ──────────────────────────────────
HW_RTC=$(hwclock -r 2>/dev/null || echo "N/A")
log "B. hwclock -r  : $HW_RTC"

# ── Signal D: clean shutdown marker ───────────────────────────────
if [ -f "$MARKER" ]; then
    SHUTDOWN_KIND="clean"
    rm -f "$MARKER"
else
    SHUTDOWN_KIND="UNEXPECTED"
fi
log "D. prev shutdown: $SHUTDOWN_KIND"

# Prepare Redis runtime directory
mkdir -p /var/run/redis
chown redis:redis /var/run/redis 2>/dev/null || true

# ── Wait for redis ready ──────────────────────────────────────────
log "→ Waiting for redis ready..."
for i in $(seq 1 60); do
    if "$REDIS_CLI" ping 2>/dev/null | grep -q PONG; then
        log "   redis ready (took ${i}s)"
        break
    fi
    sleep 1
done

# ── Start sv500A35 early (redis만 의지) ───────────────────────────
log "→ Starting sv500A35 (early, depends on redis only)..."
systemctl start sv500A35

# ── Wait for influxdb ready ───────────────────────────────────────
log "→ Waiting for influxdb ready..."
for i in $(seq 1 120); do
    if curl -sf http://localhost:8086/health >/dev/null 2>&1; then
        log "   influxdb ready (took ${i}s)"
        break
    fi
    sleep 1
done

# ── Start webserver (Type=notify, blocks until READY=1) ───────────
log "→ Starting webserver (Type=notify, blocks until READY=1)..."
systemctl start webserver
log "   webserver active"

log "===== All services started ====="
