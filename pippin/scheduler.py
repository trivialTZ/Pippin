"""Scheduler abstraction for Pippin.

Supports Slurm (sbatch/squeue) and SGE/OGS (qsub/qstat).
Slurm is the default.  Set ``SCHEDULER: type: sge`` in your global config
to switch to SGE.
"""

import subprocess
from abc import ABC, abstractmethod

from pippin.config import get_logger

logger = get_logger()


class Scheduler(ABC):
    """Abstract scheduler interface."""

    @abstractmethod
    def submit(self, script_path, cwd=None):
        """Submit *script_path* to the batch system.

        Parameters
        ----------
        script_path : str
            Absolute path to the job script.
        cwd : str, optional
            Working directory for the submission command.
        """

    @abstractmethod
    def get_jobs(self):
        """Return a list of currently-queued job name strings for $USER.

        Returns ``None`` if the query command fails, ``[]`` if no jobs are
        running.  The list shape is the same as what the rest of Pippin
        already expects from the ``squeue`` polling in ``manager.py``.
        """

    def count_jobs(self):
        """Return the number of jobs currently in the queue for $USER.

        Returns 0 on error so callers can keep running safely.
        """
        jobs = self.get_jobs()
        if jobs is None:
            return 0
        return len(jobs)


class SlurmScheduler(Scheduler):
    """Slurm backend — wraps sbatch / squeue."""

    def submit(self, script_path, cwd=None):
        subprocess.run(["sbatch", script_path], cwd=cwd)

    def get_jobs(self):
        """Return job names from ``squeue -h -u $USER -o '%%.j'``.

        Returns ``None`` on command failure.
        """
        p = subprocess.run(
            "squeue -h -u $USER -o '%.j'",
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if p.returncode != 0 or p.stderr:
            logger.error(
                f"squeue failed (rc={p.returncode}): {p.stderr.strip()}"
            )
            return None
        return [line.strip() for line in p.stdout.splitlines()]

    def count_jobs(self):
        """Fast count via ``squeue -ho %A -u $USER | wc -l``."""
        try:
            return int(
                subprocess.check_output(
                    "squeue -ho %A -u $USER | wc -l",
                    shell=True,
                    stderr=subprocess.STDOUT,
                )
            )
        except subprocess.CalledProcessError:
            return 0


class SGEScheduler(Scheduler):
    """SGE / OGS backend — wraps qsub / qstat.

    Tested against BU SCC (Open Grid Scheduler).  The ``qstat -u $USER``
    output format is::

        job-ID  prior   name       user   state  submit/start at     queue  ...
        ------- ------  ---------  -----  -----  ------------------  -----  ...
         123456  0.555  MYJOB      user   r      03/28/2026 10:00:00 all.q  ...

    Column index 2 (0-based after splitting on whitespace) is the job name.
    """

    def submit(self, script_path, cwd=None):
        subprocess.run(["qsub", script_path], cwd=cwd)

    def get_jobs(self):
        """Return job names from ``qstat -u $USER -r``.

        Uses ``-r`` flag to get full (untruncated) job names via the
        ``Full jobname:`` lines.  Plain ``qstat`` truncates names to 10 chars
        which breaks Pippin's prefix-based job matching.

        Returns ``None`` on command failure, ``[]`` when no jobs are queued.
        """
        p = subprocess.run(
            "qstat -u $USER -r",
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if p.returncode != 0 or p.stderr:
            logger.error(
                f"qstat failed (rc={p.returncode}): {p.stderr.strip()}"
            )
            return None

        names = []
        for line in p.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("Full jobname:"):
                name = stripped.split("Full jobname:", 1)[1].strip()
                if name:
                    names.append(name)
        return names


def get_scheduler(global_config):
    """Factory: return the right Scheduler based on *global_config*.

    Reads ``SCHEDULER.type`` (default ``"slurm"``).
    Falls back gracefully when the ``SCHEDULER`` key is absent so that
    existing configs that only have ``SBATCH:`` keep working.

    Parameters
    ----------
    global_config : dict
        Parsed global Pippin config (from ``pippin.config.get_config()``).

    Returns
    -------
    Scheduler
    """
    sched_cfg = global_config.get("SCHEDULER", {})
    sched_type = sched_cfg.get("type", "slurm").lower()

    if sched_type == "sge":
        logger.info("Scheduler: SGE (qsub/qstat)")
        return SGEScheduler()

    # Default — slurm
    if sched_type != "slurm":
        logger.warning(
            f"Unknown scheduler type '{sched_type}', defaulting to slurm."
        )
    logger.info("Scheduler: Slurm (sbatch/squeue)")
    return SlurmScheduler()
