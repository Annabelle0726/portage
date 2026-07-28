# HANDOFF — build instructions for Claude Code

**Read `PLATFORM.md` first** — it is the capstone definition (final open-model
platform + the comparison suite against Claude/Codex/Perplexity) and supersedes
this file where they conflict. Its §9 appends Phase 6a + Phases 7–10 to the plan
below. **Then read `REVISION-PLAN.md`** — the 2026-07 Scale-1 transition
(open-first ladder + PAYG ceiling) that Phase 6a operationalizes.

This repo contains drafts, specs, and decisions from a long design process. Your
job is to turn it into a small, working, maintainable system — **building as
little as possible**. The design principle that governs everything: prefer
configuring an existing tool over writing code, and keep custom code to the thin
layer that is genuinely novel.

Read `PROJECT.md` (mission + novelty claim) and `specs/00`–`11` for rationale.
This file is the execution plan and overrides drafts where they conflict.

---

## 1. What this is

A meter- and sovereignty-aware routing layer for coding agents, piloted
personally (local open-weight → hosted open-weight → PAYG frontier ceiling) and
generalized to institutional compute (EduCloud / NSF ACCESS / Jetstream2). Core
ideas, in one line each:

- **Meters, not models:** the scarce resource is a budget the router must respect
  — a PAYG dollar ceiling, an institutional allocation, or open-only-displacement
  headroom — not per-token dollars.
- **Free before metered, sovereign before scarce, proprietary last;** sensitive
  data pinned to local by deterministic rule.
- **Deterministic fail-up guard:** a runner decides pass/fail (diff + lint +
  tests), never the model's self-report; failures escalate one tier up. An
  unreachable tier is skipped as `unavailable`, not scored as a failure.
- **Triage before routing:** a free local classifier catches underspecified
  tasks before they waste a frontier turn, then picks provider + model + effort.
- **Measured, not asserted:** baseline-vs-treatment evidence that quota went
  down while ceiling-stalls stayed flat, plus `proprietary_displacement` (the
  open-only flip trigger).

## 2. Buy-over-build resolution (FINAL — do not rebuild these)

| Drafted in repo | Verdict | Replace with |
|---|---|---|
| `scripts/sovereign_broker.py` | **DELETE — fully covered** | **LiteLLM proxy.** One `config.yaml` gives cooldowns (429 → immediate cooldown), ordered failover (`order=1,2,3` = free→allocation→paid), background health checks, retries/backoff, Ollama + Anthropic + OpenAI-compatible endpoints, spend logging. Express free-before-metered as deployment `order`; the sovereign pool is just multiple deployments of the same `model_name`. |
| `.claude-code-router/*` configs | **RESOLVED Phase 1 — deleted.** | Claude Code talks to LiteLLM's Anthropic-compatible `/v1/messages` directly (verified: `docs/phase-1-findings.md`). `.claude-code-router/` and all its configs are gone; the CI review job and `plan.py`'s planner call now use native `claude -p`. Codex's path through LiteLLM remains unverified (Codex CLI not installed) — open question for Phase 3. |
| OpenRouter hosted-open tier | **CONFIG, not code.** | A LiteLLM deployment group with a hard open-weight allowlist (models not on the list aren't deployments) + provider routing by price/throughput/latency + optional ZDR. Do NOT write a custom aggregator or use an unrestricted auto-router. Allowlist manifest = `herdr-meters/models.json` (license + quant floor per model). |
| Together / DeepInfra direct-open tier | **CONFIG, not code.** | LiteLLM deployments (serverless, OpenAI-compatible). Together primary, DeepInfra optional — redundancy against OpenRouter, and the bench compares aggregation vs direct on the same model. |
| Open research stack (Science lane) | **DEPLOY, not build.** | **SearXNG** (self-hosted metasearch) + open fetch/crawl behind the citation-resolution verifier (`PLATFORM.md` §7). Required to test against Perplexity and to make the sovereign research path real. |
| `scripts/scheduler.py` | **SHRINK.** | cron/launchd + a 20-line queue drain. Keep only enqueue/drain; delete the reset-estimate math (it was mostly moot for Lane B — see specs/04). |
| `scripts/plan.py` decomposition | **KEEP, thin.** | The per-subtask *runnable acceptance check* + human plan gate is the novel bit. Do NOT adopt Spec Kit/BMAD wholesale — they're heavier and lack the runnable-check enforcement. |
| `scripts/failup.py` | **KEEP.** | This is the contribution's core mechanism. Harden per §4, and add the `unavailable` vs `model_failed` split (Phase 2). |
| `scripts/measure.py` | **KEEP, but read LiteLLM's spend logs** for token/cost columns instead of duplicating; our custom metrics (win-tier distribution, ceiling-stall rate, `proprietary_displacement`, rescue efficiency, /usage snapshots) stay. |
| `herdr-meters/` plugin | **KEEP.** | Novel; no existing Herdr plugin does cross-vendor meter routing. Publishes via the `herdr-plugin` GitHub topic. |
| `herdr-meters/classify.py` | **KEEP.** | Free local triage+routing; deterministic pins + license/allowlist check first. |
| Lane A hooks (`.claude/hooks/*`) | **KEEP as-is.** | Already thin uses of native PreCompact/SessionStart. |
| `.claude/agents/*`, skills, CLAUDE.md | **KEEP as-is.** | Native Claude Code features, already minimal. |
| `scripts/ai` dispatcher | **DEPRECATE** in favor of the herdr-meters plugin (same function, better surface). Keep only if the user asks for a non-Herdr path. |
| Local serving (`local-serve.sh`) | **KEEP;** consider MLX later for throughput on Apple Silicon; not required. |

Also reuse, don't rebuild: STREAM's `hpc-as-api`/`streamrelay` for exposing HPC
jobs as OpenAI-compatible endpoints (they become LiteLLM deployments); in
EduCloud, **Outfitter** provisions/reaps the sovereign inference nodes and
Portage routes onto them; native Claude Code auto Opus→Sonnet downshift, effort
levels, Task Budgets (Lane A pilot only).

## 3. Target architecture (post-consolidation)

```
Lane A (interactive pilot — retiring)     Lane B (automation, open-first ladder)
────────────────────────────────          ─────────────────────────────────────────
native claude + hooks + skills            claude -p / open runners
herdr panes: claude | local               failup.py --runner ... ──▶ tiers.<mode>.json
herdr-meters plugin:                                     │
  classify (local 7B) → triage/route      LiteLLM proxy :4000  ◀── plan.py stages
  dispatch / board / mark                   deployments (by order):
                                              local_fast/burst (ollama, order=1, free)
                                              sovereign jetstream2 / HPC (order=2)
                                              openrouter allowlist (order=3)
                                              together / deepinfra (order=4)
                                              anthropic/openai PAYG (order=5, hybrid only,
                                                boundary-gated, budget-capped)
                                            cooldowns, health, spend logs
measure.py reads: failup-log, decomp-log, LiteLLM spend, /usage + displacement
```

Sensitive workspaces: `policy_mode: sovereign` — a LiteLLM config variant whose
`model_list` contains ONLY local deployments (the pin is enforced by absence,
same as before; stricter than `open_weight_only`, which still allows hosted-open).

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
  non-local models. **[DONE — see `docs/phase-1-findings.md`.]**

### Phase 2 — guard + decomposer hardening
- `failup.py`: verify `--model`/`--effort` flags against the REAL installed CLI
  versions (this was never verified — treat all CLI invocations as unverified
  until you run them); unit-test the ladder logic, budget ceiling, stash/reset
  recovery with a stub runner (a fake script that succeeds/fails on command) —
  zero tokens. **Add the `unavailable` vs `model_failed` split:** a
  connection-refused / timeout on a rung logs `unavailable` and skips to the
  next rung; only a verifier failure logs `model_failed` and counts as a real
  escalation. This keeps availability noise out of win-tier stats and router
  priors.
- `plan.py`: unit-test extract/validate/toposort/MANUAL-stop with fixtures;
  same stub-runner approach.
- **Accept:** `uv run pytest` green with NO network and NO model calls;
  a stubbed hard task demonstrably escalates through the ladder and a stubbed
  budget cap stops below the proprietary rung with the correct message; a
  stubbed offline rung logs `unavailable` and is skipped, not escalated.

### Phase 3 — herdr-meters plugin
- Verify against the installed Herdr version: `pane list` output shape,
  `pane run` semantics, plugin env vars. Fix `find_pane` matching accordingly.
- Wire `dispatch` to prefer LiteLLM-routable targets where applicable; keep the
  scarce-confirmation and sensitive-pin behavior exactly as drafted.
- Test `classify.py` against the real local model on ~15 real tasks from the
  user's history; tune keyword rules only where the model misses. Add the
  license/allowlist check to the deterministic layer (R2, `specs/09`).
- **Accept:** `herdr plugin link` + `board`/`picker`/`dispatch`/`mark` work in
  a live Herdr session; sensitive phrasing never reaches a non-local target
  (add a test asserting the deterministic layer fires before any subprocess).

### Phase 4 — measurement
- Point `measure.py` at LiteLLM's spend/log store for token+cost columns; keep
  run_id grouping, win-tier distribution, ceiling-stall rate, and the honest
  verdict line. Add `decomp-log` ingestion. **Add reports:** per-rung solve %,
  `unavailable` vs not-good-enough failures, `proprietary_displacement` (of
  verified successes, % that would become stalls if the PAYG rung were removed),
  and rescue efficiency (proprietary $ that flipped failure→success ÷ total
  proprietary $).
- Write the pilot protocol doc: baseline week (no routing) vs treatment week,
  daily `/usage` snapshots, pre-registered success criteria (quota down,
  stalls flat).
- **Accept:** `measure.py report` produces the comparison table + a displacement
  report from synthetic fixture logs; a fixture where stalls rise triggers the
  "do not claim a win" verdict.

### Phase 5 — maintenance rails (from the maintenance research)
- Stub-LLM smoke tests already exist from Phase 2 — wire into CI on every PR.
- Nightly live canary: ONE tiny request per deployment path via LiteLLM health
  checks or a cron script; fail loudly.
- Renovate config with a custom datasource watching Claude Code releases +
  `models.json`/`KNOWN_GOOD_VERSIONS.md` as the model-ID + allowlist manifest.
- **Accept:** CI runs token-free tests; canary demonstrably alerts when an
  endpoint is down (test by pointing one at a dead URL).

### Phase 6a — Scale-1 transition (open-first + PAYG ceiling) — see `REVISION-PLAN.md` §5
- Extend the LiteLLM config: OpenRouter deployment group (open-weight allowlist
  enforced in config), Together direct group (DeepInfra optional), budgets +
  cooldowns; wire Anthropic/OpenAI/Perplexity as the PAYG ceiling with per-task-
  class `proprietary_budget` and the escalation boundary (verified open failure /
  documented specialist / explicit override).
- **Bench baseline while subscriptions are still live:** run the 12-task pilot
  cut, arms A1 (platform) and A4 (native Claude Code on Max), commit results +
  prereg, date-stamped. **Then** cancel Claude Max / Codex Plus / Perplexity Pro
  and record the cancellation date (a cost-accounting epoch).
- **Accept:** a curl reaches an allowlisted model via OpenRouter; a
  non-allowlisted model 404s; killing OpenRouter fails over to Together; the
  PAYG rung refuses dispatch without a `proprietary_budget > 0` task class and
  logs its spend separately; the weekly `proprietary_displacement` report runs.

### Phase 6 — EduCloud generalization + release prep
- Add sovereign endpoints (Jetstream2; later campus HPC via `hpc-as-api`) as
  LiteLLM deployments — provisioned/reaped by **Outfitter** in EduCloud. Confirm
  Jetstream2 external-access status first; if still network-gated, document the
  run-on-instance deployment mode. Add the per-lane `policy_mode` posture
  (`specs/02` §"Per-lane policy modes").
- Write the release README positioning the novelty (meter+sovereign fusion,
  runnable-check governance, measurement method incl. displacement) with
  related-work citations (STREAM, llm-router/9router/OmniRoute, CrewAI
  guardrails, ScopeGate).
- Tag `herdr-meters` with the `herdr-plugin` topic when the user says go.
- **Accept:** a second machine can reproduce the stack from README alone.

## 5. Environment & secrets (never commit)
`ANTHROPIC_API_KEY`, `OPENAI_API_KEY` (Codex/PAYG path), `OPENROUTER_API_KEY`
(hosted-open tier), `TOGETHER_API_KEY` / `DEEPINFRA_API_KEY` (direct-open tier),
`PERPLEXITY_API_KEY` (Sonar research specialist), `JETSTREAM2_TOKEN` (when
external access is live). LiteLLM master key if the proxy is exposed beyond
localhost. Ollama needs none. **No subscription credentials in the production
ladder** — Claude Max / Codex Plus keys, if kept at all, live only in the Parity
Bench baseline harness.

## 6. Standing rules (from the design process — do not regress)
1. Meter logic: route free-before-metered, sovereign-before-scarce,
   proprietary-last; a rung is reached only when everything below it failed
   verification or is `unavailable`.
2. The proprietary PAYG rung (and any `scarce: true` target) is never reached
   except on verified open failure, a documented specialist need, or an explicit
   override; never auto-spent because it would perform better.
3. Sensitive data never reaches shared/cloud tiers — enforced by config absence
   (`policy_mode: sovereign`) and the deterministic classifier layer, never by
   model judgment and never by a provider's ZDR/retention promise.
4. The classifier asks; it doesn't rewrite. Uncertainty escalates upward.
5. No fan-out orchestration; parallelize only across meters or file-disjoint
   plan stages.
6. Every efficiency claim must survive the ceiling-stall / non-inferiority check
   in `measure.py`. `unavailable` events are excluded from quality stats.
7. Multi-account rotation to multiply subscription throughput is against
   vendor ToS — out of scope, permanently.

## 7. Known open questions (verify at build time, don't assume)
- Exact `claude -p` model+effort flag syntax: **RESOLVED Phase 1**, see
  `KNOWN_GOOD_VERSIONS.md`. `codex` flag syntax remains open — Codex CLI is not
  installed on the dev machine; verify on first machine that has it (Phase 3).
- LiteLLM Anthropic-format passthrough sufficiency for Claude Code: **RESOLVED
  Phase 1** — yes, direct, no shim. See `docs/phase-1-findings.md`.
- OpenRouter open-weight allowlist enforcement + provider-restriction syntax in
  a LiteLLM deployment (Phase 6a) — verify a non-allowlisted model actually
  fails closed.
- Herdr CLI JSON shapes on the installed version (Phase 3).
- Jetstream2 external access + current model list (Phase 6).
- Whether Anthropic/OpenAI have shipped a programmatic usage endpoint since
  July 2026 — if yes, wire it into `measure.py` and herdr-meters availability
  and delete the manual-snapshot instructions.
