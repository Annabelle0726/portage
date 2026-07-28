# REVISION-PLAN — Scale-1 transition: open-first ladder with a PAYG ceiling

> **July 2026 update: `LINE-P-ROADMAP.md` is now the staging plan of record
> (S0–S5).** This file remains the doc-revision record and the Phase 6a
> acceptance reference; where they differ, Line P wins. The two material
> changes: (1) the proprietary rescue line is a **$10/30-day Opus key**,
> confirm-gated behind a verified open failure, 24-hour window, no fallbacks —
> narrower than the per-task-class PAYG budgets drafted below; (2)
> subscriptions are **not** cancelled after a one-time bench baseline —
> Pro-tier arms (Claude Pro, Perplexity Education Pro) ride through the S3
> calibration window (60–90 days, $60–80 envelope, $100 ceiling) as
> instrumented comparison arms, and S4 cuts what the evidence says to cut.

*Drafted 2026-07-21 from review of `specs/10` (Open-Weight Only) and `specs/11`
(Hybrid Open-First + Proprietary PAYG) against PLATFORM.md, HANDOFF.md,
PROJECT.md, specs/02/03/08/09, `.claude/tiers.claude.json`, and
`docs/phase-1-findings.md`. This plan is the work order for the next build
sessions; nothing in the repo has been rewritten yet except the addition of
specs/10, specs/11, and this file.*

## 0. Decision recorded

- **Operating mode now:** `policy_mode: hybrid` (specs/11) — local open →
  hosted open → Anthropic/OpenAI/Perplexity **PAYG only after verified open
  failure**. Fixed subscription rungs (Claude Max / Codex Plus) exit the
  production ladder.
- **End state:** `policy_mode: open_weight_only` (specs/10). The switch is
  **empirical, not ideological**: flip when `proprietary_displacement` (specs/11
  §measure.py additions) stays below threshold — proposed **< 5% of verified
  successes over a 4-week window** (tune in prereg).
- **Scope now:** Greg's personal Scale-1 pilot (iMac + MacBook Pro). EduCloud
  deployment planning is in place (§6) but not scheduled.

## 1. What the new architecture improves (assessment)

1. **Subscription rungs removed.** The old production ladder
   (`local → Claude Max/Codex → …`, specs/08 Scale 1; `tiers.claude.json`)
   entangled routing with flat-rate psychology — specs/03's own finding was
   that discipline beats orchestration on a flat plan. All-PAYG makes every
   marginal call carry a marginal price, so *cost per verified success* is
   finally a single honest number and the router's decisions are real
   economic decisions. Amortized/quota-share accounting (PLATFORM §5.4)
   survives, but only inside the Parity Bench baseline arms.
2. **`proprietary_displacement` is the missing transition metric.** "If we
   switched to open-weight-only today, what % of currently successful tasks
   become ceiling stalls?" turns the sovereignty goal into a dashboard number
   with a flip threshold. It completes measure.py's story: the honesty gate
   said *don't claim wins that cost quality*; displacement says *when the
   frontier tier stops earning its place*.
3. **The escalation boundary is now policy, not habit.** Proprietary requires
   (a) verified open failure, (b) documented specialist need, or (c) explicit
   override (specs/11). This is the fail-up guard's philosophy promoted to the
   provider boundary — it prevents hybrid from silently re-becoming
   proprietary-first.
4. **Model-policy / infra-policy separation at `remote_open`.** Herdr picks the
   model (allowlist, license metadata); OpenRouter picks the infra provider
   under price/throughput/latency + ZDR + quantization constraints. Sovereignty
   stays in Herdr; commodity choice is delegated. Never an unrestricted
   auto-router.
5. **`unavailable ≠ model_failed`.** A sleeping MacBook is a capacity event,
   not a quality signal. Without this split, local_burst's uptime pattern
   poisons win-tier stats, adaptive-router priors (PLATFORM §6), and Parity
   data. Small change, large integrity payoff.
6. **Capability aliases over model names** (`local/code-large`,
   `proprietary/reasoning`…). Matches the steward design (specs/09) and LiteLLM
   model-groups; Parity Bench assigns the winner behind each alias. Business
   logic stops churning with model releases.
7. **Rescue-efficiency metric**: proprietary dollars that converted verified
   failure → success ÷ total proprietary dollars. The ceiling must earn its
   keep in flipped outcomes, not plausible prose.
8. **Hardware purchase becomes a measured decision.** The 128 GB node is bought
   when telemetry shows local-too-small failures that hosted-open solves at
   volume (specs/10 §hardware rule) — capex version of buy-over-build.
9. **Aggregator redundancy.** Together (serverless per-token) as direct backup,
   DeepInfra optional — removes OpenRouter as a single point of dependency and
   lets the bench compare aggregation vs direct on the same model.
10. **Perplexity demoted from fixed app subscription to metered specialist**
    behind the open research stack (SearXNG + citation-resolution verifier,
    already PLATFORM §7). Same pattern as code: open first, PAYG rescue,
    measured.

## 2. Conflicts, gaps, and sequencing risks (resolve during revision)

1. **The sovereign HPC rung is absent from specs/10–11.** Understandable at
   personal Scale 1 (no allocation wired yet), but `local → sovereign →
   subscription → API` is PROJECT.md's *thesis*. The unified ladder (§3)
   reinserts **T4 sovereign** between local and hosted-open; it simply sits
   empty until Jetstream2/campus endpoints exist (HANDOFF Phase 6). Do not let
   the Scale-1 docs erase the novelty claim.
2. **Cancel subscriptions AFTER the bench baseline.** Parity Bench arm A4
   (native Claude Code on Max) and the amortized/quota-share accounting
   require live subscriptions. Sequence: run the 12-task pilot cut (PLATFORM
   §8) across A1/A4 while Max is active → then cancel (specs/11 Phase A
   "cancel once the PAYG hatch is tested"). If cancellation happens first,
   A4 becomes API-priced and the amortized arm is declared historical in the
   prereg — acceptable, but decide, don't drift.
3. **PROJECT.md's novelty wording needs a careful edit, not a rewrite.**
   "Subscription-quota-awareness" generalizes to **meter-awareness**: meters
   are now PAYG budgets, allocation balance, and displacement — subscriptions
   remain only as instrumented baseline. The fusion claim (meter-aware routing
   + sovereign compute + deterministic gate) is intact and arguably cleaner.
4. **Quantization variance on OpenRouter.** The same allowlisted model can be
   served at different quants by different providers. Allowlist entries carry a
   quantization floor; Parity Bench benchmarks **per endpoint**, not per model
   name, before an endpoint earns production traffic.
5. **ZDR is not the sensitive pin.** Optional ZDR on remote-open is defense in
   depth for *ordinary* work. The sensitive lane remains **config absence**
   (no non-local deployments exist in that model_list) — never a runtime check,
   never delegated to a provider's retention promise.
6. **Ladder-walk latency on known-hard tasks.** Walking T1→T6 before rescue
   costs wall-clock. Mitigation already in specs/11: per-task-class
   `proprietary_budget` — classes with a displacement track record get a
   bounded pre-authorized ceiling; routine classes get budget 0. Triage (R1/R2)
   assigns the class; the guard still requires the open attempt unless the
   class is documented specialist.
7. **Supersessions.** specs/03 (Max-wallet pilot) → mark HISTORICAL (its
   findings stand; its config retires). `.claude/tiers.claude.json` → retire
   after Phase A (Lane A native fallback may keep a copy pointed at LiteLLM
   aliases). specs/02's ladder and specs/08's Scale-1 table → rewritten per §4.

## 3. The unified ladder (one ladder, three modes)

```
T0 deterministic     pins, overrides, triage, license/allowlist checks   (always)
T1 local_fast        iMac warm + MacBook dynamic — ONE capability rung,
                     TWO health-checked deployments; a sleeping MacBook
                     logs `unavailable`, never `model_failed`            (always)
T2 local_large       DORMANT — future 128 GB node, enabled: auto,
                     bought on the hardware-case dashboard trigger       (always)
T3 remote_open_fast  Groq — pinned model IDs, per-model compat record    (open+hybrid)
T4 remote_open_broad OpenRouter, hard open-weight allowlist; provider
                     routing by price/throughput/latency; ZDR optional   (open+hybrid)
T5 remote_open_direct DORMANT — Together; defined, disabled; re-enable
                     trigger: OpenRouter unavailability in telemetry     (open+hybrid)
T6 proprietary       Anthropic / OpenAI / Perplexity Sonar — PAYG rescue,
                     verified open failure + budget envelope + logged
                     reason + confirm gate ($10/30d, no fallbacks)       (hybrid only)
T7 CEILING_STALL     terminal state, not a routable rung — emits the
                     stall artifact (attempted tiers + verifier evidence)
```

| Mode | Rungs | Use |
|---|---|---|
| `open_weight_only` | T0–T5 | end state; hosted open allowed (weights downloadable) |
| `hybrid` | T0–T7 | **now** — transition; T6 behind the escalation boundary |
| `sovereign` | T0–T2 (+`institutional_sovereign` at Scale 2) | clinical / student-data / EduCloud sensitive lanes — **no remote at all**, commercial or open-hosted |

Note `sovereign ≠ open_weight_only`: sovereign also excludes hosted-open
(commercial infra serving open weights). Escalation stays open-to-open before
any open-to-closed step (PLATFORM §2 rule, unchanged).

> **Revised 2026-07-28 per CW02-decisions.md §3** (dormant-slot synthesis):
> local_burst collapsed into local_fast as a second deployment; Groq added at
> T3; Together dormant at T5; sovereign is an EduCloud-profile config insert,
> not a personal rung. §4's file-by-file rows below predate this revision —
> CW-03 executed the documentation changes; read those rows as history.

## 4. File-by-file revisions

| File | Change |
|---|---|
| `PLATFORM.md` | §2 ladder → §3 above (T0–T7 + stall); §3 modes: rename full-open → `open_weight_only`, keep hybrid/sovereign, add mode-switch-is-config-only; §5.3 add displacement + rescue-efficiency to metrics; §6 note unavailable events excluded from router priors; §9 add transition phases (§5 below). |
| `HANDOFF.md` | §2 buy-over-build: add rows — OpenRouter (config, not code), Together/DeepInfra (config), SearXNG (deploy, not build); §3 diagram: Lane B deployments become local(order1) → sovereign(order2) → openrouter-allowlist(order3) → together(order4) → anthropic/openai PAYG(order5, hybrid); §4: insert Phase 6a (§5); Phase 2 gains unavailable-vs-failed in failup; Phase 4 gains new metrics. |
| `PROJECT.md` | Thesis edit per §2.3 (meter-awareness generalization); ladder line → `local → sovereign HPC → hosted open-weight → PAYG frontier (boundary-gated)`; scope-in adds allowlist governance + displacement report; subscriptions move to "benchmark baseline only". |
| `README.md` | Read-order table: add specs/10–11 + this plan; one-paragraph ladder summary update. |
| `specs/02` | Local ladder → `local_fast → local_burst → [local_large] → remote_open → remote_open_direct → PAYG (hybrid)`; EduCloud section gains per-lane policy_mode table (§6). |
| `specs/03` | Prepend HISTORICAL banner: pilot complete, subscriptions exiting production ladder; findings preserved for bench protocol. |
| `specs/08` | Scale-1 table rewritten (new ladder; OpenRouter/Together roles; "nothing new to adopt" still true — both are LiteLLM config); Scale-2 note: sovereign rung slots at T4 unchanged. |
| `specs/09` | No structural change; add license/allowlist check to R2 routing's deterministic layer; note R3 templates gain `code.remote-open.md` key. |
| `.claude/tiers.claude.json` | Retire in Phase A (see §2.7). |
| `KNOWN_GOOD_VERSIONS.md` | Add OpenRouter + Together endpoints/models as pinned entries; allowlist is versioned config with license + quant floor per model. |
| `litellm.config.yaml` (Phase 1 artifact) | Add openrouter/together deployments with `order`, budgets, cooldowns; per-mode variants: `litellm.open-only.yaml`, `litellm.hybrid.yaml`, `litellm.sensitive.yaml` (unchanged — local-only by absence). |
| `scripts/failup.py` | Distinguish connection-refused/timeout (skip rung, log `unavailable`) from verifier failure (escalate, log `model_failed`). |
| `scripts/measure.py` | New columns/reports: per-rung solve %, unavailable vs not-good-enough, `proprietary_displacement`, rescue efficiency ($→flip rate), open-inference cost per verified success. |
| `herdr-meters/models.json` | Becomes the allowlist manifest: license, weights-source, quant floor, ZDR-capable providers. |
| `KICKOFF-PROMPT.md` | Next-session scope = Phase 6a items 1–4 (§5), not Phase 0 (done). |

## 5. Pilot transition sequence (maps specs/11 Phases A→C onto HANDOFF)

**Phase 6a — PAYG transition (insert after current Phase 4/5 work, before
Phase 6 sovereign):**

1. Extend `litellm.config.yaml`: OpenRouter deployment group (allowlist
   enforced in config — models not on the list simply don't exist as
   deployments), Together direct group, budgets + cooldowns.
   *Accept:* curl through LiteLLM reaches an allowlisted model via OpenRouter;
   a non-allowlisted model name 404s; killing OpenRouter fails over to
   Together.
2. Wire Anthropic + OpenAI PAYG keys as T7 with LiteLLM budget caps;
   Perplexity Sonar API for the Science lane behind the open research stack.
   *Accept:* T7 refuses dispatch without a `proprietary_budget > 0` task
   class; spend logs show T7 separately.
3. failup.py + measure.py telemetry changes (§4).
   *Accept:* stub-runner tests — a stubbed offline rung logs `unavailable`
   and is skipped; fixtures produce a displacement report.
4. **Bench baseline while subscriptions live:** run the 12-task pilot cut,
   arms A1 (platform) and A4 (native Claude Code on Max).
   *Accept:* results committed with prereg; date-stamped.
5. Cancel Claude Max / Codex / Perplexity Pro. Record the date in
   KNOWN_GOOD_VERSIONS (it's a cost-accounting epoch).
6. Displacement cadence: `measure.py report` weekly; flip criterion per §0.

**Phase B (hardware):** buy the 128 GB node only on specs/10's four-condition
rule; it enters as T3 `local_large` deployments — no other change.

**Phase C (flip):** `policy_mode: hybrid` → `open_weight_only` = swap LiteLLM
config variant + policy flag. No code change. Announce in the changelog with
the displacement evidence attached.

## 6. EduCloud deployment plan (planning in place now; scheduled later)

Scale-invariance rule (specs/08) holds: the custom core — guard, triage,
steward, meters, metrics — is identical; only the ladder population and
tenancy change.

- **Topology:** one LiteLLM proxy per institution (or per department), virtual
  keys per course/lane; Keycloak (Waypoint) fronts authn; per-key budgets are
  the course-level meter. Postgres outcome store shared; Langfuse optional.
- **Per-lane policy modes (default posture):**

  | Lane | Mode | Rationale |
  |---|---|---|
  | Student-facing (Belay tutoring, feedback on student work) | `sovereign` | student prompts never leave institutional infra — stronger than ZDR; FERPA-aligned; the pin is config absence, per invariant |
  | Course automation (grading pipelines via Cairn) | `sovereign` or `open_weight_only` | grading content may be sensitive; hosted-open only with ZDR + institutional sign-off |
  | Staff/research lanes | `hybrid` | boundary-gated PAYG rescue, budget per PI/course |
- **Sovereign pool:** Jetstream2 / campus vLLM endpoints as T4 deployments.
  Cross-module: **Outfitter provisions the inference nodes** (its jetstream2/hpc
  adapters stand up and reap GPU instances under budget); Portage routes onto
  whatever endpoints Outfitter reports healthy. Attribution labels
  (course/assignment/student, opaque) are shared vocabulary across Portage
  spend logs and Outfitter's cost ledger.
- **Belay integration:** Belay's leak gate stays Belay's own deterministic
  verifier (never Portage's job); Portage supplies routed inference under the
  lane's policy mode; Belay's DomainPack calls declare task class so triage
  assigns budget 0 (student lanes have no T7 at all — mode, not budget,
  enforces it).
- **Adoption gate per institution:** a lane flips to `open_weight_only` /
  stays `sovereign` based on per-lane displacement measured during a pilot
  term. The same metric that governs Greg's personal flip governs
  institutional posture — one instrument, every scale.
- **Grant narrative hook:** displacement + rescue-efficiency reports are the
  evidence base for "public infrastructure, no proprietary dependency" claims
  in PESOSE/IUSE materials — measured, dated, reproducible.

## 7. Invariants that do not change (re-affirmed)

Verifier decides, never the model (failup.py authoritative). Sensitive pin by
config absence, never runtime check, never a provider's retention promise.
Triage before routing; deterministic pins always win. Honesty/non-inferiority
gates on every claim. Buy-over-build: OpenRouter, Together, DeepInfra, SearXNG
are **config/deploys, not code**. Open-to-open escalation before any
open-to-closed step. No fan-out orchestration.

## 8. Acceptance for the revision work itself

- Docs updated per §4; `specs/10`/`11` referenced as normative Scale-1 inputs.
- `litellm.hybrid.yaml` validates; allowlist manifest carries license + quant
  floor for every remote-open model.
- Stub tests: unavailable-vs-failed split; displacement + rescue reports from
  fixtures; T7 refuses without budget.
- Bench prereg updated with the accounting decision from §2.2 (baseline-first
  or historical-amortized), dated.

## 9. Phase-numbering map (canonical: S0–S5, per LINE-P-ROADMAP.md)

| S-stage | Absorbs |
|---|---|
| S0 | CC-P0 v2 (split + push), HB-0 (gateway/registry), HB-1 (frontends) |
| S1 | HB-2 (verification, budgets, paired baseline) + CC-P1 verifier-contract consumption |
| S2 | HB-3 (cache affinity, shared memory) |
| S3 | Calibration + staged cutover (the old "Phase 4") |
| S4 | HB-4 (learning loop, collapse guards) |
| S5 | Full implementation (Line P definition of done) |

PLATFORM §9's Phases 7–10 are post-S5 / Line E work. HANDOFF's Phases 0–5 and
pilot-reconciled §8's Phases 0–5 are historical numbering; where any phase
number conflicts with an S-stage, the S-stage wins (header rule, this file).
