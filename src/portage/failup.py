#!/usr/bin/env -S uv run --script
# SPDX-License-Identifier: AGPL-3.0-only
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

The deterministic gate itself is no longer inline: it is the `code` profile of
the verifier contract (`code_profile.py` here, `SPEC.md` in the sibling
verifier-contract repository), reached through `code_verdict()`. The escalation
logic below is unchanged and now reads a verdict document instead of a
`(bool, reason)` pair.
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

# The escalation ladder is FILE-DRIVEN (bottom -> top) so the local and EduCloud
# versions differ by config, not code. Default file: .claude/tiers.json.
# A tiers file is either a bare JSON array, or {"_comment": "...", "tiers": [...]}
# — the object form exists purely so a tiers file can document, in JSON, which
# runner/env it expects (native vs LiteLLM-gatewayed; see .claude/tiers.*.json).
# Example (local):    ["local-small", "local-big", "sonnet", "opus"]  (LiteLLM rungs)
# Example (Claude-5x pilot, native): ["sonnet", {"model": "opus", "effort": "high"}]
DEFAULT_TIERS_FILE = ".claude/tiers.json"

# A tier entry is either a bare model string (effort defaults) or an object
# {"model": "...", "effort": null|"low"|"medium"|"high"|"xhigh"|"max"}. Note that
# "default" is NOT a valid effort — use null to omit the flag. The Claude-5x pilot
# uses the object form so escalation raises MODEL and EFFORT together, discovering
# the cheapest (model, effort) that clears the deterministic check.


def load_tiers(project: str, tiers_file: str) -> list[dict]:
    path = Path(tiers_file)
    if not path.is_absolute():
        path = Path(project) / tiers_file
    raw = (json.loads(path.read_text(encoding="utf-8")) if path.is_file()
           else ["sonnet", "opus"])
    if isinstance(raw, dict):
        raw = raw["tiers"]
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


# Substrings that mark a runner failure as UNAVAILABILITY (network/rate-limit/
# gateway trouble) rather than the tier lacking the capability to do the task.
# Checked case-insensitively against the runner's own stdout+stderr, BEFORE the
# deterministic gate runs — an unreachable model also produces an empty diff,
# and misfiling that as "empty-diff" (a capability verdict) would poison
# measure.py's win-tier distribution and the steward's training signal
# (PLATFORM.md §9) with attempts that were never really tried.
#
# ── ONE DISTINCTION, TWO SITES, ON PURPOSE ──────────────────────────────────
# This is the "the SUBJECT was unreachable" half of the distinction the verifier
# contract's SPEC.md §2 names. The other half — "the JUDGE was unreachable" — is
# a non-zero exit from the verifier itself and lives at `code_verdict()` below;
# the two are cross-referenced so a later reader sees one distinction
# deliberately implemented in two places rather than two mechanisms that
# drifted. THIS check stays HERE, upstream of the verifier call, and must never
# move into the contract: the request document carries no endpoint, credential
# or model handle (SPEC.md §5), so a verifier cannot tell "the model could not
# do the task" from "the model was rate-limited" — only this function, which
# holds the runner's own transcript, can. SPEC.md §2.1 quotes the comment above
# verbatim as the rationale, so keep the two in sync if you ever edit it.
AVAILABILITY_MARKERS = (
    "429", "503", "502", "connection refused", "connect refused",
    "rate limit", "overloaded", "econnrefused", "connection reset",
    "service unavailable", "apiconnectionerror", "temporarily unavailable",
)


def runner_availability_failure(proc: subprocess.CompletedProcess) -> str | None:
    """None if the runner looked reachable; else an "unavailable:<marker>" reason."""
    blob = f"{proc.stdout}\n{proc.stderr}".lower()
    for marker in AVAILABILITY_MARKERS:
        if marker in blob:
            return f"unavailable:{marker}"
    return None


DEFAULT_GATE_CMDS = (
    ["uv", "run", "ruff", "check", "."],
    ["uv", "run", "pytest", "-q"],
)

# The guard's log, measure.py and distill.py have read these exact strings since
# before the contract existed, and `.claude/state/failup-log.jsonl` is
# longitudinal — records months old carry them. The contract's registry-governed
# `reason_code` is the label source those consumers should move to (see the
# verifier-contract repo's docs/P1-report.md §6). The log now carries BOTH: the
# raw `reason_code` alongside this translation, so the move can happen a consumer
# at a time without a migration and without any historical record changing
# meaning. This table stays until the last consumer of `reason` is gone.
_LEGACY_REASON = {
    "code.empty_diff": "empty-diff",
    "code.lint_failed": "lint-failed",
    "code.typecheck_failed": "typecheck-failed",
    "code.tests_failed": "tests-failed",
}

_CODE_PROFILE = None


def code_profile():
    """The sibling `code` profile module, loaded by path.

    failup.py is a single-file `uv run --script` utility rather than a package
    member — tests load it by path too (tests/conftest.py) — so a plain
    `import code_profile` would resolve only when sys.path happens to contain
    src/portage. Loading by path works in both modes and adds no dependency:
    code_profile.py is stdlib-only, like everything else in this repo's core.
    """
    global _CODE_PROFILE
    if _CODE_PROFILE is None:
        path = Path(__file__).resolve().parent / "code_profile.py"
        spec = importlib.util.spec_from_file_location("portage_code_profile", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _CODE_PROFILE = module
    return _CODE_PROFILE


def code_verdict(project: str, gate_cmds=None) -> dict:
    """The deterministic gate, THROUGH THE VERIFIER CONTRACT BOUNDARY.

    Was `checks_pass()`, which returned `(bool, reason)`. The predicate is
    unchanged — non-empty change set, then lint, then tests, short-circuiting at
    the first failure — but it now lives in `code_profile.py` behind a request
    document in / verdict document out interface (`SPEC.md` in the sibling
    verifier-contract repo). What moved is the boundary, not the decision.

    `gate_cmds`, an optional (lint_cmd, test_cmd) pair, lets tests substitute
    trivial fixture commands for the project's own ruff+pytest so the guard's
    ESCALATION LOGIC is unit-testable with zero network and zero model calls
    (HANDOFF Phase 2 acceptance). Production callers never pass it.

    ── ONE DISTINCTION, TWO SITES, ON PURPOSE ──────────────────────────────
    This is the "the JUDGE was unreachable" half of the distinction SPEC.md §2
    names: if the verifier itself breaks it raises (as an executable it would
    exit non-zero), and that is NOT a `fail` verdict — collapsing the two would
    turn every crashed verifier into a universal failure signal and silently
    escalate every task to the most expensive tier. The other half — "the
    SUBJECT was unreachable" — is `runner_availability_failure()` above, which
    runs BEFORE this call and stays out of the contract for the reason stated
    there. Read the two comments together.
    """
    profile = code_profile()
    lint_cmd, test_cmd = gate_cmds or DEFAULT_GATE_CMDS
    # The caller computes the change set; the profile only judges it. That is why
    # `git` stays here and not in the profile — the contract must not know that
    # this caller happens to use git.
    diff = git(project, "status", "--porcelain").stdout
    request = profile.build_request(
        diff=diff, working_dir=project, lint=lint_cmd, test=test_cmd
    )
    return profile.verify(request)


def run_ladder(task: str, project: str, tiers_file: str, runner: str,
               max_tier: int | None = None, start_tier: int = 0,
               gate_cmds=None) -> int:
    """The escalation loop. Returns the process exit code (0 clean pass, 1
    otherwise) rather than calling sys.exit directly, so tests can call this
    and inspect the result without spawning a subprocess."""
    TIERS = load_tiers(project, tiers_file)
    top = len(TIERS) - 1
    ceiling = top if max_tier is None else min(max_tier, top)

    run_id = uuid.uuid4().hex[:8]        # groups this task's escalation attempts
    log = Path(project) / ".claude" / "state" / "failup-log.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    # INVARIANT: `.claude/state/` must stay in the project's .gitignore. On
    # failure this loop runs `git stash push -u`, which sweeps up (and removes
    # from the tree) every untracked file that ISN'T ignored. Without the
    # ignore entry, the guard would delete its own just-written log on every
    # escalation. Verified by tests/conftest.py's `git_repo` fixture, which
    # reproduces the failure when the ignore entry is missing.

    if git(project, "status", "--porcelain").stdout.strip():
        print("[failup] warning: working tree is dirty at start; commit or stash first",
              file=sys.stderr)
    base = git(project, "rev-parse", "HEAD").stdout.strip()

    for tier in range(start_tier, ceiling + 1):
        model = TIERS[tier]["model"]
        effort = TIERS[tier]["effort"]
        t0 = time.time()
        # VERIFIED against Claude Code 2.1.207 (see docs/phase-1-findings.md):
        #   --model  takes a bare name/alias ('sonnet', 'claude-sonnet-5') or any
        #            string the configured gateway resolves (e.g. a LiteLLM model
        #            group). The "provider,model" comma form is CCR Router syntax
        #            and is REJECTED here — it must not appear in a tiers file.
        #   --effort takes exactly low|medium|high|xhigh|max. An unknown value is
        #            NOT an error: the CLI warns and silently uses default effort,
        #            so a typo would quietly flatten the ladder. Tiers that want
        #            default effort must set effort to null, which omits the flag.
        cmd = runner.split() + [task, "--model", model]
        if effort:
            cmd += ["--effort", effort]
        try:
            proc = run(cmd, cwd=project)
            avail_reason = runner_availability_failure(proc)
        except subprocess.TimeoutExpired:
            avail_reason = "unavailable:timeout"

        if avail_reason:
            # The SUBJECT was unreachable — never reaches the verifier at all,
            # so there is no verdict document and therefore no reason_code. The
            # contract has no availability namespace ON PURPOSE (SPEC.md §2.1),
            # so `reason_code: null` here is the correct record, not a gap: it
            # says "no verifier judged this", which is exactly the fact
            # `category` also carries.
            ok, reason, reason_code, category = (
                False, avail_reason, None, "availability")
        else:
            # By the time we get here the availability case is already filtered
            # out, so an empty change set IS a capability verdict (SPEC.md §2.1).
            verdict = code_verdict(project, gate_cmds)
            ok = verdict["verdict"] == "pass"
            # A `pass` carries no reason code (schema/verdict.schema.json
            # requires one only on `fail`), so this is None on success too.
            reason_code = verdict.get("reason_code")
            reason = "ok" if ok else _LEGACY_REASON[verdict["reason_code"]]
            category = "ok" if ok else "capability"

        with log.open("a") as f:
            f.write(json.dumps({
                "ts": datetime.now(UTC).isoformat(), "run_id": run_id,
                "task": task,                # needed for distillation (docs/specs/09)
                "tier": tier, "model": model, "effort": effort,
                # BOTH, not one. `reason` is the legacy string this log has
                # carried since before the contract existed and is what keeps
                # month-old records meaning what they said. `reason_code` is the
                # registry-governed code, verbatim from the verdict document,
                # and is what a new consumer should branch on: the registry is
                # append-only (SPEC.md §7.2), whereas a free-text reason can be
                # reworded invisibly to someone reading last month's logs.
                "ok": ok, "reason": reason, "reason_code": reason_code,
                "category": category,
                "seconds": round(time.time() - t0, 1),
            }) + "\n")

        if ok:
            print(f"[failup] clean pass at tier {tier} ({model}, effort={effort})")
            return 0

        print(f"[failup] tier {tier} ({model}) failed ({category}): {reason}",
              file=sys.stderr)
        if tier < ceiling:
            # park the failed attempt (recoverable), reset clean, escalate
            git(project, "stash", "push", "-u", "-m", f"failup-t{tier}-{reason}")
            git(project, "reset", "--hard", base)
        # at the ceiling, leave the attempt in the tree for a human to inspect

    capped = max_tier is not None and ceiling < len(TIERS) - 1
    msg = ("budget ceiling reached (quota-capped below the top tier); STOPPED for a "
           "human — did not spend scarce Opus quota" if capped
           else "top tier reached without a clean pass; attempt left in tree for review")
    print(f"[failup] {msg}", file=sys.stderr)
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, help="prompt for the automated run")
    ap.add_argument("--start-tier", type=int, default=0)
    ap.add_argument("--project", default=os.getcwd())
    ap.add_argument("--tiers", default=DEFAULT_TIERS_FILE,
                    help="JSON file: ordered list of model strings or {model,effort}")
    ap.add_argument("--runner", default="claude -p",
                    help="agent invocation. Native `claude -p` draws the Max wallet "
                         "directly (Claude-5x pilot) or, with ANTHROPIC_BASE_URL/ "
                         "ANTHROPIC_AUTH_TOKEN pointed at LiteLLM, routes through the "
                         "proxy instead — same binary either way (see "
                         "docs/phase-1-findings.md). No shim is needed for either path.")
    ap.add_argument("--max-tier", type=int, default=None,
                    help="budget-pressure ceiling: never escalate above this tier "
                         "index. If the capped tier fails, STOP and flag a human "
                         "rather than spend scarce Opus quota.")
    args = ap.parse_args()
    sys.exit(run_ladder(args.task, args.project, args.tiers, args.runner,
                        max_tier=args.max_tier, start_tier=args.start_tier))


if __name__ == "__main__":
    main()
