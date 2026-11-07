#!/usr/bin/env bash
set -euo pipefail
umask 077
command -v python3 >/dev/null 2>&1 || { printf 'Falta Python 3.\n'; exit 1; }
PPP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
exec python3 "$PPP_DIR/inspeccionar.py" "$@"
