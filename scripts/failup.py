#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Fail-up guard (Lane B) — the thing that makes escalation flawless.

Runs an automated coding task at an assigned tier, then verifies it
DETERMINISTICALLY (the agent changed something + it's coherent + tests pass).
On failure it parks the attempt, resets clean, and retries ONE TIER UP, to the
ceiling. No model call in the guard itself, so a misrouted hard task can't die
on a too-cheap model — it fails the check and self-corrects to Opus.

This is why you don't need a sophisticated classifier: cheap heuristics can be
wrong, because the guard catches the misses.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

# The escalation ladder is FILE-DRIVEN (bottom -> top) so the local and EduCloud
# versions differ by config, not code. Default file: .claude/tiers.json.
# Example (local):    ["local,qwen2.5-coder:7b", "local,qwen2.5-coder:32b",
#                      "anthropic,claude-sonnet-5", "anthropic,claude-opus-4-8"]
# Example (EduCloud): ["local,qwen2.5-coder:7b", "jetstream2,gpt-oss-120b",
#                      "anthropic,claude-sonnet-5", "anthropic,claude-opus-4-8"]
DEFAULT_TIERS_FILE = ".claude/tiers.json"

# A tier entry is either a bare "provider,model" string (effort defaults) or an
# object {"model": "...", "effort": "default|high|xhigh"}. The Claude-5x pilot
# uses the object form so escalation raises MODEL and EFFORT together, discovering
# the cheapest (model, effort) that clears the deterministic check.


def load_tiers(project: str, tiers_file: str) -> list[dict]:
    path = Path(tiers_file)
    if not path.is_absolute():
        path = Path(project) / tiers_file
    raw = (json.loads(path.read_text(encoding="utf-8")) if path.is_file()
           else ["anthropic,claude-sonnet-5", "anthropic,claude-opus-4-8"])
    tiers = []
    for e in raw:
        if isinstance(e, str):
            tiers.append({"model": e, "effort": None})
        else:
            tiers.append({"model": e["model"], "effort": e.get("effort")})
    return tiers


def run(cmd, cwd=None, timeout=1800):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def git(project, *args):
    return run(["git", "-C", project, *args])


def checks_pass(project: str):
    """Deterministic gate: non-empty diff -> coherent -> tests green."""
    if not git(project, "status", "--porcelain").stdout.strip():
        return False, "empty-diff"                     # agent did nothing
    if run(["uv", "run", "ruff", "check", "."], cwd=project).returncode != 0:
        return False, "lint-failed"                    # proxy for "patch applies"
    if run(["uv", "run", "pytest", "-q"], cwd=project).returncode != 0:
        return False, "tests-failed"                   # correctness
    return True, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, help="prompt for the automated run")
    ap.add_argument("--start-tier", type=int, default=0)
    ap.add_argument("--project", default=os.getcwd())
    ap.add_argument("--tiers", default=DEFAULT_TIERS_FILE,
                    help="JSON file: ordered list of model strings or {model,effort}")
    ap.add_argument("--runner", default="claude -p",
                    help="agent invocation. Claude-5x pilot: 'claude -p' (native, "
                         "draws the separate credit). Multi-provider: 'ccr code -p'.")
    ap.add_argument("--max-tier", type=int, default=None,
                    help="budget-pressure ceiling: never escalate above this tier "
                         "index. If the capped tier fails, STOP and flag a human "
                         "rather than spend scarce Opus quota.")
    args = ap.parse_args()
    project = args.project
    TIERS = load_tiers(project, args.tiers)
    ceiling = len(TIERS) - 1 if args.max_tier is None else min(args.max_tier, len(TIERS) - 1)

    run_id = uuid.uuid4().hex[:8]        # groups this task's escalation attempts
    log = Path(project) / ".claude" / "state" / "failup-log.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)

    if git(project, "status", "--porcelain").stdout.strip():
        print("[failup] warning: working tree is dirty at start; commit or stash first",
              file=sys.stderr)
    base = git(project, "rev-parse", "HEAD").stdout.strip()

    for tier in range(args.start_tier, ceiling + 1):
        model = TIERS[tier]["model"]
        effort = TIERS[tier]["effort"]
        t0 = time.time()
        # NOTE: match `--model` / `--effort` to your CLI version's flags (native
        # `claude -p` and `ccr code -p` differ; Haiku rejects the top effort level
        # and must use 'high'). Effort is omitted when the tier sets none.
        cmd = args.runner.split() + [args.task, "--model", model]
        if effort:
            cmd += ["--effort", effort]
        run(cmd, cwd=project)
        ok, reason = checks_pass(project)

        with log.open("a") as f:
            f.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(), "run_id": run_id,
                "task": args.task,          # needed for distillation (specs/09)
                "tier": tier, "model": model, "effort": effort,
                "ok": ok, "reason": reason,
                "seconds": round(time.time() - t0, 1),
            }) + "\n")

        if ok:
            print(f"[failup] clean pass at tier {tier} ({model}, effort={effort})")
            sys.exit(0)

        print(f"[failup] tier {tier} ({model}) failed: {reason}", file=sys.stderr)
        if tier < ceiling:
            # park the failed attempt (recoverable), reset clean, escalate
            git(project, "stash", "push", "-u", "-m", f"failup-t{tier}-{reason}")
            git(project, "reset", "--hard", base)
        # at the ceiling, leave the attempt in the tree for a human to inspect

    capped = args.max_tier is not None and ceiling < len(TIERS) - 1
    msg = ("budget ceiling reached (quota-capped below the top tier); STOPPED for a "
           "human — did not spend scarce Opus quota" if capped
           else "top tier reached without a clean pass; attempt left in tree for review")
    print(f"[failup] {msg}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
