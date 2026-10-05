"""The scaffold's own contract, tested.

This repository has no analysis in it yet. What it does have is a set of promises - data
stays out of git, the data policy says how to obtain the data, and the test suite can
actually run in CI - and those are checkable now.

The CI promise is here because it has already failed once. In `cgm-forecast-conformal` the
workflow died with `pytest: command not found`, and underneath that sat a second fault: bare
`pytest` could not import `src`, because pytest puts the test file's own directory on
sys.path rather than the repository root. `python -m pytest` hides it locally, since Python
adds the working directory itself. Both faults came from the shared scaffold, so both are
asserted here rather than left to be rediscovered when this repository gets content.
"""
from __future__ import annotations

import configparser
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return out.stdout.split()


# --- the CI contract, which has failed before ------------------------------------

def test_pytest_is_a_declared_dependency():
    """CI installs from requirements.txt and then runs pytest; it has to be in there."""
    reqs = (ROOT / "requirements.txt").read_text().lower()
    assert "pytest" in reqs, "requirements.txt does not declare pytest, so CI cannot run the suite"


def test_pythonpath_is_configured_so_bare_pytest_can_import_src():
    cfg = tomllib.loads((ROOT / "pyproject.toml").read_text())
    paths = cfg.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("pythonpath")
    assert paths and "." in paths, (
        "pyproject.toml must put the repository root on pythonpath, or bare `pytest` "
        "cannot import src and CI fails while `python -m pytest` passes locally")


def test_a_ci_workflow_exists_and_runs_the_suite():
    wf = ROOT / ".github" / "workflows" / "tests.yml"
    assert wf.exists(), "no CI workflow"
    assert "pytest" in wf.read_text()


# --- the data contract -----------------------------------------------------------

def test_no_data_is_tracked():
    tracked = _tracked()
    offenders = [f for f in tracked
                 if (f.startswith("data/") and f != "data/README.md")
                 or f.endswith((".npz", ".pkl", ".h5", ".parquet", ".csv.gz"))]
    assert not offenders, f"data files are tracked: {offenders}"


def test_data_directory_is_ignored():
    probe = ROOT / "data" / "_ignore_probe.csv"
    probe.parent.mkdir(exist_ok=True)
    probe.write_text("x\n")
    try:
        out = subprocess.run(["git", "check-ignore", "-v", str(probe)],
                             cwd=ROOT, capture_output=True, text=True)
        assert out.returncode == 0, "data/ is not gitignored"
    finally:
        probe.unlink(missing_ok=True)


def test_data_readme_states_how_to_obtain_the_data():
    text = (ROOT / "data" / "README.md").read_text().lower()
    assert "data/" in text and "gitignore" in text
    # the target paper is not chosen yet, so the file must say so rather than imply a source
    assert "not yet selected" in text or "licence" in text or "license" in text


def test_pre_commit_hooks_are_configured():
    cfg = (ROOT / ".pre-commit-config.yaml").read_text()
    for hook in ("gitleaks", "detect-private-key", "check-added-large-files"):
        assert hook in cfg, f"{hook} is not configured"
