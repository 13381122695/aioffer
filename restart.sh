#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

target="${1:-all}"
"${ROOT_DIR}/stop.sh" "${target}" || true
sleep 1
"${ROOT_DIR}/start.sh" "${target}"
"${ROOT_DIR}/status.sh" "${target}"

