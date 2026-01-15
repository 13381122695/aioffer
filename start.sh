#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="${ROOT_DIR}/.run"
LOG_DIR="${ROOT_DIR}/.logs"
mkdir -p "${RUN_DIR}" "${LOG_DIR}"

BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
BACKEND_RELOAD="${BACKEND_RELOAD:-1}"
BACKEND_PYTHON="${BACKEND_PYTHON:-python3}"

FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
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

start_backend() {
  local pid_file="${RUN_DIR}/backend.pid"
  if [[ -f "${pid_file}" ]]; then
    local pid
    pid="$(cat "${pid_file}" 2>/dev/null || true)"
    if pid_alive "${pid}"; then
      echo "backend: already running (pid=${pid})"
      return 0
    fi
    rm -f "${pid_file}"
  fi

  local existing
  existing="$(port_pid "${BACKEND_PORT}")"
  if [[ -n "${existing}" ]]; then
    echo "backend: port ${BACKEND_PORT} already in use (pid=${existing})"
    return 0
  fi

  local reload_flag=""
  if [[ "${BACKEND_RELOAD}" == "1" || "${BACKEND_RELOAD}" == "true" ]]; then
    reload_flag="--reload"
  fi

  local cmd
  cmd="${BACKEND_PYTHON} -m uvicorn main:app ${reload_flag} --host ${BACKEND_HOST} --port ${BACKEND_PORT}"

  (
    cd "${ROOT_DIR}/backend"
    if command -v setsid >/dev/null 2>&1; then
      nohup setsid bash -c "${cmd}" > "${LOG_DIR}/backend.log" 2>&1 &
    else
      nohup bash -c "${cmd}" > "${LOG_DIR}/backend.log" 2>&1 &
    fi
    echo $! > "${pid_file}"
  )

  echo "backend: started (pid=$(cat "${pid_file}"), port=${BACKEND_PORT})"
}

start_frontend() {
  local pid_file="${RUN_DIR}/frontend.pid"
  if [[ -f "${pid_file}" ]]; then
    local pid
    pid="$(cat "${pid_file}" 2>/dev/null || true)"
    if pid_alive "${pid}"; then
      echo "frontend: already running (pid=${pid})"
      return 0
    fi
    rm -f "${pid_file}"
  fi

  local existing
  existing="$(port_pid "${FRONTEND_PORT}")"
  if [[ -n "${existing}" ]]; then
    echo "frontend: port ${FRONTEND_PORT} already in use (pid=${existing})"
    return 0
  fi

  local cmd
  cmd="npm run dev -- --host ${FRONTEND_HOST} --port ${FRONTEND_PORT}"

  (
    cd "${ROOT_DIR}/frontend"
    if command -v setsid >/dev/null 2>&1; then
      nohup setsid bash -c "${cmd}" > "${LOG_DIR}/frontend.log" 2>&1 &
    else
      nohup bash -c "${cmd}" > "${LOG_DIR}/frontend.log" 2>&1 &
    fi
    echo $! > "${pid_file}"
  )

  echo "frontend: started (pid=$(cat "${pid_file}"), port=${FRONTEND_PORT})"
}

usage() {
  echo "Usage: $0 [all|backend|frontend]"
}

target="${1:-all}"
case "${target}" in
  all)
    start_backend
    start_frontend
    ;;
  backend)
    start_backend
    ;;
  frontend)
    start_frontend
    ;;
  *)
    usage
    exit 2
    ;;
esac

