"""Shared fixtures for testing the scripts/ tools without network or model calls.

scripts/failup.py and scripts/plan.py are single-file `uv run --script`
utilities, not a package, so they're loaded by path rather than imported
normally.
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def failup():
    return _load("failup_under_test", SCRIPTS / "failup.py")


@pytest.fixture
def plan_mod():
    return _load("plan_under_test", SCRIPTS / "plan.py")


@pytest.fixture
def git_repo(tmp_path):
    """A throwaway git repo with a tracked marker.txt at HEAD, so `git reset
    --hard` (failup.py's recovery step) has something meaningful to revert to
    between escalation attempts.

    Mirrors this repo's own `.gitignore` in one specific way: `.claude/state/`
    is ignored. That's load-bearing, not cosmetic — failup.py's own log lives
    under `.claude/state/`, and `git stash push -u` (used to park a failed
    attempt) sweeps up and removes any untracked-and-NOT-ignored file. Without
    the ignore, the guard would delete its own just-written log entry on every
    escalation. A fixture without this entry reproduces that exact failure.
    """
    repo = tmp_path / "proj"
    repo.mkdir()

    def run(*a):
        return subprocess.run(a, cwd=repo, check=True, capture_output=True)

    run("git", "init", "-q")
    run("git", "config", "user.email", "test@example.com")
    run("git", "config", "user.name", "Test")
    (repo / ".gitignore").write_text(".claude/state/\n")
    (repo / "marker.txt").write_text("INIT")
    run("git", "add", ".")
    run("git", "commit", "-q", "-m", "init")
    return repo


NOOP_LINT = [sys.executable, "-c", "import sys; sys.exit(0)"]
CHECK_MARKER = [sys.executable, str(FIXTURES / "check_marker.py")]
STUB_RUNNER = f"{sys.executable} {FIXTURES / 'stub_runner.py'}"
