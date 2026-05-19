#!/usr/bin/env bash
# Regenerate metrics.json and related figures for the CHP vs stabilizer-python comparison.
# Schema written matches reports/chp_vs_stabilizer_assets/metrics.json (EPR, GHZ, Teleport (z);
# python: timing_ms, peak_alloc_kib, outcome_freq; chp: timing_ms, outcome_freq).
#
# Usage (from anywhere):
#   bash reports/chp_vs_stabilizer_assets/run_chp_vs_stabilizer_metrics.sh
# Optional env:
#   SKIP_BUILD=1    do not rebuild CHP
#   RUN_PYTEST=1    run stabilizer-python tests first
#   N=200 WARMUP=10 override benchmark sample counts (defaults match committed metrics.json)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${ROOT}"

N="${N:-200}"
WARMUP="${WARMUP:-10}"
CHP_DIR="${ROOT}/learning_material/CHP"
CHP_SRC="${CHP_DIR}/chp.c"
CHP_EXE="${CHP_DIR}/chp.exe"

if [[ ! -f "${CHP_SRC}" ]]; then
  echo "error: missing ${CHP_SRC}" >&2
  exit 1
fi

if [[ "${SKIP_BUILD:-0}" != "1" ]]; then
  echo "Building CHP -> ${CHP_EXE}"
  gcc -o "${CHP_EXE}" "${CHP_SRC}"
fi

if [[ ! -f "${CHP_EXE}" ]]; then
  echo "error: CHP executable not found at ${CHP_EXE} (build failed or wrong platform?)" >&2
  exit 1
fi

if [[ "${RUN_PYTEST:-0}" == "1" ]]; then
  echo "Running stabilizer-python tests"
  (cd "${ROOT}/stabilizer-python" && python -m pytest -q)
fi

echo "Running benchmark (writes metrics.json, plots, metrics_summary.md under reports/chp_vs_stabilizer_assets/)"
python "${ROOT}/reports/chp_vs_stabilizer_benchmark.py" --n "${N}" --warmup "${WARMUP}"

echo "Done."
