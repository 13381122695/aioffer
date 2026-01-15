#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="${ROOT_DIR}/.run"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

pid_alive() {
  local pid="$1"
  [[ -n "${pid}" ]] && kill -0 "${pid}" >/dev/null 2>&1
}

port_pid() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null | head -n 1 || true
    return 0
  fi
  if command -v ss >/dev/null 2>&1; then
    ss -lptn "sport = :${port}" 2>/dev/null | awk -F'pid=' 'NF>1{print $2}' | awk -F',' 'NR==1{print $1}' || true
    return 0
  fi
  echo ""
}

show_one() {
  local name="$1"
  local pid_file="$2"
  local port="$3"

  local pid=""
  if [[ -f "${pid_file}" ]]; then
    pid="$(cat "${pid_file}" 2>/dev/null || true)"
  fi

  if [[ -n "${pid}" ]] && pid_alive "${pid}"; then
    echo "${name}: running (pid=${pid}, port=${port}, managed=yes)"
    return 0
  fi

  local p
  p="$(port_pid "${port}")"
  if [[ -n "${p}" ]]; then
    echo "${name}: running (pid=${p}, port=${port}, managed=no)"
    return 0
  fi

  echo "${name}: stopped (port=${port})"
}

usage() {
  echo "Usage: $0 [all|backend|frontend]"
}

target="${1:-all}"
case "${target}" in
  all)
    show_one "backend" "${RUN_DIR}/backend.pid" "${BACKEND_PORT}"
    show_one "frontend" "${RUN_DIR}/frontend.pid" "${FRONTEND_PORT}"
    ;;
  backend)
    show_one "backend" "${RUN_DIR}/backend.pid" "${BACKEND_PORT}"
    ;;
  frontend)
    show_one "frontend" "${RUN_DIR}/frontend.pid" "${FRONTEND_PORT}"
    ;;
  *)
    usage
    exit 2
    ;;
esac

