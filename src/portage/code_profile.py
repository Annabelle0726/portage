#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""
Portage's implementation of the `code` profile of the verifier contract.

The contract lives in the sibling `verifier-contract` repository (`SPEC.md`,
`schema/request.schema.json`, `schema/verdict.schema.json`,
`schema/context/code.context.schema.json`). This module is the deterministic
gate that used to be `failup.py::checks_pass`, moved behind that boundary: a
request document in, a verdict document out.

THE PREDICATE IS UNCHANGED. Non-empty change set, then lint, then tests, in that
order, short-circuiting at the first failure — the same three checks in the same
order with the same meanings, and the same three reason codes SPEC.md section
0.3 fixed from `checks_pass`'s return values:

    empty-diff   -> code.empty_diff
    lint-failed  -> code.lint_failed
    tests-failed -> code.tests_failed
    ok           -> the `pass` verdict, which is why `ok` has no code

The optional fourth check is `typecheck`, registered as `code.typecheck_failed`.
It runs between lint and tests and only when `context.commands.typecheck` is
present. The fail-up guard does not configure one, so in Portage today that code
is registered and never emitted — which is what the registry's append-only
policy is for (SPEC.md section 7.2): the code exists for Cairn's grading runner,
which will.

NOTHING HERE IS TIED TO EITHER CALLER (SPEC.md section 3.1). The context carries
a working directory and a command set. It does not know what a tier is, what
escalation is, or that a fail-up ladder exists. That is deliberate: this profile
serves Portage's guard and, after the rename in `CC-C4-cairn-rename.md`, Cairn's
grading runner at `github.com/EduCloud-Ecosystem/cairn`.

WHAT DOES NOT CROSS THE BOUNDARY.

  * AVAILABILITY. `failup.py::runner_availability_failure()` stays upstream of
    this call and is NOT reimplemented here (SPEC.md section 2.1). An empty
    change set arriving at this profile is already a capability question,
    because the caller has already filtered out the "the model was never really
    tried" case. This profile has no way to make that distinction and must not
    appear to: there is no `unavailable` verdict and no availability reason
    code.
  * ESCALATION. Whether a `fail` means "retry one tier up", "stop and flag a
    human", or "record a loss" is the caller's policy. The verdict says the
    candidate failed and which check failed; `failup.py` decides what that is
    worth.
  * COMMAND OUTPUT. Evidence carries each check's name, status and exit code,
    and never a line of what the command printed. Lint and test output quotes
    source lines, and source lines are candidate content — a verdict that
    echoed them would reproduce the candidate through the contract (SPEC.md
    section 6). The output goes to the caller's own log, not into the verdict.

`candidate` is the CHANGE SET AS TEXT — `git status --porcelain` output, or
whatever equivalent a non-git caller produces. It is a string because SPEC.md
section 3 says the thing being judged is always a produced artifact and keeping
it scalar is what makes the evidence non-reproduction rule mechanically
checkable. The caller computes it; this profile only asks whether it is empty
and, if not, whether the commands agree.

This file is also a conformant executable: `python3 code_profile.py` reads a
request document on stdin, writes a verdict document on stdout, and exits
non-zero if it cannot reach a verdict (SPEC.md section 1.1).
"""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any

PROFILE = "code"

EXIT_BAD_STDIN = 2
EXIT_JUDGE_FAILED = 3

# Matches the timeout `failup.py::run` has always used for gate commands.
TIMEOUT_SECONDS = 1800

# Check order IS the short-circuit order, the evidence order (SPEC.md section 8
# makes evidence order part of determinism) and the reason-code precedence
# (SPEC.md section 4.1). Only one check can fail per verdict, because a failing
# check stops the run — the same behaviour `checks_pass` had, and it is
# load-bearing: running the test suite after lint has already failed costs the
# guard real minutes on every escalation.
_CHECKS: tuple[tuple[str, str, str], ...] = (
    ("lint", "code.lint_failed", "the lint command exited non-zero"),
    ("typecheck", "code.typecheck_failed", "the typecheck command exited non-zero"),
    ("test", "code.tests_failed", "the test command exited non-zero"),
)

_EMPTY_DIFF_CODE = "code.empty_diff"
_EMPTY_DIFF_DETAIL = "the change set is empty; the agent changed nothing"

# Evidence status vocabulary. Fixed profile strings (SPEC.md section 6).
_PASSED = "passed"
_FAILED = "failed"
_NOT_RUN = "not_run"  # short-circuited by an earlier failure
_NOT_CONFIGURED = "not_configured"  # no command supplied for this check


class VerifierError(RuntimeError):
    """The judge could not decide. Becomes a non-zero exit, never a `fail`."""


def build_request(
    diff: str,
    working_dir: str,
    task: str = "",
    lint: list[str] | None = None,
    test: list[str] | None = None,
    typecheck: list[str] | None = None,
) -> dict[str, Any]:
    """Assemble a contract request document for the code profile.

    `diff` is the caller's change set as text; `working_dir` is where the
    commands run. Nothing else crosses.
    """
    commands: dict[str, list[str]] = {}
    if lint is not None:
        commands["lint"] = list(lint)
    if typecheck is not None:
        commands["typecheck"] = list(typecheck)
    if test is not None:
        commands["test"] = list(test)
    return {
        "profile": PROFILE,
        "task": task,
        "candidate": diff,
        "context": {"working_dir": working_dir, "commands": commands},
    }


def _run(argv: list[str], cwd: str) -> int:
    try:
        return subprocess.run(  # noqa: S603 — argv vector, never a shell string
            argv, cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT_SECONDS
        ).returncode
    except subprocess.TimeoutExpired as err:
        # A command that never returns is a JUDGE failure, not a candidate
        # failure: nothing was decided about the candidate (SPEC.md section 2.2).
        raise VerifierError(
            f"gate command timed out after {TIMEOUT_SECONDS}s: {argv}"
        ) from err
    except OSError as err:
        raise VerifierError(f"gate command could not be executed: {argv}: {err}") from err


def _verdict(
    outcome: str, reason_code: str | None, detail: str, evidence: list[dict[str, Any]]
) -> dict[str, Any]:
    doc: dict[str, Any] = {"verdict": outcome, "profile": PROFILE}
    if reason_code is not None:
        doc["reason_code"] = reason_code
    doc["detail"] = detail
    doc["evidence"] = evidence
    return doc


def verify(request: dict[str, Any]) -> dict[str, Any]:
    """Request document in, verdict document out. One candidate per call."""
    context = request.get("context")
    if not isinstance(context, dict):
        raise VerifierError("request.context is required and must be an object")
    working_dir = context.get("working_dir")
    if not isinstance(working_dir, str) or not working_dir:
        raise VerifierError(
            "context.working_dir is required and must be a non-empty string"
        )
    commands = context.get("commands")
    if not isinstance(commands, dict):
        raise VerifierError("context.commands is required and must be an object")
    candidate = request.get("candidate")
    if not isinstance(candidate, str):
        raise VerifierError("request.candidate is required and must be a string")

    changed_files = len([ln for ln in candidate.splitlines() if ln.strip()])

    # One evidence object per check EVALUATED — always four, in a fixed order, so
    # a pass documents its own coverage and a fail says which checks never ran
    # (SPEC.md section 4). Nothing candidate-derived except `changed_files`,
    # which is a count.
    diff_evidence = {
        "check": "diff",
        "status": _PASSED if changed_files else _FAILED,
        "changed_files": changed_files,
    }
    evidence: list[dict[str, Any]] = [diff_evidence]

    if not changed_files:
        evidence += [
            {
                "check": name,
                "status": _NOT_RUN if name in commands else _NOT_CONFIGURED,
                "exit_code": None,
            }
            for name, _c, _d in _CHECKS
        ]
        return _verdict("fail", _EMPTY_DIFF_CODE, _EMPTY_DIFF_DETAIL, evidence)

    failed: tuple[str, str] | None = None
    for name, code, detail in _CHECKS:
        argv = commands.get(name)
        # `not_configured` is checked BEFORE `not_run`, so a check's status
        # depends on the request rather than on where in the run the failure
        # landed: an unconfigured check reads the same whether or not something
        # earlier failed. Both are distinct from `passed` — a check nobody ran
        # is not a check that succeeded.
        if argv is None:
            evidence.append({"check": name, "status": _NOT_CONFIGURED, "exit_code": None})
            continue
        if failed is not None:
            evidence.append({"check": name, "status": _NOT_RUN, "exit_code": None})
            continue
        ok_argv = (
            isinstance(argv, list) and argv and all(isinstance(a, str) for a in argv)
        )
        if not ok_argv:
            raise VerifierError(
                f"context.commands.{name} must be a non-empty array of strings"
            )
        rc = _run(argv, working_dir)
        evidence.append(
            {"check": name, "status": _PASSED if rc == 0 else _FAILED, "exit_code": rc}
        )
        if rc != 0:
            failed = (code, detail)

    if failed is not None:
        return _verdict("fail", failed[0], failed[1], evidence)
    return _verdict(
        "pass",
        None,
        "change set is non-empty and every configured check passed",
        evidence,
    )


def main(argv: list[str] | None = None) -> int:
    """Executable form: stdin -> stdout, exit 0 iff a verdict was reached."""
    try:
        request = json.loads(sys.stdin.read())
    except (ValueError, OSError) as err:
        print(f"code: cannot read a request document on stdin: {err}", file=sys.stderr)
        return EXIT_BAD_STDIN
    try:
        verdict = verify(request)
    except Exception as err:  # noqa: BLE001 — any failure here is a JUDGE failure
        print(
            f"code: the verifier failed and reached no verdict: {err!r}", file=sys.stderr
        )
        return EXIT_JUDGE_FAILED
    json.dump(verdict, sys.stdout, sort_keys=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
