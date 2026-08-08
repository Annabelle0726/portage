# CC-P12 — Make escalation's re-prefill cost visible, after confirming it's real

*Claude Code prompt. Authored in Cowork, 2026-08-08, from
`docs/specs/13-routing-paradigm.md` §4.1 (source:
`routing-gateway-brokering-landscape-2026-08-08.md`, Cowork project).

The scan's finding, Morph's strongest technical point: a model switch is a
full re-prefill, forfeiting the ~5x cache-hit discount, and a
verify-then-escalate ladder switches models mid-task *by design* — so it
pays this cost on every escalation. The spec's ask: "`tier_pricing`'s cost
capture should treat an escalation as discarding the cached prefix, so the
recorded cost of a two-rung task reflects re-prefill rather than assuming
cache continuity."

**Read `tier_pricing.py` and `failup.py` closely before writing anything —
this may be a reporting gap, not a live bug.** `failup.py`'s `run_ladder()`
spawns a fresh `claude -p` subprocess per tier attempt
(`cmd = runner.split() + [attempt_task, "--model", model, ...]`); each tier
is a different model, and prompt caches don't carry across models or fresh
processes. `tier_pricing.price_for_rung()` already prices each attempt
independently from that attempt's own `tokens_in`/`cache_read_tokens` — it
doesn't currently assume cache continuity *across* tiers anywhere Cowork's
audit found. So Part 1 below is a verification step, not an assumed
prerequisite: don't build Part 2 on an assumed bug without checking first.*

---

## 1. Confirm or refute the premise, empirically

Run (or find in existing logs) at least one real `failup.py` run that
escalated across two tiers. Inspect `.claude/state/failup-log.jsonl` for that
run's attempts and check: is `cache_read_tokens` genuinely null/0 on the
attempt *after* an escalation, confirming there's no cross-tier cache
carryover to misprice? Or is there some path (same-tier retry within
`failure_classes.MAX_ATTEMPTS_PER_TIER`, which *does* reuse the same model)
where cache continuity is assumed and shouldn't be?

State the answer plainly in your report before touching code. If the
premise is refuted — no live pricing bug exists — say so and treat the rest
of this prompt as the reporting-gap work it's actually needed for, not a
correctness fix you're inventing a justification for.

## 2. Add a distinct escalation-cost figure to `measure.py`

Today `summarize()` in `measure.py` produces `cost_by_tier_usd`, additive per
tier — a two-rung task's true total cost is recoverable by summing, but
nothing states it as its own number, and the paired baseline (which exists
specifically to be honest about what the ladder costs) shouldn't require a
reader to do that arithmetic by hand.

Add an `escalation_cost_usd` figure (name it better if you find a clearer
one) alongside the existing per-tier breakdown: for every **admissible,
escalated** run (reuse the existing `escalated` / admissible-run logic
already in `summarize()` — do not build a second population filter that
could drift from it), sum the cost of every attempt *after* the first, and
report that as its own line, separate from floor-tier cost. This is the
number that answers "what did escalating actually cost us," which is
exactly what Morph's critique says today's accounting hides.

Print it in `_fmt()` alongside the existing cost lines, same formatting
convention as `cost_by_tier_usd`.

## 3. Tests

Add or extend `tests/test_measure.py` with a fixture run that escalates
(reuse whatever fixture-log pattern the file already has for
`cost_by_tier_usd` — don't invent a new log-shape). Assert the new figure is
present, correctly excludes floor-tier cost, and behaves like the rest of
this module's cost accounting on the `cost_unknown` / unpriced-row case
(never silently drop an unpriceable attempt — same "no silent exclusion"
rule the module's docstring already states for `inadmissible_runs`).

## 4. Report

- The Part 1 empirical finding, stated plainly, before anything else.
- What you added and why it's additive (existing consumers of `summarize()`
  should see this as a new key, not a changed one).
- `uv run ruff check .` and `uv run pytest -q` both green.
- If Part 1 found a real cache-continuity assumption worth fixing beyond
  visibility, say so explicitly and describe it — don't fix it silently
  inside a prompt scoped to reporting.
