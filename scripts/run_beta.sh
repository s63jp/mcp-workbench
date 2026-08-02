#!/usr/bin/env bash
# MCP Workbench Beta Supervisor
# Starts the server and tunnel, monitors both, handles crashes.
# Designed to survive shell exit.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

SERVER_PORT="${SERVER_PORT:-3460}"
TUNNEL_LOG="$LOG_DIR/tunnel.log"
SERVER_LOG="$LOG_DIR/server.log"
PID_FILE="$LOG_DIR/server.pid"
TUNNEL_PID_FILE="$LOG_DIR/tunnel.pid"

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG_DIR/supervisor.log"; }

start_server() {
    # Check if port is already in use by a healthy server
    if curl -sf "http://localhost:$SERVER_PORT/api/health" > /dev/null 2>&1; then
        log "Port $SERVER_PORT already serving (preserving existing server)"
        EXISTING_PID=$(ss -tlnp | grep ":$SERVER_PORT " | grep -oP 'pid=\K[0-9]+' | head -1)
        if [ -n "$EXISTING_PID" ]; then
            echo "$EXISTING_PID" > "$PID_FILE"
            log "Recorded existing server pid $EXISTING_PID"
        fi
        return 0
    fi
    # Clean up stale PID file if present
    [ -f "$PID_FILE" ] && ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null && rm -f "$PID_FILE"
    log "Starting MCP Workbench server on port $SERVER_PORT..."
    cd "$PROJECT_DIR"
    # setsid creates a new session, detaching from this shell completely
    setsid nohup python3 server.py "$SERVER_PORT" > "$SERVER_LOG" 2>&1 < /dev/null &
    echo $! > "$PID_FILE"
    sleep 3
    if curl -sf "http://localhost:$SERVER_PORT/api/health" > /dev/null 2>&1; then
        log "Server healthy (pid $(cat "$PID_FILE"))"
    else
        log "Server failed health check. Check $SERVER_LOG"
        return 1
    fi
}

start_tunnel() {
    if [ -f "$TUNNEL_PID_FILE" ] && kill -0 "$(cat "$TUNNEL_PID_FILE")" 2>/dev/null; then
        log "Tunnel already running (pid $(cat "$TUNNEL_PID_FILE"))"
        return 0
    fi
    log "Starting Cloudflare tunnel..."
    cd "$PROJECT_DIR"
    setsid nohup cloudflared tunnel --url "http://localhost:$SERVER_PORT" > "$TUNNEL_LOG" 2>&1 < /dev/null &
    echo $! > "$TUNNEL_PID_FILE"
    sleep 8
    URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$TUNNEL_LOG" | head -1)
    if [ -n "$URL" ]; then
        log "Tunnel active: $URL"
        echo "$URL" > "$LOG_DIR/public_url.txt"
    else
        log "Tunnel failed to start. Check $TUNNEL_LOG"
    fi
}

stop() {
    log "Stopping..."
    [ -f "$PID_FILE" ] && kill "$(cat "$PID_FILE")" 2>/dev/null && rm -f "$PID_FILE"
    [ -f "$TUNNEL_PID_FILE" ] && kill "$(cat "$TUNNEL_PID_FILE")" 2>/dev/null && rm -f "$TUNNEL_PID_FILE"
    log "Stopped"
}

status() {
    [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null && echo "Server: running (pid $(cat "$PID_FILE"))" || echo "Server: stopped"
    [ -f "$TUNNEL_PID_FILE" ] && kill -0 "$(cat "$TUNNEL_PID_FILE")" 2>/dev/null && echo "Tunnel: running (pid $(cat "$TUNNEL_PID_FILE"))" || echo "Tunnel: stopped"
    [ -f "$LOG_DIR/public_url.txt" ] && echo "URL: $(cat "$LOG_DIR/public_url.txt")"
}

# Simple monitor loop
monitor() {
    log "Monitoring. Ctrl+C to stop, or run $0 stop from another terminal."
    while true; do
        sleep 30
        if [ -f "$PID_FILE" ] && ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            log "Server crashed. Restarting..."
            rm -f "$PID_FILE"
            start_server
        fi
        if [ -f "$TUNNEL_PID_FILE" ] && ! kill -0 "$(cat "$TUNNEL_PID_FILE")" 2>/dev/null; then
            log "Tunnel died. Restarting..."
            rm -f "$TUNNEL_PID_FILE"
            start_tunnel
        fi
    done
}

case "${1:-start}" in
    start)   start_server; start_tunnel; status ;;
    stop)    stop ;;
    status)  status ;;
    restart) stop; start_server; start_tunnel; status ;;
    monitor) monitor ;;
    *)       echo "Usage: $0 {start|stop|status|restart|monitor}"; exit 1 ;;
esac
