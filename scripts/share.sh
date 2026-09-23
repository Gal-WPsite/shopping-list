#!/usr/bin/env bash
# Serve a built list (with shared live state) and open a temporary public Cloudflare Quick Tunnel to it.
#   share.sh start <dir> [port=8765] [ttl-seconds=0, never closes]
#   share.sh stop [port=8765]
# Needs python3 and cloudflared (brew install cloudflared). No Cloudflare account required.
set -euo pipefail

cmd=${1:-}
state_dir=${TMPDIR:-/tmp}/shopping-list-share
mkdir -p "$state_dir"

stop() {
  local port=$1 f
  for f in "$state_dir/$port".{server,tunnel,timer}.pid; do
    [[ -f $f ]] && kill "$(cat "$f")" 2>/dev/null || true
    rm -f "$f"
  done
}

case $cmd in
  start)
    dir=${2:?usage: share.sh start <dir> [port] [ttl]}
    port=${3:-8765}
    ttl=${4:-0}
    [[ -f $dir/index.html ]] || { echo "no index.html in $dir" >&2; exit 1; }
    command -v cloudflared >/dev/null || { echo "cloudflared not found (brew install cloudflared)" >&2; exit 1; }
    stop "$port"
    log=$state_dir/$port.log
    nohup python3 "$(dirname "$0")/server.py" "$dir" "$port" >/dev/null 2>&1 &
    echo $! >"$state_dir/$port.server.pid"
    # --config /dev/null: never inherit ingress rules from ~/.cloudflared/config.yml,
    # which would make every request hit a named tunnel's catch-all 404.
    nohup cloudflared tunnel --config /dev/null --no-autoupdate --url "http://127.0.0.1:$port" >"$log" 2>&1 &
    echo $! >"$state_dir/$port.tunnel.pid"
    url=
    for _ in $(seq 1 60); do
      url=$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$log" | head -1 || true)
      [[ -n $url ]] && break
      sleep 1
    done
    [[ -n $url ]] || { echo "tunnel did not start, see $log" >&2; stop "$port"; exit 1; }
    if [[ $ttl != 0 ]]; then
      nohup bash -c "sleep $ttl; '$0' stop $port" >/dev/null 2>&1 &
      echo $! >"$state_dir/$port.timer.pid"
    fi
    # The new hostname takes a few seconds to resolve; ask a public resolver so a
    # cached miss on this machine does not make a working link look dead.
    status=000
    for _ in $(seq 1 30); do
      ip=$(dig +short @1.1.1.1 "${url#https://}" A 2>/dev/null | head -1 || true)
      if [[ -n $ip ]]; then
        status=$(curl -s -o /dev/null -w '%{http_code}' --resolve "${url#https://}:443:$ip" "$url/" || true)
        [[ $status == 200 ]] && break
      fi
      sleep 2
    done
    echo "url=$url"
    echo "status=$status"
    [[ $ttl == 0 ]] && echo "auto_close=never" || echo "auto_close_in=${ttl}s"
    ;;
  stop)
    stop "${2:-8765}"
    echo "stopped"
    ;;
  *)
    sed -n '2,5p' "$0" >&2
    exit 1
    ;;
esac
