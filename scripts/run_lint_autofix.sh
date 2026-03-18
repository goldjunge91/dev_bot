#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Repo note:
# - This repository contains both ROS2 packages and PlatformIO firmware sources.
# - This script is intentionally for ROS2 linting only.
# - Scope is restricted to src/**, excluding src/serial.

if [[ -f /opt/ros/humble/setup.bash ]]; then
  # shellcheck disable=SC1091
  source /opt/ros/humble/setup.bash
fi

if [[ -f install/setup.bash ]]; then
  # shellcheck disable=SC1091
  source install/setup.bash
fi

FAIL=0
TARGET_PATHS=()

while IFS= read -r -d '' dir; do
  base="$(basename "$dir")"
  if [[ "$base" == "serial" ]]; then
    continue
  fi
  TARGET_PATHS+=("$dir")
done < <(find src -mindepth 1 -maxdepth 1 -type d -print0)

if [[ ${#TARGET_PATHS[@]} -eq 0 ]]; then
  echo "No target package directories found under src/ (after exclusions)."
  exit 0
fi

run_step() {
  local label="$1"
  shift
  echo
  echo "==> $label"
  if "$@"; then
    echo "[OK] $label"
  else
    echo "[FAIL] $label"
    FAIL=1
  fi
}

echo "Target paths: ${TARGET_PATHS[*]}"

run_step "Reformat C/C++ with uncrustify (ROS2 targets only)" ament_uncrustify --reformat "${TARGET_PATHS[@]}"
run_step "Apply custom lint autofixes (safe-only)" python3 scripts/lint_autofix.py --path src --exclude serial

run_step "Run cppcheck" env AMENT_CPPCHECK_ALLOW_SLOW_VERSIONS=1 ament_cppcheck "${TARGET_PATHS[@]}"
run_step "Run cpplint" ament_cpplint "${TARGET_PATHS[@]}"
run_step "Run flake8" ament_flake8 "${TARGET_PATHS[@]}"
run_step "Run lint_cmake" ament_lint_cmake "${TARGET_PATHS[@]}"
run_step "Run pep257" ament_pep257 "${TARGET_PATHS[@]}"
run_step "Run xmllint" ament_xmllint "${TARGET_PATHS[@]}"
run_step "Run uncrustify (check mode)" ament_uncrustify "${TARGET_PATHS[@]}"

echo
if [[ "$FAIL" -eq 0 ]]; then
  echo "Lint autofix pipeline completed successfully."
else
  echo "Lint autofix pipeline completed with remaining errors."
fi

exit "$FAIL"
