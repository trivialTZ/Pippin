# BU SCC Support (SGE / Open Grid Scheduler)

Pippin supports two scheduler backends:

| Backend | Submit | Poll | Config `type` |
|---|---|---|---|
| Slurm (default) | `sbatch` | `squeue` | `slurm` |
| SGE / SCC | `qsub` | `qstat` | `sge` |

---

## How to configure SCC mode

### 1. Copy the example global config

```bash
cp configs/scc/cfg_scc.yml ~/my_scc.yml
```

Edit `~/my_scc.yml` to match your SCC project and paths.

### 2. Set environment variables

```bash
export QSUB_TEMPLATES=/path/to/your/qsub/templates   # dir containing QSUB_SCC.TEMPLATE etc.
export SCRATCH_SIMDIR=/projectnb/yourgroup/sim
export PIPPIN_OUTPUT=/projectnb/yourgroup/pippin_output
export PRODUCTS=/projectnb/yourgroup/products         # if using SuperNNova / CosmoMC
```

### 3. Create your qsub template files

Example `QSUB_SCC.TEMPLATE` (CPU jobs):

```bash
#!/bin/bash
#$ -N REPLACE_NAME
#$ -o REPLACE_LOGFILE
#$ -j y
#$ -l h_rt=REPLACE_WALLTIME
#$ -l mem_total=REPLACE_MEM
#$ -pe omp 1

echo "Job $JOB_ID starting on $(hostname) at $(date)"

REPLACE_JOB
```

The placeholders `REPLACE_NAME`, `REPLACE_LOGFILE`, `REPLACE_WALLTIME`, `REPLACE_MEM`,
and `REPLACE_JOB` are filled in by Pippin at runtime.

For GPU jobs, add:
```bash
#$ -l gpus=1
#$ -l gpu_c=6.0
```

### 4. Configure the SCHEDULER block in your global config

```yaml
SCHEDULER:
  type: sge                                        # <-- key line
  cpu_location: $QSUB_TEMPLATES/QSUB_SCC.TEMPLATE
  gpu_location: $QSUB_TEMPLATES/QSUB_SCC_gpu.TEMPLATE
```

### 5. Set BATCH_INFO in your pipeline YAML for SNANA tasks

SNANA handles its own job submission for `SIM` and `LCFIT` stages.
You must tell it to use `qsub`:

```yaml
SIM:
  MY_SIM:
    IA:
      BASE: surveys/sdss/sims_ia/sn_ia_g10_sdss_3yr.input
    GLOBAL:
      BATCH_INFO: qsub $QSUB_TEMPLATES/QSUB_SCC.TEMPLATE 10

LCFIT:
  MY_FIT:
    BASE: surveys/sdss/lcfit_nml/sn_fit_sdss.nml
    OPTS:
      BATCH_INFO: qsub $QSUB_TEMPLATES/QSUB_SCC.TEMPLATE 10
```

### 6. Run Pippin

```bash
pippin -c ~/my_scc.yml my_pipeline.yml
```

---

## Running a local (non-DES) smoke test

A minimal smoke-test config using SDSS survey files (already in this repo) is
provided at `configs/scc/smoke_test_sim.yml`.  It does **not** require
`DES_ROOT` or any DES-specific ancillary files.

```bash
# On SCC:
pippin -c configs/scc/cfg_scc.yml configs/scc/smoke_test_sim.yml
```

Expected output directory: `$PIPPIN_OUTPUT/SMOKE_TEST_SCC/`

For a pure local unit-level check (no cluster needed):

```bash
pytest tests/test_scheduler.py -v
```

---

## Manual verification checklist (must run on real SCC)

These steps **cannot** be automated locally and must be confirmed on BU SCC:

- [ ] `qstat -u $USER` column layout matches expected: col 2 (0-based) is the job name
- [ ] `qsub job.sh` exits 0 and the job appears in `qstat` output
- [ ] The job name Pippin sets appears untruncated in `qstat` col 2
      (SGE truncates names >10 chars by default; adjust `REPLACE_NAME` length if needed)
- [ ] DataPrep task submits and finishes on SCC
- [ ] SIM task with `BATCH_INFO: qsub ...` runs end-to-end
- [ ] GPU job header syntax is correct for SCC
      (confirm `#$ -l gpus=1` vs `#$ -l gpu=1` with SCC documentation)
- [ ] Project / queue flags needed (e.g. `#$ -P myproject`) are added to your template
- [ ] `PIPPIN_OUTPUT` and `SCRATCH_SIMDIR` are on a writable shared filesystem

---

## Scheduler internals (for developers)

The scheduler abstraction lives in `pippin/scheduler.py`.

```
Scheduler          (abstract)
├── SlurmScheduler  submit=sbatch, poll=squeue
└── SGEScheduler    submit=qsub,   poll=qstat
```

The active scheduler is selected in `Manager.__init__` via `get_scheduler(global_config)`
and passed to each task via `task.set_scheduler()`.  Tasks that Pippin submits
directly (`DataPrep`, `SuperNNova` classifier) call `self.scheduler.submit()`.
Tasks submitted by SNANA itself (`SIM`, `LCFIT`) only need the poll side;
those are handled transparently by the manager loop.
