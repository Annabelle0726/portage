# CC-P14 — Self-hosted Langfuse for measure.py's telemetry

*Claude Code prompt. Authored in Cowork, 2026-08-08, from an LLM-
observability provider scan (`morph-full-and-provider-landscape-2026-08-08.md`,
Cowork project). Of everything surveyed (Langfuse, Arize Phoenix, Helicone,
Traceloop, Braintrust, LangSmith, W&B Weave, PromptLayer), only **Langfuse**
(MIT-licensed core, Docker/Helm self-hostable, OTel-native ingestion, Postgres
+ ClickHouse backend) and **Arize Phoenix** (Apache-2.0, also self-hostable)
are genuinely self-hostable at the tier this platform needs — everything
else is SaaS-first with self-hosting gated behind an enterprise tier that
isn't really open. Langfuse is the one worth standing up: it's zero
sovereignty cost (self-hosted, no data leaves the deployment) and purely
additive to what `measure.py` already does.

**This is additive telemetry, not a replacement for `measure.py`'s own
metric logic.** `measure.py`'s `summarize()` — Ceiling-Normalized Accuracy,
per-tier recall, the five-class failure taxonomy, three-price cost
accounting — stays exactly as it is. This prompt adds a parallel export path
so those same events are ALSO queryable with trace-level replay, an
eval-dataset store, and prompt-version diffing, none of which `measure.py`'s
own JSONL parsing gives you today.*

---

## 1. Read first

- `src/portage/measure.py` — especially `summarize()`'s event shape
  (`failup-log.jsonl`'s per-attempt records) and the module's own note on
  what it can and can't see (the docstring block above `summarize()`)
- `src/portage/failup.py` — where these events are actually written
  (`run_ladder()`'s per-attempt logging block)
- `config/deploy/compose.example.yaml` — the existing deployment shape this
  needs to extend, not fork

## 2. Instrument with OpenLLMetry, not a Langfuse-specific SDK

Use the OpenTelemetry-native **OpenLLMetry** SDK (vendor-neutral
instrumentation) rather than Langfuse's own client library directly — this
keeps the instrumentation swappable (Phoenix or any other OTel sink could
consume the same traces later) rather than coupling `failup.py`/`plan.py` to
one vendor's SDK. Emit a span per tier-attempt in `run_ladder()`, carrying
the same fields the JSONL log already writes (tier, model, effort, ok,
reason, reason_code, category, cost/token usage) — additive, not a
replacement for the existing `.claude/state/failup-log.jsonl` write, which
stays as the source of truth `measure.py` reads from.

## 3. Add self-hosted Langfuse to the deploy config

Extend `config/deploy/compose.example.yaml` (or add a sibling compose file
if mixing observability infra into the example deploy is the wrong call —
state your reasoning) with a Langfuse service (Docker, per Langfuse's own
self-hosting docs — Postgres + ClickHouse backing store) receiving the OTel
export. This is infrastructure config, matching the platform's existing
"config diff, not code" posture wherever possible — keep actual code
changes limited to the instrumentation call sites in §2.

## 4. Confirm nothing about measure.py's own metrics changes

Run `measure.py report` before and after this change against the same
fixture logs used in `tests/test_measure.py` and confirm byte-identical
output. This prompt must not touch `summarize()`'s logic — if you find
yourself wanting to change it to "feed off Langfuse instead of JSONL,"
that's out of scope; the JSONL log remains the metrics source of truth,
Langfuse is a parallel, optional enrichment layer for a human to explore
traces in.

## 5. Tests

- Instrumentation emits a span with the expected fields for a fixture
  ladder run (mock/no-op exporter in tests — never require a live Langfuse
  instance for the test suite to pass).
- `measure.py`'s existing tests (`tests/test_measure.py`) unchanged and
  green — this is the proof the metrics path wasn't touched.
- If OpenLLMetry or its dependencies aren't already in `pyproject.toml`,
  add them there, matching this repo's existing dependency-declaration
  convention.

## 6. Report

- Confirm `measure.py report`'s output is byte-identical before/after.
- Whether the compose addition lives in the existing example file or a new
  sibling file, and why.
- Any place OpenLLMetry's instrumentation API required a workaround for
  this codebase's `uv run --script` single-file module pattern (`failup.py`
  is not a package member — same idiom note its own docstring already
  carries for `code_profile()`/`failure_classes()`) — flag it rather than
  silently restructuring the module to fit the instrumentation library.
- `uv run ruff check .` and `uv run pytest -q` both green.
