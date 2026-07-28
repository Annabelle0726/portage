# PROJECT — meter- and sovereignty-aware routing for coding agents

The focused contribution. Not a personal-efficiency tool (on a flat Claude
subscription, discipline beats orchestration — see `docs/specs/03`). This is the one
part with a reason to exist as open source: the piece that **isn't** just Claude.

> **Naming note (2026-07):** the original thesis said "subscription-quota-aware."
> The Scale-1 transition (`docs/specs/11`, `REVISION-PLAN.md`) removes fixed
> subscription rungs from the production ladder, so the general term is now
> **meter-aware**: a meter is any scarce budget the router must respect — a PAYG
> dollar ceiling, an institutional allocation balance, or the
> `proprietary_displacement` headroom that governs the open-only flip.
> Subscriptions survive only as an *instrumented benchmark baseline* (Parity
> Bench arms), not as a routed tier. The fusion claim below is unchanged and
> arguably cleaner without the subscription framing.

## Thesis (the unoccupied intersection)

Every existing coding-agent router optimizes one of two things and never both:

- Commercial routers (LiteLLM, OpenRouter, Portkey) optimize **per-token dollars**.
- The newer quota-aware routers (llm-router, 9router, OmniRoute) optimize
  **subscription quota** — but their "free" tier is always a commercial free tier
  or the user's own local model.
- The HPC-inference systems (STREAM/`hpc-as-api`, FIRST, Jetstream2) treat
  **institutional/research compute as sovereign, zero-marginal-cost** — but they
  are not coding-agent routers and reason about cloud dollars, not the meters a
  self-hoster actually faces.

**Nobody combines meter-awareness (PAYG budgets + institutional allocation) with
institutional/research compute (NSF ACCESS / Jetstream2) as a sovereign zero-cost
tier, gated by a deterministic acceptance check.** That intersection is this
project. The routing order inverts the commercial default:
`local → sovereign HPC → hosted open-weight → paid frontier (boundary-gated)` —
overflow goes to compute you already control *before* the scarce, metered tier,
and proprietary inference is a verified-failure rescue path, never a fixed rung.

This generalizes the resource-aware-tiers + governance-grader pattern already
proven in `peer-tutor-framework` (Jetstream2 tiers, a deterministic solution-leak
grader) from the tutoring domain into a standalone coding-agent layer.

## Scope

**In (core to the contribution):**
- The tier ladder `local → sovereign (jetstream2) → hosted open-weight →
  proprietary PAYG` (`tiers.educloud.json` / the mode configs in `docs/specs/10`–`11`)
  and its configs, incl. the sensitive-data pin (`config.educloud-sensitive.json`,
  local-only by construction).
- The **open-weight allowlist governance** at the `remote_open` tier: Herdr
  selects an allowlisted model (license + quantization-floor metadata);
  OpenRouter selects only an approved infra provider. Model policy stays in
  Herdr; commodity choice is delegated.
- The **deterministic fail-up guard** (`failup.py`) — escalation decided by a
  runner, never the model's self-report; and now distinguishing an *unavailable*
  rung (skip, capacity noise) from a *failed* rung (escalate, quality signal).
- The **proprietary escalation boundary** — T7 (PAYG frontier) is reachable only
  on verified open failure, a documented specialist need, or an explicit
  override; never because it would simply perform better.
- The **plan-first decomposer** (`plan.py`) with per-subtask *runnable* acceptance
  checks and a runnable integration check.
- The **measurement harness** (`measure.py`) — the reproducible baseline-vs-
  treatment evidence, now including `proprietary_displacement` (the open-only
  flip trigger) and rescue efficiency (did proprietary dollars actually convert
  failure to success). This is the half the ecosystem lacks and the reason to
  publish.
- Maintenance/CI: version pinning, stub-LLM smoke tests, a nightly live canary,
  Renovate custom-datasource drift detection.
- A generalizable policy schema so others plug their own tiers/backends.

**Out (kept as optional scaffolding, not the contribution):**
- Claude-only efficiency pilot (`docs/specs/03`, now HISTORICAL), OpenRouter cost
  routing, the personal multi-surface/scheduling quota tooling. Useful to *me*;
  not novel.
- Runtime prompt engineer, fan-out arbiter, from-scratch router, sophisticated
  classifier. The fail-up guard makes the classifier unnecessary.
- Fixed proprietary subscription rungs (Claude Max / Codex Plus) as *routed*
  tiers — retired from the production ladder; retained only as Parity Bench
  baseline arms (`PLATFORM.md` §5).

## Related work (position against, don't reinvent)

- **Sovereign compute:** STREAM (arXiv 2606.13968) + `hpc-as-api`/`streamrelay`
  already solve HPC firewall traversal + OpenAI-compatible exposure — build on
  them; Jetstream2 inference service (NSF ACCESS 2005506) is the reference backend.
- **Quota-aware routing:** llm-router, 9router, OmniRoute — study their 5h/weekly
  bucket tracking; note the missing HPC tier is the gap.
- **Deterministic gates:** CrewAI function guardrails, DSPy assertions, ScopeGate
  (arXiv 2606.28679), AutoPyVerifier — cite these; differentiate on *what* the gate
  governs (tier/meter escalation + the proprietary boundary), not that a gate
  exists.

## Roadmap

**Stage 1 — harden (in progress):**
- [x] Per-subtask acceptance checks are runnable and enforced outside the model.
- [x] Robust plan JSON extraction with validation + raw dump on failure.
- [ ] Pin CLI + router + model IDs; encode the guard's rules as unit tests.
- [ ] Stub-LLM smoke tests for the guard, decomposer, and tier router (token-free).
- [ ] Split `unavailable` from `model_failed` in the guard + telemetry (docs/specs/11).

**Stage 2 — measure (the result):**
- [ ] Baseline vs. treatment week on `taskcapture` via `measure.py`; defend
      "quota down, ceiling-stalls flat."
- [ ] `proprietary_displacement` report + rescue-efficiency report from real logs.
- [ ] Nightly live canary per provider path.

**Stage 3 — differentiate & publish:**
- [x] Sovereign tier is a *federation* (`litellm.config.yaml` model groups): a pool
      of institutional endpoints with free-before-metered, health-aware failover
      to the proprietary ceiling — provided natively by LiteLLM (ordered
      deployments + cooldowns), not custom code. See `~/dev/educloud/docs/specs/05-federated-sovereign.md` (relocated at CC-P0 v2 per CW02 §4) and HANDOFF §2.
- [ ] Reuse `hpc-as-api`/`streamrelay` to expose each endpoint; add HPC-queue /
      allocation-balance awareness (current health is lazy circuit-breaking only).
- [ ] Meter-window awareness reads a recorded /usage or a PAYG budget balance
      (or a real endpoint if a provider ships one).
- [ ] Release the policy pack + measurement method + the meter+sovereign fusion as
      the novelty, with related-work citations to preempt "already exists."

## Time-sensitivity

The novelty is a mid-2026 snapshot: the quota-aware routers are one changelog away
from adding an ACCESS/HPC tier. If planting the flag on the fusion, the window is
now, and the measurement evidence is what makes it a result rather than a claim.

---

## Parked (defined later)

Per CC-P0 v2 Step 5 — recorded so nothing is silently forgotten, not written
as code:

- **OpenHands substrate adoption beyond Lane B basics.** HB-1 wires the basic
  Docker autonomy tier only. Deeper adoption (custom agent skills, multi-repo
  runs) is revisited after the HB-1 report shows what the basics actually need.
- **The Postgres outcome store and Langfuse wiring.** Both are commented out in
  the LiteLLM config (`# database_url`, `# success_callback: ["langfuse"]`) —
  Phase 8 per `docs/PLATFORM.md` §6. `measure.py` + JSONL is sufficient at
  Scale 1; a hosted trace store is infrastructure weight one user doesn't need
  yet.
- **Adaptive routing and retraining.** The steward's classify/adapt loop stays
  rule-based (deterministic pins + statistical priors, Beta-Binomial per
  `docs/BUILD-PLAN.md`) until calibration volume exists. HB-4, parked, per the
  herdr-build-plan's own routing-collapse caution.
- **The steward fine-tune.** The base open-weight model runs unmodified. A
  tuned variant is HB-4 work, gated on calibration data existing to tune
  against, and on the collapse guards from the pitfall register landing first.
- **Lane verifiers beyond leak and code.** Today: the leak-over-retrieval gate
  (Belay) and the runnable code check (`failup.py`/`plan.py`). Additional
  verifier lanes (math, factual, citation) are HB-2/S1 scope, pending the
  CC-P1 verifier-contract repo stabilizing first — see CW02-decisions.md §2.3.
