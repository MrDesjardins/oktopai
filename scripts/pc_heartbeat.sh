#!/usr/bin/env bash
set -u

interval_seconds="${1:-60}"
duration_seconds="${2:-10800}"
output_path="${3:-.oktopai/logs/pc-heartbeat.log}"

mkdir -p "$(dirname "$output_path")"
start_epoch="$(date +%s)"
end_epoch=$((start_epoch + duration_seconds))

record() {
  printf '\n=== heartbeat %s ===\n' "$(date --iso-8601=seconds)" >> "$output_path"
  printf 'load: ' >> "$output_path"
  timeout 10s uptime >> "$output_path" 2>&1 || printf 'unavailable\n' >> "$output_path"
  printf 'memory:\n' >> "$output_path"
  timeout 10s free -h >> "$output_path" 2>&1 || true
  printf 'disk:\n' >> "$output_path"
  timeout 10s df -h . >> "$output_path" 2>&1 || true
  printf 'gpu:\n' >> "$output_path"
  timeout 10s nvidia-smi --query-gpu=timestamp,name,memory.used,memory.free,utilization.gpu,temperature.gpu --format=csv,noheader >> "$output_path" 2>&1 || true
  printf 'relevant processes:\n' >> "$output_path"
  timeout 10s ps -eo pid,etime,%cpu,%mem,rss,cmd --sort=-rss >> "$output_path" 2>&1 || true
}

trap 'record; exit 0' INT TERM
while [ "$(date +%s)" -lt "$end_epoch" ]; do
  record
  sleep "$interval_seconds"
done
