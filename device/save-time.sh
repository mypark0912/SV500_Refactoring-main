#!/bin/bash
# Persist current epoch for boot-time RTC recovery.
# Invoked every 60s by time-keeper.timer.

TIME_FILE="/usr/local/sv500/last_known_time"
mkdir -p "$(dirname "$TIME_FILE")"
date '+%s' > "$TIME_FILE"
