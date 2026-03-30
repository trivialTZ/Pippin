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

# SNANA runtime libraries — must load before running snlc_sim.exe
module load cfitsio/4.4.1
module load gsl/2.5
export GSL_DIR=/share/pkg.8/gsl/2.5/install
export CFITSIO_DIR=/share/pkg.8/cfitsio/4.4.1/install
export LD_LIBRARY_PATH="$GSL_DIR/lib:$CFITSIO_DIR/lib:$LD_LIBRARY_PATH"

# Simulation output directory
export SCRATCH_SIMDIR="/project/pi-brout/data/SIM"

# Pippin output
export PIPPIN_OUTPUT="/project/pi-brout/data/pippin_output"

# Existing SBATCH templates (for version A — Slurm control test)
export SBATCH_TEMPLATES="/project/pi-brout/templates"

mkdir -p "$PIPPIN_OUTPUT"

# Activate Pippin venv
source /project/pi-brout/apps/Pippin/.venv/bin/activate

# Ensure PATH_SNDATA_SIM.LIST exists
mkdir -p "$SCRATCH_SIMDIR"
if [ ! -f "$SCRATCH_SIMDIR/PATH_SNDATA_SIM.LIST" ]; then
    echo "$SCRATCH_SIMDIR" > "$SCRATCH_SIMDIR/PATH_SNDATA_SIM.LIST"
    echo "  Created $SCRATCH_SIMDIR/PATH_SNDATA_SIM.LIST"
fi

echo "Environment set:"
echo "  ABTEST_TEMPLATES = $ABTEST_TEMPLATES"
echo "  SNANA_DIR        = $SNANA_DIR"
echo "  SNDATA_ROOT      = $SNDATA_ROOT"
echo "  SCRATCH_SIMDIR   = $SCRATCH_SIMDIR"
echo "  PIPPIN_OUTPUT    = $PIPPIN_OUTPUT"
echo "  SBATCH_TEMPLATES = $SBATCH_TEMPLATES"
