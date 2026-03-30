#!/bin/bash
# ============================================================
# setup_env.sh  — set required environment variables before
# running either A/B test pipeline on BU SCC.
#
# Edit the values below to match your SCC account/paths,
# then:  source tests/scc_abtest/setup_env.sh
# ============================================================

# Path to the abtest templates directory (this folder)
export ABTEST_TEMPLATES="$(cd "$(dirname "${BASH_SOURCE[0]}")/templates" && pwd)"

# Directory where SNANA writes simulation output
# Example: /projectnb/yourgroup/sim
export SCRATCH_SIMDIR="/projectnb/YOURGROUP/sim"

# Pippin output root
# Results land in $PIPPIN_OUTPUT/abtest_A_slurm/ and $PIPPIN_OUTPUT/abtest_B_sge/
export PIPPIN_OUTPUT="/projectnb/YOURGROUP/pippin_output"

# SNANA installation (needed by SNANA internally)
export SNANA_DIR="/usr/local/snana"  # adjust to your SCC install

# Optional: location of extra Pippin products (classifiers etc.)
# export PRODUCTS="/projectnb/YOURGROUP/products"

echo "Environment set:"
echo "  ABTEST_TEMPLATES = $ABTEST_TEMPLATES"
echo "  SCRATCH_SIMDIR   = $SCRATCH_SIMDIR"
echo "  PIPPIN_OUTPUT    = $PIPPIN_OUTPUT"
echo "  SNANA_DIR        = $SNANA_DIR"
