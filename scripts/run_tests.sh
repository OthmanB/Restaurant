#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="${ROOT_DIR}/.venv/bin/python"

if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo "Error: virtual environment python not found at ${VENV_PYTHON}" >&2
  echo "Create it with: python3 -m venv .venv && .venv/bin/pip install numpy scipy matplotlib pyyaml" >&2
  exit 1
fi

export PYTHONPATH="${ROOT_DIR}/sources:${ROOT_DIR}"

TEST_TARGET="${1:-all}"

case "${TEST_TARGET}" in
  all)
    "${VENV_PYTHON}" -m unittest discover -s "${ROOT_DIR}/tests" -p "test_*.py"
    ;;
  fast)
    "${VENV_PYTHON}" -m unittest       tests.test_config_loading       tests.test_sweep_generation
    ;;
  properties)
    "${VENV_PYTHON}" -m unittest       tests.test_math_properties       tests.test_system_invariants
    ;;
  simulation)
    "${VENV_PYTHON}" -m unittest       tests.test_simulation_outputs
    ;;
  *)
    # Pass-through mode: allow explicit module/path arguments
    "${VENV_PYTHON}" -m unittest "${TEST_TARGET}"
    ;;
esac
