# Pippin Scheduler A/B Test — BU SCC

This folder contains everything needed to compare Slurm vs SGE scheduler
behavior on BU SCC. No DES files or DES-specific environment variables required.

---

## Folder contents

```
tests/scc_abtest/
  README.md                   this file
  setup_env.sh                set environment variables (edit first)
  run_abtest.sh               run both versions end-to-end
  cfg_A_slurm.yml             global config: Slurm backend (control)
  cfg_B_sge.yml               global config: SGE backend  (treatment)
  pipeline_A_slurm.yml        pipeline: small SDSS sim via sbatch
  pipeline_B_sge.yml          pipeline: identical SDSS sim via qsub
  templates/
    SBATCH_SCC_cpu.TEMPLATE   Slurm job header template
    QSUB_SCC_cpu.TEMPLATE     SGE CPU job header template
    QSUB_SCC_gpu.TEMPLATE     SGE GPU job header template
```

---

## One-time setup

### 1. Edit `setup_env.sh`

Open `setup_env.sh` and replace the placeholder values:

```bash
export SCRATCH_SIMDIR="/projectnb/YOURGROUP/sim"
export PIPPIN_OUTPUT="/projectnb/YOURGROUP/pippin_output"
export SNANA_DIR="/path/to/snana"   # wherever SNANA is installed on SCC
```

### 2. Edit the job templates if needed

`templates/QSUB_SCC_cpu.TEMPLATE` — add your project/queue flags, e.g.:
```bash
#$ -P yourproject
```

`templates/SBATCH_SCC_cpu.TEMPLATE` — add your partition/account, e.g.:
```bash
#SBATCH --partition=shared
#SBATCH --account=yourproject
```

### 3. Install Pippin (if not already)

```bash
cd /path/to/pippin
pip install -e .
```

---

## Running the A/B test

From the Pippin repo root:

```bash
# Step 1: load environment
source tests/scc_abtest/setup_env.sh

# Step 2: run all tests (unit + both pipelines)
bash tests/scc_abtest/run_abtest.sh
```

Or run each part separately:

```bash
# Unit tests only (no cluster needed, runs locally)
python -m pytest tests/test_scheduler.py -v

# Version A: Slurm
python run.py -c tests/scc_abtest/cfg_A_slurm.yml tests/scc_abtest/pipeline_A_slurm.yml

# Version B: SGE
python run.py -c tests/scc_abtest/cfg_B_sge.yml tests/scc_abtest/pipeline_B_sge.yml
```

---

## Expected output

### Unit tests
```
tests/test_scheduler.py  18 passed
```

### Version A (Slurm)
Pippin polls `squeue`, submits via `sbatch`, prints:
```
No failed tasks
```
Output in `$PIPPIN_OUTPUT/abtest_A_slurm/`

### Version B (SGE)
Pippin polls `qstat`, submits via `qsub`, prints:
```
No failed tasks
```
Output in `$PIPPIN_OUTPUT/abtest_B_sge/`

---

## What to check if something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `qstat: command not found` | Module not loaded | `module load sge` or equivalent |
| `qstat` parses 0 jobs but jobs are running | Column layout differs | Check col index in `pippin/scheduler.py` `SGEScheduler.get_jobs()` |
| Job name mismatch (0 matches) | SGE truncates names >10 chars | Shorten `prefix` in `cfg_B_sge.yml` (e.g. `prefix: B`) |
| `sbatch: command not found` on SCC | Slurm not available | Expected — only use version B (SGE) on SCC |
| `SNANA_DIR` KeyError | Env var not set | Check `setup_env.sh` was sourced |
| `SCRATCH_SIMDIR` variable unresolved | Env var not set | Check `setup_env.sh` was sourced |

---

## Manual verification checklist

After running both pipelines, confirm:

- [ ] `qstat -u $USER` col 2 is the job name (not truncated)
- [ ] Version A exit code 0, output dir populated
- [ ] Version B exit code 0, output dir populated
- [ ] Both output dirs contain a `SDSS_SIM_*/` folder with simulation products
- [ ] No `FAILED` tasks in either Pippin log
