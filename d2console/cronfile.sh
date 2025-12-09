#!/usr/bin/env bash
# write current system uptime seconds to /var/www/html/d2console/data/server_uptime.txt
OUT="/var/www/html/d2console/data/server_uptime.txt"
if [ -r /proc/uptime ]; then
  # first field is seconds with fraction
  uptime_seconds=$(awk '{printf("%.0f",$1)}' /proc/uptime)
  echo "$uptime_seconds" > "$OUT"
fi
