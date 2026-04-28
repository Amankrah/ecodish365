#!/bin/bash
# Memory watchdog — runs via cron every 5 minutes.
# If available memory drops below the threshold, restarts Gunicorn workers
# (which are the biggest memory consumers due to CNF data singletons).
#
# Install:
#   sudo cp deploy/scripts/memory-watchdog.sh /usr/local/bin/ecodish365-memory-watchdog.sh
#   sudo chmod +x /usr/local/bin/ecodish365-memory-watchdog.sh
#   (crontab -l; echo "*/5 * * * * /usr/local/bin/ecodish365-memory-watchdog.sh") | crontab -

THRESHOLD_MB=500  # restart if available memory falls below this
LOG="/var/log/ecodish365/memory-watchdog.log"

available_kb=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
available_mb=$((available_kb / 1024))
total_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
total_mb=$((total_kb / 1024))
used_mb=$((total_mb - available_mb))
pct=$((used_mb * 100 / total_mb))

if [ "$available_mb" -lt "$THRESHOLD_MB" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') WARN available=${available_mb}MB (<${THRESHOLD_MB}MB) — restarting gunicorn" >> "$LOG"
    systemctl restart ecodish365-gunicorn
    # Clear file-based Django cache to free disk I/O pressure
    rm -rf /tmp/ecodish365-cache/* 2>/dev/null
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO gunicorn restarted, cache cleared" >> "$LOG"
else
    # Log hourly (every 12th run) for baseline visibility
    minute=$(date +%M)
    if [ "$((minute % 60))" -lt 5 ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') OK available=${available_mb}MB used=${used_mb}MB (${pct}%)" >> "$LOG"
    fi
fi
