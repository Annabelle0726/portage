"""HB-2: per-class failure priors and per-tier recall in measure.py::summarize().

No test_measure.py existed before HB-2 — these cover only the new fields;
they don't re-test win_tier_distribution/floor_pass_rate/etc., which have no
dedicated tests either but are exercised indirectly by every prior consumer
of failup-log.jsonl. Writing log entries by hand (not through failup.py)
keeps this file independent of the guard's own tests.
"""
import json


def _write_log(project, entries):
    d = project / ".claude" / "state"
    d.mkdir(parents=True, exist_ok=True)
    with (d / "failup-log.jsonl").open("w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


def _attempt(run_id, tier, model, ok, reason, category, attempt_in_tier=0):
    return {
        "ts": "2026-08-06T00:00:00+00:00", "run_id": run_id, "task": "t",
        "tier": tier, "model": model, "effort": None,
        "attempt_in_tier": attempt_in_tier, "ok": ok, "reason": reason,
        "reason_code": None, "category": category, "seconds": 0.1,
    }


def test_per_class_failures_counts_failed_attempts_by_class(measure, tmp_path):
    project = tmp_path
    _write_log(project, [
        _attempt("r1", 0, "m0", False, "lint-failed", "capability"),
        _attempt("r1", 0, "m0", False, "lint-failed", "capability", attempt_in_tier=1),
        _attempt("r1", 1, "m1", True, "ok", "ok"),
        _attempt("r2", 0, "m0", False, "tests-failed", "capability"),
        _attempt("r2", 1, "m1", True, "ok", "ok"),
    ])

    s = measure.summarize(str(project), None, None)

    assert s["per_class_failures"] == {"lint-failed": 2, "tests-failed": 1}


def test_per_class_failures_excludes_availability(measure, tmp_path):
    project = tmp_path
    _write_log(project, [
        _attempt("r1", 0, "m0", False, "unavailable:503", "availability"),
        _attempt("r1", 0, "m0", True, "ok", "ok"),
    ])

    s = measure.summarize(str(project), None, None)

    # The tier-0 attempt that never reached the verifier contributes no class.
    assert s["per_class_failures"] == {}


def test_per_tier_recall_is_pass_share_of_attempts_that_reached_the_tier(
        measure, tmp_path):
    project = tmp_path
    _write_log(project, [
        _attempt("r1", 0, "m0", False, "lint-failed", "capability"),
        _attempt("r1", 1, "m1", True, "ok", "ok"),
        _attempt("r2", 0, "m0", True, "ok", "ok"),
        _attempt("r3", 0, "m0", False, "lint-failed", "capability"),
        _attempt("r3", 1, "m1", True, "ok", "ok"),
    ])

    s = measure.summarize(str(project), None, None)

    # tier 0: 3 attempts reached it (r1, r2, r3), 1 passed (r2) -> 33.3%
    # tier 1: 2 attempts reached it (r1, r3), 2 passed -> 100%
    assert s["per_tier_recall"] == {0: 33.3, 1: 100.0}
