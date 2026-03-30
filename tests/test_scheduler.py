"""Unit tests for pippin.scheduler.

All tests use mocked subprocess calls — no real cluster access is needed.
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from pippin.scheduler import (
    SGEScheduler,
    SlurmScheduler,
    get_scheduler,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_proc(stdout="", stderr="", returncode=0):
    p = MagicMock()
    p.stdout = stdout
    p.stderr = stderr
    p.returncode = returncode
    return p


# ---------------------------------------------------------------------------
# SlurmScheduler
# ---------------------------------------------------------------------------

class TestSlurmScheduler:
    def test_submit_calls_sbatch(self):
        sched = SlurmScheduler()
        with patch("pippin.scheduler.subprocess.run") as mock_run:
            sched.submit("/tmp/job.slurm", cwd="/tmp")
        mock_run.assert_called_once_with(["sbatch", "/tmp/job.slurm"], cwd="/tmp")

    def test_get_jobs_parses_output(self):
        sched = SlurmScheduler()
        fake_output = "PIP_SIM_JOB\nPIP_FIT_JOB\n"
        with patch("pippin.scheduler.subprocess.run", return_value=_make_proc(stdout=fake_output)):
            jobs = sched.get_jobs()
        assert jobs == ["PIP_SIM_JOB", "PIP_FIT_JOB"]

    def test_get_jobs_returns_none_on_error(self):
        sched = SlurmScheduler()
        with patch("pippin.scheduler.subprocess.run",
                   return_value=_make_proc(returncode=1, stderr="error")):
            jobs = sched.get_jobs()
        assert jobs is None

    def test_get_jobs_empty_queue(self):
        sched = SlurmScheduler()
        with patch("pippin.scheduler.subprocess.run", return_value=_make_proc(stdout="")):
            jobs = sched.get_jobs()
        assert jobs == []

    def test_count_jobs_uses_wc(self):
        sched = SlurmScheduler()
        with patch("pippin.scheduler.subprocess.check_output", return_value=b"7\n"):
            n = sched.count_jobs()
        assert n == 7

    def test_count_jobs_returns_zero_on_error(self):
        sched = SlurmScheduler()
        with patch("pippin.scheduler.subprocess.check_output",
                   side_effect=subprocess.CalledProcessError(1, "squeue")):
            n = sched.count_jobs()
        assert n == 0


# ---------------------------------------------------------------------------
# SGEScheduler
# ---------------------------------------------------------------------------

class TestSGEScheduler:
    # Realistic qstat output from BU SCC (two header lines + job rows)
    QSTAT_OUTPUT = (
        "job-ID  prior   name       user         state submit/start at     queue\n"
        "------- ------- ---------- ------------ ----- ------------------- -----\n"
        " 123456  0.5550 PIP_SIM    myuser       r     03/28/2026 10:00:00 all.q\n"
        " 123457  0.5550 PIP_FIT    myuser       qw    03/28/2026 10:01:00 all.q\n"
    )

    def test_submit_calls_qsub(self):
        sched = SGEScheduler()
        with patch("pippin.scheduler.subprocess.run") as mock_run:
            sched.submit("/tmp/job.sh", cwd="/tmp")
        mock_run.assert_called_once_with(["qsub", "/tmp/job.sh"], cwd="/tmp")

    def test_get_jobs_parses_normal_output(self):
        sched = SGEScheduler()
        with patch("pippin.scheduler.subprocess.run",
                   return_value=_make_proc(stdout=self.QSTAT_OUTPUT)):
            jobs = sched.get_jobs()
        assert jobs == ["PIP_SIM", "PIP_FIT"]

    def test_get_jobs_empty_queue(self):
        """qstat with no jobs prints only headers (or nothing)."""
        sched = SGEScheduler()
        # No jobs: qstat prints nothing (exit 0)
        with patch("pippin.scheduler.subprocess.run",
                   return_value=_make_proc(stdout="")):
            jobs = sched.get_jobs()
        assert jobs == []

    def test_get_jobs_only_headers(self):
        """qstat may print two header lines even with no jobs on some systems."""
        sched = SGEScheduler()
        headers_only = (
            "job-ID  prior   name       user   state  submit/start at  queue\n"
            "------- ------- ---------- ------ -----  ---------------- -----\n"
        )
        with patch("pippin.scheduler.subprocess.run",
                   return_value=_make_proc(stdout=headers_only)):
            jobs = sched.get_jobs()
        assert jobs == []

    def test_get_jobs_returns_none_on_command_error(self):
        sched = SGEScheduler()
        with patch("pippin.scheduler.subprocess.run",
                   return_value=_make_proc(returncode=1, stderr="qstat: command not found")):
            jobs = sched.get_jobs()
        assert jobs is None

    def test_count_jobs_matches_get_jobs_length(self):
        sched = SGEScheduler()
        with patch("pippin.scheduler.subprocess.run",
                   return_value=_make_proc(stdout=self.QSTAT_OUTPUT)):
            n = sched.count_jobs()
        assert n == 2

    def test_count_jobs_zero_when_get_jobs_fails(self):
        sched = SGEScheduler()
        with patch("pippin.scheduler.subprocess.run",
                   return_value=_make_proc(returncode=1, stderr="error")):
            n = sched.count_jobs()
        assert n == 0


# ---------------------------------------------------------------------------
# get_scheduler factory
# ---------------------------------------------------------------------------

class TestGetScheduler:
    def test_returns_slurm_for_slurm_type(self):
        cfg = {"SCHEDULER": {"type": "slurm",
                              "cpu_location": "/tmp/cpu.tmpl",
                              "gpu_location": "/tmp/gpu.tmpl"}}
        sched = get_scheduler(cfg)
        assert isinstance(sched, SlurmScheduler)

    def test_returns_sge_for_sge_type(self):
        cfg = {"SCHEDULER": {"type": "sge",
                              "cpu_location": "/tmp/cpu.tmpl",
                              "gpu_location": "/tmp/gpu.tmpl"}}
        sched = get_scheduler(cfg)
        assert isinstance(sched, SGEScheduler)

    def test_defaults_to_slurm_when_scheduler_key_absent(self):
        """Backward compat: configs with only SBATCH: block should still work."""
        cfg = {"SBATCH": {"cpu_location": "/tmp/cpu.tmpl",
                           "gpu_location": "/tmp/gpu.tmpl"}}
        sched = get_scheduler(cfg)
        assert isinstance(sched, SlurmScheduler)

    def test_defaults_to_slurm_for_unknown_type(self):
        cfg = {"SCHEDULER": {"type": "condor"}}
        sched = get_scheduler(cfg)
        assert isinstance(sched, SlurmScheduler)

    def test_type_is_case_insensitive(self):
        cfg = {"SCHEDULER": {"type": "SGE"}}
        sched = get_scheduler(cfg)
        assert isinstance(sched, SGEScheduler)
