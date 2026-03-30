#!/bin/bash
# ============================================================
# run_abtest.sh  — run both A (Slurm) and B (SGE) pipelines
# and compare exit codes.
#
# Usage (from Pippin repo root):
#   source tests/scc_abtest/setup_env.sh
#   bash tests/scc_abtest/run_abtest.sh
# ============================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")") && pwd)"
PIPPIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Pippin A/B scheduler test ==="
echo "Repo root : $PIPPIN_ROOT"
echo "Templates : $ABTEST_TEMPLATES"
echo ""

# ---------- unit tests (no cluster needed) ----------
echo "[1/3] Running scheduler unit tests..."
python -m pytest "$PIPPIN_ROOT/tests/test_scheduler.py" -v
echo ""

# ---------- Version A: Slurm ----------
echo "[2/3] Running Version A (Slurm) pipeline..."
python "$PIPPIN_ROOT/run.py" \
    --config "$PIPPIN_ROOT/tests/scc_abtest/cfg_A_slurm.yml" \
    "$PIPPIN_ROOT/tests/scc_abtest/pipeline_A_slurm.yml"
RC_A=$?
echo "Version A exit code: $RC_A"
echo ""

# ---------- Version B: SGE ----------
echo "[3/3] Running Version B (SGE) pipeline..."
python "$PIPPIN_ROOT/run.py" \
    --config "$PIPPIN_ROOT/tests/scc_abtest/cfg_B_sge.yml" \
    "$PIPPIN_ROOT/tests/scc_abtest/pipeline_B_sge.yml"
RC_B=$?
echo "Version B exit code: $RC_B"
echo ""

# ---------- summary ----------
echo "=========================================="
echo "A/B Test Summary"
echo "=========================================="
if [ $RC_A -eq 0 ]; then
    echo "  Version A (Slurm): PASS"
else
    echo "  Version A (Slurm): FAIL (exit $RC_A)"
fi
if [ $RC_B -eq 0 ]; then
    echo "  Version B (SGE)  : PASS"
else
    echo "  Version B (SGE)  : FAIL (exit $RC_B)"
fi
echo "=========================================="

if [ $RC_A -eq 0 ] && [ $RC_B -eq 0 ]; then
    echo "OVERALL: BOTH PASS"
    exit 0
else
    echo "OVERALL: ONE OR BOTH FAILED"
    exit 1
fi
