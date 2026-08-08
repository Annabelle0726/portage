# CC-P13 — Classification-informed entry rung, verification unchanged

*Claude Code prompt. Authored in Cowork, 2026-08-08, from
`docs/specs/13-routing-paradigm.md` §4.2 (source:
`routing-gateway-brokering-landscape-2026-08-08.md`, Cowork project). This is
the largest of the three items the landscape scan produced (see also CC-P11,
CC-P12) — do those first if they aren't already landed; this one is more
invasive and easiest to get subtly wrong.

The idea, in the spec's own words: "classification decides *where to
start*; verification still decides *whether it worked*." The useful half of
classification-first routing (Morph's Router and most of the OSS field),
without its bet. The T1 classifier tier (Gemma 4 E4B) already exists and
already does rough triage elsewhere in this platform. Let it choose
`run_ladder()`'s entry rung instead of always starting at tier 0, so a task
predictably beyond the local tier doesn't have to fail there first to learn
that.

**The hard constraint, stated in the spec and repeated here because it is
the entire point of this prompt: this must not silently become
classification-first.** If entry-rung selection ever correlates with
reduced verification — fewer escalations, fewer same-tier retries, anything
that looks like the classifier's guess is being trusted instead of
checked — that is a regression, not an optimization. `failup.py`'s own
docstring already states the platform's thesis: "no model call in the guard
itself, so a misrouted hard task can't die on a too-cheap model — it fails
the check and self-corrects." Classification must slot in without touching
that sentence's truth.*

---

## 1. Read first

- `docs/specs/13-routing-paradigm.md` §4.2, and §1 for why verify-then-
  escalate is the platform's stated thesis (cites eth-sri/cascade-routing,
  ICML 2025 — the formal backing for why the guard must stay authoritative)
- `src/portage/failup.py` in full — `run_ladder()`'s `start_tier` parameter
  already exists (used today only by `plan.py`'s decomposition driver, and by
  tests) — this task is about what *chooses* that argument, not about adding
  a new mechanism to the ladder itself
- Wherever the T1 classifier (Gemma 4 E4B) currently does triage — find its
  existing call site before writing a second one; if none exists as a
  reusable function, that's a real gap worth naming in your report, not
  silently duplicating

## 2. Write the constraint test before the feature

This is the part of the prompt to not skip or shortcut. Before writing any
classifier-selection code, write a test that asserts: **whether a task
enters the ladder at tier 0 or at a classifier-chosen tier, a task that
fails verification at its entry tier escalates exactly as it would have from
tier 0** — same retry-then-escalate behavior
(`failure_classes.MAX_ATTEMPTS_PER_TIER`), same logging, same eventual
outcome if the true answer requires a higher tier than the classifier
guessed. Use `run_ladder()`'s existing `start_tier` parameter and a stub
runner (same fixture idiom `tests/test_failup.py` and `tests/conftest.py`
already use) to simulate "classifier picked tier 2, but only tier 3 actually
passes" and confirm the run still reaches tier 3, verified, not stalled.

Confirm this test would **fail** under a naive implementation that lets
classification skip verification (e.g., trusts tier 2's output without
running the gate) — if you can't make it fail under a plausible wrong
implementation, the test isn't testing the constraint yet.

## 3. Build the classifier-informed entry selection

Add a function (new module, or a home in an existing one if you find the
T1 classifier's existing call site makes that obviously right) that takes
the task text and returns a `start_tier` index into the loaded tiers list —
same shape `run_ladder()` already accepts. Wire it as the *default* for
`start_tier` when the caller doesn't explicitly pass one (preserve the
explicit-override path `plan.py` uses today unchanged).

Failure mode discipline: if the classifier is unreachable or its output
doesn't parse, fall back to `start_tier=0` (the floor) — the same
"unavailable, not evidence about capability" posture `failup.py` already
applies to model calls in `runner_availability_failure()`. A classifier
outage must degrade to "start at the bottom," never to "skip verification,"
never to a crash.

## 4. Tests

- The constraint test from §2, now passing.
- Classifier-selection unit tests: correct tier chosen for an obvious case,
  floor fallback on classifier failure/malformed output, no change to
  `plan.py`'s existing explicit `start_tier` behavior.
- Confirm `tests/test_failup.py`'s existing tests are unaffected — this
  should be purely additive to `run_ladder()`'s calling convention.

## 5. Report

- Paste the §2 constraint test's failing output against a naive
  implementation, and its passing output against the real one — this is the
  evidence the hard constraint actually held, not just an assertion that it
  did.
- Where the T1 classifier call lives now, and whether you reused an existing
  call site or had to add the first reusable one (flag it if the latter —
  that's worth knowing, not just doing).
- `uv run ruff check .` and `uv run pytest -q` both green.
- Any case where entry-tier selection and verification outcome correlated in
  your test data in a way that's worth a second look before this ships.
