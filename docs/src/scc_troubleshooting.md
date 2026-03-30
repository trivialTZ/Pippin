# BU SCC Troubleshooting Guide

This guide covers common issues when running Pippin on BU SCC (Open Grid Scheduler / SGE).

---

## Quick diagnosis checklist

Run these first to confirm your environment is ready:

```bash
cd /project/pi-brout/apps/Pippin
source tests/scc_abtest/setup_env.sh

# 1. Scheduler available?
which qsub && qstat -u $USER

# 2. SNANA executable works?
snlc_sim.exe 2>&1 | head -1

# 3. submit_batch_jobs.sh in PATH?
which submit_batch_jobs.sh

# 4. Pippin scheduler loads correctly?
python -c "from pippin.scheduler import get_scheduler; print(type(get_scheduler({'SCHEDULER':{'type':'sge'}})))"

# 5. Unit tests pass?
python -m pytest tests/test_scheduler.py -v
```

---

## Issue: `snlc_sim.exe: error while loading shared libraries: libcfitsio.so.10`

**Cause:** SNANA runtime libraries not in `LD_LIBRARY_PATH`.

**Fix:**
```bash
module load cfitsio/4.4.1
module load gsl/2.5
export LD_LIBRARY_PATH="/share/pkg.8/gsl/2.5/install/lib:/share/pkg.8/cfitsio/4.4.1/install/lib:$LD_LIBRARY_PATH"
```

Add these to `tests/scc_abtest/setup_env.sh` (already done if you cloned the latest repo).

**If `libgsl.so.28` is missing** (SNANA compiled against newer GSL):
```bash
cd /project/pi-brout/apps/SNANA/src
export GSL_DIR=/share/pkg.8/gsl/2.5/install
export CFITSIO_DIR=/share/pkg.8/cfitsio/4.4.1/install
make ../bin/snlc_sim.exe
```

---

## Issue: `Unable to run job: attribute "mem_total" is not a memory value`

**Cause:** The qsub template uses a memory attribute or value format not accepted by this SCC queue.

**Diagnosis:** Check which memory attributes are valid:
```bash
qconf -sc | grep -i mem
```

**Common fixes:**
- Change `4GB` → `4G` in the template
- Change `mem_total` → `h_vmem` or `mem_free` depending on what `qconf -sc` shows
- Remove the memory line entirely to use queue defaults

Test a minimal job first:
```bash
cat > /tmp/test_mem.sh << 'EOF'
#!/bin/bash
#$ -N test_mem
#$ -j y
#$ -o /tmp/test_mem.log
#$ -l h_rt=0:01:00
#$ -pe omp 1
echo "works"
EOF
qsub /tmp/test_mem.sh
qstat -u $USER
```

Once you find the working memory syntax, update `tests/scc_abtest/templates/QSUB_SCC_cpu.TEMPLATE`.

---

## Issue: `Unable to find NGENTOT_RATECALC` (SNANA normalization fails)

**Cause:** `snlc_sim.exe` ran but crashed silently during the normalization step.

**Diagnosis:**
```bash
cat /project/pi-brout/data/pippin_output/.../LOGS/SIMnorm_*.LOG
```

Common sub-causes:

| Error in norm log | Fix |
|---|---|
| `libcfitsio.so.10: not found` | Load cfitsio module (see above) |
| `OPT_MWEBV = -3 < 0 is no longer allowed` | Change to `OPT_MWEBV: 3` in sim input file |
| `2 'EXPOSURE_TIME:' keys exceeds limit=1` | Remove duplicate key from sim input file |
| `SIMLIB_FILE` path not found | Replace hardcoded path with `$SNDATA_ROOT/simlib/...` |

---

## Issue: `No more waiting, there are no scheduler jobs active that match ...`

**Cause:** Pippin polls `qstat` for job names but jobs finish before the threshold is reached.

**This is usually harmless** if the simulation actually completed. Check:
```bash
ls /project/pi-brout/data/pippin_output/.../LOGS/ALL.DONE
cat /project/pi-brout/data/pippin_output/.../LOGS/MERGE.LOG | tail -10
```

If `ALL.DONE` exists with `SUCCESS`, the run succeeded. Pippin will detect it on the next poll.

If jobs are finishing too fast and Pippin fails before detecting `ALL.DONE`, the fix is to increase `num_empty_threshold` in `pippin/task.py` (default 10) for your workflow.

---

## Issue: CPU job log files not appearing / jobs submitted but not running

**Cause:** qsub silently rejected the job due to invalid resource request.

**Diagnosis:** Submit the batch script manually:
```bash
cd /path/to/LOGS/
qsub CPU0000_JOBLIST_scc4.BATCH
```

If you see `Unable to run job: attribute X is not a memory value`, fix the memory attribute in the template (see memory issue above).

**Log file location:** SGE writes the log (`-o` option) relative to the directory where `qsub` is called, not the job's `cd` directory. If `-o` is a relative path, look in the submission directory.

---

## Issue: `BATCH_ENV_SETUP` causes normalization to fail

**Cause:** `BATCH_ENV_SETUP` in the pipeline YAML gets passed as a command-line argument to the normalization `snlc_sim.exe` run, which doesn't understand it.

**Fix:** Do NOT use `BATCH_ENV_SETUP` in the Pippin pipeline YAML for environment setup. Instead, put `module load` commands directly in the qsub template file (`QSUB_SCC_cpu.TEMPLATE`). SNANA copies the template header into every generated batch script.

---

## Issue: `ModuleNotFoundError: No module named 'coloredlogs'`

**Cause:** The venv lost packages after module reloads.

**Fix:**
```bash
source /project/pi-brout/apps/Pippin/.venv/bin/activate
pip install coloredlogs -q
```

---

## Issue: Scheduler shows `Slurm` even when SGE config is specified

**Cause:** Using `-c` flag instead of `--config`. In Pippin, `-c` means `--check` (validate config), not `--config`.

**Fix:**
```bash
# WRONG:
python run.py -c tests/scc_abtest/cfg_B_sge.yml pipeline.yml

# CORRECT:
python run.py --config tests/scc_abtest/cfg_B_sge.yml pipeline.yml
```

---

## Issue: `SETUP.location` task files not found

**Cause:** `SETUP.location` is a relative path but `DATA_DIRS` doesn't include the repo root.

**Fix:** Add the repo root to `DATA_DIRS` in your global config:
```yaml
DATA_DIRS:
  - data_files
  - /project/pi-brout/apps/Pippin
```

Then set:
```yaml
SETUP:
  location: pippin/tasks
```

---

## Issue: `qstat` job name truncated — Pippin cannot track jobs

**Cause:** SGE truncates job names to 10 characters in plain `qstat` output.

**Fix:** Already handled in `pippin/scheduler.py` — Pippin uses `qstat -u $USER -r` and parses `Full jobname:` lines. No user action needed.

---

## Verifying the full environment before a real run

```bash
source tests/scc_abtest/setup_env.sh

# Check all required tools
echo "qsub: $(which qsub)"
echo "qstat: $(which qstat)"
echo "snlc_sim.exe: $(which snlc_sim.exe)"
echo "submit_batch_jobs.sh: $(which submit_batch_jobs.sh)"
echo "SNDATA_ROOT: $SNDATA_ROOT"
echo "SNANA_DIR: $SNANA_DIR"
snlc_sim.exe 2>&1 | head -1   # should print 'Full command:'

# Test minimal qsub
cat > /tmp/pippin_test.sh << 'EOF'
#!/bin/bash
#$ -N pippin_test
#$ -j y
#$ -o /tmp/pippin_test.log
#$ -l h_rt=0:01:00
#$ -pe omp 1
module load cfitsio/4.4.1 gsl/2.5
snlc_sim.exe 2>&1 | head -1
EOF
qsub /tmp/pippin_test.sh
sleep 10
cat /tmp/pippin_test.log 2>/dev/null || echo 'log not written yet'
```
