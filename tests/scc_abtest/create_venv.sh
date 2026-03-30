#!/bin/bash
# ============================================================
# create_venv.sh — one-time setup of Pippin venv on BU SCC
# Usage:  bash tests/scc_abtest/create_venv.sh
# Run once per installation; afterwards use setup_env.sh
# ============================================================

set -e

PIPPIN_DIR=/project/pi-brout/apps/Pippin
VENV_DIR=$PIPPIN_DIR/.venv

echo "Creating venv at $VENV_DIR ..."
python3 -m venv "$VENV_DIR"

echo "Activating venv ..."
source "$VENV_DIR/bin/activate"

echo "Upgrading pip ..."
pip install --upgrade pip

echo "Installing Pippin dependencies from requirements.txt ..."
pip install -r "$PIPPIN_DIR/requirements.txt"

echo "Installing Pippin package in editable mode ..."
pip install -e "$PIPPIN_DIR"

echo ""
echo "Done. Venv is ready at $VENV_DIR"
echo "To activate: source $VENV_DIR/bin/activate"
echo "Or just run: source tests/scc_abtest/setup_env.sh"
