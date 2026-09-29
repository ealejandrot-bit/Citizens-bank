#!/usr/bin/env bash
# Ejecuta el scorecard de punta a punta (pasos 00–17). Se detiene en el primer QC gate fallido.
set -euo pipefail
cd "$(dirname "$0")/src"
export PYTHONHASHSEED=42
for s in $(ls [0-9][0-9]_*.py | sort); do
  echo "════════ $s ════════"
  python3 "$s"
done
