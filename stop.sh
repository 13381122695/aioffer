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

pg_kill() {
  local pid="$1"
  if ! pid_alive "${pid}"; then
    return 0
  fi
  kill -- "-${pid}" >/dev/null 2>&1 || kill "${pid}" >/dev/null 2>&1 || true
}

wait_stop() {
  local pid="$1"
  local seconds="${2:-10}"
  local i=0
  while pid_alive "${pid}" && [[ "${i}" -lt "${seconds}" ]]; do
    sleep 1
    i=$((i + 1))
  done
  if pid_alive "${pid}"; then
    kill -9 -- "-${pid}" >/dev/null 2>&1 || kill -9 "${pid}" >/dev/null 2>&1 || true
  fi
}

port_pids() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true
    return 0
  fi
  if command -v ss >/dev/null 2>&1; then
    ss -lptn "sport = :${port}" 2>/dev/null | awk -F'pid=' 'NF>1{print $2}' | awk -F',' '{print $1}' || true
    return 0
  fi
  echo ""
}

matches_cmd() {
  local pid="$1"
  local needle="$2"
  local args
  args="$(ps -p "${pid}" -o args= 2>/dev/null || true)"
  [[ "${args}" == *"${needle}"* ]]
}

stop_by_pidfile() {
  local pid_file="$1"
  local name="$2"
  if [[ ! -f "${pid_file}" ]]; then
    return 1
  fi
  local pid
  pid="$(cat "${pid_file}" 2>/dev/null || true)"
  rm -f "${pid_file}"
  if [[ -z "${pid}" ]]; then
    echo "${name}: pidfile empty"
    return 0
  fi
  if ! pid_alive "${pid}"; then
    echo "${name}: not running"
    return 0
  fi
  pg_kill "${pid}"
  wait_stop "${pid}" 10
  echo "${name}: stopped"
  return 0
}

stop_backend() {
  local pid_file="${RUN_DIR}/backend.pid"
  if stop_by_pidfile "${pid_file}" "backend"; then
    return 0
  fi

  local pids
  pids="$(port_pids "${BACKEND_PORT}")"
  if [[ -z "${pids}" ]]; then
    echo "backend: not running"
    return 0
  fi
  local stopped=0
  for pid in ${pids}; do
    if matches_cmd "${pid}" "uvicorn" && matches_cmd "${pid}" "main:app"; then
      pg_kill "${pid}"
      wait_stop "${pid}" 10
      stopped=1
    fi
  done
  if [[ "${stopped}" -eq 1 ]]; then
    echo "backend: stopped"
  else
    echo "backend: found pid(s) on port ${BACKEND_PORT}, but not matching uvicorn main:app"
    return 1
  fi
}

stop_frontend() {
  local pid_file="${RUN_DIR}/frontend.pid"
  if stop_by_pidfile "${pid_file}" "frontend"; then
    return 0
  fi

  local pids
  pids="$(port_pids "${FRONTEND_PORT}")"
  if [[ -z "${pids}" ]]; then
    echo "frontend: not running"
    return 0
  fi
  local stopped=0
  for pid in ${pids}; do
    if matches_cmd "${pid}" "vite" || matches_cmd "${pid}" "npm run dev"; then
      pg_kill "${pid}"
      wait_stop "${pid}" 10
      stopped=1
    fi
  done
  if [[ "${stopped}" -eq 1 ]]; then
    echo "frontend: stopped"
  else
    echo "frontend: found pid(s) on port ${FRONTEND_PORT}, but not matching vite"
    return 1
  fi
}

usage() {
  echo "Usage: $0 [all|backend|frontend]"
}

target="${1:-all}"
case "${target}" in
  all)
    stop_frontend || true
    stop_backend || true
    ;;
  backend)
    stop_backend
    ;;
  frontend)
    stop_frontend
    ;;
  *)
    usage
    exit 2
    ;;
esac

