# HANDOFF — build instructions for Claude Code

**Read `PLATFORM.md` first** — it is the capstone definition (final open-model
platform + the comparison suite against Claude/Codex/Perplexity) and supersedes
this file where they conflict. Its §9 appends Phases 7–10 to the plan below.

This repo contains drafts, specs, and decisions from a long design process. Your
job is to turn it into a small, working, maintainable system — **building as
little as possible**. The design principle that governs everything: prefer
configuring an existing tool over writing code, and keep custom code to the thin
layer that is genuinely novel.

Read `PROJECT.md` (mission + novelty claim) and `specs/00`–`06` for rationale.
This file is the execution plan and overrides drafts where they conflict.

---

## 1. What this is

A quota- and sovereignty-aware routing layer for coding agents, piloted
personally (Claude Max 5x + ChatGPT Plus/Codex + Perplexity Pro + local
open-weight) and generalized to institutional compute (EduCloud / NSF ACCESS /
Jetstream2). Core ideas, in one line each:

- **Meters, not models:** the scarce resource is subscription quota and
  institutional allocation, not per-token dollars.
- **Free before metered, scarce last;** sensitive data pinned to local by
  deterministic rule.
- **Deterministic fail-up guard:** a runner decides pass/fail (diff + lint +
  tests), never the model's self-report; failures escalate one tier up.
- **Triage before routing:** a free local classifier catches underspecified
  tasks before they waste a frontier turn, then picks provider + model + effort.
- **Measured, not asserted:** baseline-vs-treatment evidence that quota went
  down while ceiling-stalls stayed flat.

## 2. Buy-over-build resolution (FINAL — do not rebuild these)

| Drafted in repo | Verdict | Replace with |
|---|---|---|
| `scripts/sovereign_broker.py` | **DELETE — fully covered** | **LiteLLM proxy.** One `config.yaml` gives cooldowns (429 → immediate cooldown), ordered failover (`order=1,2,3` = free→allocation→paid), background health checks, retries/backoff, Ollama + Anthropic + OpenAI-compatible endpoints, spend logging. Express free-before-metered as deployment `order`; the sovereign pool is just multiple deployments of the same `model_name`. |
| `.claude-code-router/*` configs | **Keep CCR only if needed as the Anthropic-format shim.** | Investigate first (Phase 1): LiteLLM exposes an Anthropic-compatible `/v1/messages` path; if Claude Code runs against LiteLLM directly, drop CCR and its configs entirely — fewest hops wins. If not, keep CCR as a thin client shim pointed at LiteLLM. |
| `scripts/scheduler.py` | **SHRINK.** | cron/launchd + a 20-line queue drain. Keep only enqueue/drain; delete the reset-estimate math (it was mostly moot for Lane B — see specs/04). |
| `scripts/plan.py` decomposition | **KEEP, thin.** | The per-subtask *runnable acceptance check* + human plan gate is the novel bit. Do NOT adopt Spec Kit/BMAD wholesale — they're heavier and lack the runnable-check enforcement. |
| `scripts/failup.py` | **KEEP.** | This is the contribution's core mechanism. Harden per §4. |
| `scripts/measure.py` | **KEEP, but read LiteLLM's spend logs** for token/cost columns instead of duplicating; our custom metrics (win-tier distribution, ceiling-stall rate, /usage snapshots) stay. |
| `herdr-meters/` plugin | **KEEP.** | Novel; no existing Herdr plugin does cross-vendor meter routing. Publishes via the `herdr-plugin` GitHub topic. |
| `herdr-meters/classify.py` | **KEEP.** | Free local triage+routing; deterministic pins first. |
| Lane A hooks (`.claude/hooks/*`) | **KEEP as-is.** | Already thin uses of native PreCompact/SessionStart. |
| `.claude/agents/*`, skills, CLAUDE.md | **KEEP as-is.** | Native Claude Code features, already minimal. |
| `scripts/ai` dispatcher | **DEPRECATE** in favor of the herdr-meters plugin (same function, better surface). Keep only if the user asks for a non-Herdr path. |
| Local serving (`local-serve.sh`) | **KEEP;** consider MLX later for throughput on Apple Silicon; not required. |

Also reuse, don't rebuild: STREAM's `hpc-as-api`/`streamrelay` for exposing HPC
jobs as OpenAI-compatible endpoints (they become LiteLLM deployments); native
Claude Code auto Opus→Sonnet downshift, effort levels, Task Budgets.

## 3. Target architecture (post-consolidation)

```
Lane A (interactive, Max wallet)          Lane B (automation, separate credit/API)
────────────────────────────────          ─────────────────────────────────────────
native claude + hooks + skills            claude -p  (Claude-only tasks)
herdr panes: claude | codex | local       failup.py --runner ... ──▶ tiers.json
herdr-meters plugin:                                     │
  classify (local 7B) → triage/route      LiteLLM proxy :4000  ◀── plan.py stages
  dispatch / board / mark                   deployments:
                                              local (ollama, order=1, free)
                                              jetstream2 / campus HPC (order=2)
                                              anthropic api / openrouter (order=3)
                                            cooldowns, health, spend logs
measure.py reads: failup-log, decomp-log, LiteLLM spend, /usage snapshots
```

Sensitive workspaces: a LiteLLM config variant whose `model_list` contains ONLY
local deployments (the pin is enforced by absence, same as before).

## 4. Phases, in order, each with acceptance criteria

### Phase 0 — repo hygiene (small)
- Restructure into a clean layout (`src/` or keep `scripts/`, your call), add
  `pyproject.toml` (uv-native), ruff config, delete the superseded files per §2.
- Pin versions: Claude Code CLI, LiteLLM, Herdr min version, model IDs — one
  `KNOWN_GOOD_VERSIONS.md` with rationale.
- **Accept:** `uv run ruff check .` clean; repo contains no dead drafts.

### Phase 1 — LiteLLM spine
- Write `litellm.config.yaml` (+ `litellm.sensitive.yaml`) expressing the tier
  pool: local (order 1, free) → sovereign endpoints (order 2) → paid API
  (order 3), with cooldowns and background health checks enabled.
- Investigate: can Claude Code / `claude -p` and Codex CLI (`config.toml`
  custom provider) point at LiteLLM directly? Prefer direct; fall back to CCR
  shim only if format translation is actually required. Document the finding.
- **Accept:** one curl to LiteLLM round-trips through Ollama; killing Ollama
  mid-test fails over to the next deployment; sensitive config refuses
  non-local models.

### Phase 2 — guard + decomposer hardening
- `failup.py`: verify `--model`/`--effort` flags against the REAL installed CLI
  versions (this was never verified — treat all CLI invocations as unverified
  until you run them); unit-test the ladder logic, budget ceiling, stash/reset
  recovery with a stub runner (a fake script that succeeds/fails on command) —
  zero tokens.
- `plan.py`: unit-test extract/validate/toposort/MANUAL-stop with fixtures;
  same stub-runner approach.
- **Accept:** `uv run pytest` green with NO network and NO model calls;
  a stubbed hard task demonstrably escalates local→sonnet→opus and a stubbed
  budget cap stops below opus with the correct message.

### Phase 3 — herdr-meters plugin
- Verify against the installed Herdr version: `pane list` output shape,
  `pane run` semantics, plugin env vars. Fix `find_pane` matching accordingly.
- Wire `dispatch` to prefer LiteLLM-routable targets where applicable; keep the
  scarce-confirmation and sensitive-pin behavior exactly as drafted.
- Test `classify.py` against the real local model on ~15 real tasks from the
  user's history; tune keyword rules only where the model misses.
- **Accept:** `herdr plugin link` + `board`/`picker`/`dispatch`/`mark` work in
  a live Herdr session; sensitive phrasing never reaches a non-local target
  (add a test asserting the deterministic layer fires before any subprocess).

### Phase 4 — measurement
- Point `measure.py` at LiteLLM's spend/log store for token+cost columns; keep
  run_id grouping, win-tier distribution, ceiling-stall rate, and the honest
  verdict line. Add `decomp-log` ingestion.
- Write the pilot protocol doc: baseline week (no routing) vs treatment week,
  daily `/usage` snapshots, pre-registered success criteria (quota down,
  stalls flat).
- **Accept:** `measure.py report` produces the comparison table from synthetic
  fixture logs; a fixture where stalls rise triggers the "do not claim a win"
  verdict.

### Phase 5 — maintenance rails (from the maintenance research)
- Stub-LLM smoke tests already exist from Phase 2 — wire into CI on every PR.
- Nightly live canary: ONE tiny request per deployment path via LiteLLM health
  checks or a cron script; fail loudly.
- Renovate config with a custom datasource watching Claude Code releases +
  `models.json`/`KNOWN_GOOD_VERSIONS.md` as the model-ID manifest.
- **Accept:** CI runs token-free tests; canary demonstrably alerts when an
  endpoint is down (test by pointing one at a dead URL).

### Phase 6 — EduCloud generalization + release prep
- Add sovereign endpoints (Jetstream2; later campus HPC via `hpc-as-api`) as
  LiteLLM deployments. Confirm Jetstream2 external-access status first; if
  still network-gated, document the run-on-instance deployment mode.
- Write the release README positioning the novelty (quota+sovereign fusion,
  runnable-check governance, measurement method) with related-work citations
  (STREAM, llm-router/9router/OmniRoute, CrewAI guardrails, ScopeGate).
- Tag `herdr-meters` with the `herdr-plugin` topic when the user says go.
- **Accept:** a second machine can reproduce the stack from README alone.

## 5. Environment & secrets (never commit)
`ANTHROPIC_API_KEY`, `OPENAI_API_KEY` (Codex API path, if used),
`OPENROUTER_API_KEY` (optional tier), `PERPLEXITY_API_KEY` (Sonar only),
`JETSTREAM2_TOKEN` (when external access is live). LiteLLM master key if the
proxy is exposed beyond localhost. Ollama needs none.

## 6. Standing rules (from the design process — do not regress)
1. Quota logic: on flat subscriptions, fewer/cheaper-position turns beat
   cheaper models; start tiers at the level most likely to one-shot.
2. Opus (and any `scarce: true` target) is never auto-downshifted for gates,
   never auto-spent without the ladder or a pin justifying it.
3. Sensitive data never reaches shared/cloud tiers — enforced by config absence
   and the deterministic classifier layer, never by model judgment.
4. The classifier asks; it doesn't rewrite. Uncertainty escalates upward.
5. No fan-out orchestration; parallelize only across meters or file-disjoint
   plan stages.
6. Every efficiency claim must survive the ceiling-stall check in `measure.py`.
7. Multi-account rotation to multiply subscription throughput is against
   vendor ToS — out of scope, permanently.

## 7. Known open questions (verify at build time, don't assume)
- Exact `claude -p` / `codex` / `ccr` model+effort flag syntax on installed
  versions (drafts guessed; Phase 2 verifies).
- LiteLLM Anthropic-format passthrough sufficiency for Claude Code (Phase 1).
- Herdr CLI JSON shapes on the installed version (Phase 3).
- Jetstream2 external access + current model list (Phase 6).
- Whether Anthropic/OpenAI have shipped a programmatic usage endpoint since
  July 2026 — if yes, wire it into `measure.py` and herdr-meters availability
  and delete the manual-snapshot instructions.
