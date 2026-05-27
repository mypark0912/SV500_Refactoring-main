#!/bin/bash
# Boot 로깅 + RTC 복구 only:
#   1. RTC 신호 로깅 (system time / hwclock / last_known_time / shutdown marker)
#   2. last_known_time 파일 있으면 → RTC 리셋 감지 + 시간 복구
#      파일 없으면(=time-keeper 없는 nosavertc 모드) → RTC 복구 skip
#   3. 시간 복구된 경우 redis/influxdb 재시작
#
# webserver / core / sv500A35 / smartsystems* 는 모두 systemd enable 되어 있고
# After= 체인으로 자동 시작됨. 여기서는 안 건드림.

LOG="/var/log/startup-monitor.log"
TIME_FILE="/usr/local/sv500/last_known_time"
MARKER="/usr/local/sv500/clean_shutdown"
RESET_THRESHOLD=86400          # 24h
MIN_VALID_EPOCH=1704067200     # 2024-01-01 (fallback when no last_known)

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"; }

# Ensure /usr/local is mounted before reading time file
while ! mountpoint -q /usr/local; do
    sleep 1
done

log "===== Boot started ====="

# ── Signal A: system time ─────────────────────────────────────────
NOW=$(date +%s)
log "A. system time : $(date) (epoch=$NOW)"

# ── Signal B: hardware RTC value ──────────────────────────────────
HW_RTC=$(hwclock -r 2>/dev/null || echo "N/A")
log "B. hwclock -r  : $HW_RTC"

# ── Signal C: last known time from heartbeat (optional) ──────────
if [ -f "$TIME_FILE" ]; then
    LAST_KNOWN=$(cat "$TIME_FILE" 2>/dev/null || echo 0)
    log "C. last_known  : $(date -d @$LAST_KNOWN 2>/dev/null || echo invalid) (epoch=$LAST_KNOWN)"
else
    LAST_KNOWN=0
    log "C. last_known  : <file not found, RTC recovery disabled>"
fi

# ── Signal D: clean shutdown marker ───────────────────────────────
if [ -f "$MARKER" ]; then
    SHUTDOWN_KIND="clean"
    rm -f "$MARKER"
else
    SHUTDOWN_KIND="UNEXPECTED"
fi
log "D. prev shutdown: $SHUTDOWN_KIND"

# ── Reset detection (only when last_known_time exists) ────────────
RESET_DETECTED=0
if [ "$LAST_KNOWN" -gt 0 ]; then
    DIFF=$((LAST_KNOWN - NOW))
    if [ "$DIFF" -gt "$RESET_THRESHOLD" ]; then
        log "→ RTC RESET DETECTED: system time is ${DIFF}s (>=24h) before last_known"
        RESET_DETECTED=1
    else
        log "→ Time looks consistent (diff=${DIFF}s vs last_known)"
    fi
elif [ "$NOW" -lt "$MIN_VALID_EPOCH" ]; then
    log "→ RTC RESET SUSPECTED: no last_known and system time before 2024-01-01"
fi

if [ "$RESET_DETECTED" = "1" ]; then
    if [ "$SHUTDOWN_KIND" = "UNEXPECTED" ]; then
        log "   inferred trigger: power loss during shutdown (motor start?)"
    else
        log "   inferred trigger: reset during boot (unusual)"
    fi
fi

# ── Time recovery (only when last_known_time is available) ────────
TIME_RECOVERED=0
if [ "$RESET_DETECTED" = "1" ] && [ "$LAST_KNOWN" -gt 0 ]; then
    log "→ Restoring time from last_known"
    date -s "@$LAST_KNOWN" >/dev/null 2>&1
    hwclock --systohc 2>/dev/null || true
    log "   restored system : $(date)"
    log "   restored hwclock: $(hwclock -r 2>/dev/null || echo N/A)"
    TIME_RECOVERED=1
fi

# Prepare Redis runtime directory (redis 가 필요로 함)
mkdir -p /var/run/redis
chown redis:redis /var/run/redis 2>/dev/null || true

# ── Restart redis/influxdb if time was recovered ──────────────────
# 둘 다 enable 되어있어 systemd 가 시작하지만, 시간이 보정됐다면
# 옛 시각으로 시작했을 가능성 → 재시작해서 올바른 시각으로 복귀.
if [ "$TIME_RECOVERED" = "1" ]; then
    log "→ Restarting redis and influxdb to apply corrected time"
    systemctl restart redis 2>/dev/null || true
    systemctl restart influxdb 2>/dev/null || true
fi

log "===== Boot logging done (services 는 systemd 가 After= 체인으로 자동 기동) ====="
