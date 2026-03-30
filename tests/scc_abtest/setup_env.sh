#!/bin/bash
# ============================================================
# setup_env.sh  — environment for BU SCC (pi-brout group)
# Usage:  source tests/scc_abtest/setup_env.sh
# ============================================================

# Templates directory inside this repo
export ABTEST_TEMPLATES="$(cd "$(dirname "${BASH_SOURCE[0]}")/templates" && pwd)"

# SNANA installation
export SNANA_DIR="/project/pi-brout/apps/SNANA"
export SNDATA_ROOT="/project/pi-brout/data"
export PATH="$SNANA_DIR/bin:$SNANA_DIR/util:$PATH"

# Simulation output directory
export SCRATCH_SIMDIR="/project/pi-brout/data/SIM"

# Pippin output
export PIPPIN_OUTPUT="/project/pi-brout/data/pippin_output"

# Existing SBATCH templates (for version A — Slurm control test)
export SBATCH_TEMPLATES="/project/pi-brout/templates"

mkdir -p "$PIPPIN_OUTPUT"

echo "Environment set:"
echo "  ABTEST_TEMPLATES = $ABTEST_TEMPLATES"
echo "  SNANA_DIR        = $SNANA_DIR"
echo "  SNDATA_ROOT      = $SNDATA_ROOT"
echo "  SCRATCH_SIMDIR   = $SCRATCH_SIMDIR"
echo "  PIPPIN_OUTPUT    = $PIPPIN_OUTPUT"
echo "  SBATCH_TEMPLATES = $SBATCH_TEMPLATES"
