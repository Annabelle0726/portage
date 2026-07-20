# PROJECT — quota- and sovereignty-aware routing for coding agents

The focused contribution. Not a personal-efficiency tool (on a flat Claude
subscription, discipline beats orchestration — see `specs/03`). This is the one
part with a reason to exist as open source: the piece that **isn't** just Claude.

## Thesis (the unoccupied intersection)

Every existing coding-agent router optimizes one of two things and never both:

- Commercial routers (LiteLLM, OpenRouter, Portkey) optimize **per-token dollars**.
- The newer quota-aware routers (llm-router, 9router, OmniRoute) optimize
  **subscription quota** — but their "free" tier is always a commercial free tier
  or the user's own local model.
- The HPC-inference systems (STREAM/`hpc-as-api`, FIRST, Jetstream2) treat
  **institutional/research compute as sovereign, zero-marginal-cost** — but they
  are not coding-agent routers and reason about cloud dollars, not subscription
  quota.

**Nobody combines subscription-quota-awareness with institutional/research compute
(NSF ACCESS / Jetstream2) as a sovereign zero-cost tier, gated by a deterministic
acceptance check.** That intersection is this project. The routing order inverts
the commercial default: `local → sovereign HPC → subscription quota → paid API` —
overflow goes to compute you already control *before* the scarce, metered tier.

This generalizes the resource-aware-tiers + governance-grader pattern already
proven in `peer-tutor-framework` (Jetstream2 tiers, a deterministic solution-leak
grader) from the tutoring domain into a standalone coding-agent layer.

## Scope

**In (core to the contribution):**
- The tier ladder `local → jetstream2 → sonnet → opus` (`tiers.educloud.json`)
  and its configs, incl. the sensitive-data pin (`config.educloud-sensitive.json`,
  local-only by construction).
- The **deterministic fail-up guard** (`failup.py`) — escalation decided by a
  runner, never the model's self-report.
- The **plan-first decomposer** (`plan.py`) with per-subtask *runnable* acceptance
  checks and a runnable integration check.
- The **measurement harness** (`measure.py`) — the reproducible baseline-vs-
  treatment evidence. This is the half the ecosystem lacks and the reason to
  publish.
- Maintenance/CI: version pinning, stub-LLM smoke tests, a nightly live canary,
  Renovate custom-datasource drift detection.
- A generalizable policy schema so others plug their own tiers/backends.

**Out (kept as optional scaffolding, not the contribution):**
- Claude-only efficiency pilot (`specs/03`), OpenRouter cost routing, the personal
  multi-surface/scheduling quota tooling. Useful to *me*; not novel.
- Runtime prompt engineer, fan-out arbiter, from-scratch router, sophisticated
  classifier. The fail-up guard makes the classifier unnecessary.

## Related work (position against, don't reinvent)

- **Sovereign compute:** STREAM (arXiv 2606.13968) + `hpc-as-api`/`streamrelay`
  already solve HPC firewall traversal + OpenAI-compatible exposure — build on
  them; Jetstream2 inference service (NSF ACCESS 2005506) is the reference backend.
- **Quota-aware routing:** llm-router, 9router, OmniRoute — study their 5h/weekly
  bucket tracking; note the missing HPC tier is the gap.
- **Deterministic gates:** CrewAI function guardrails, DSPy assertions, ScopeGate
  (arXiv 2606.28679), AutoPyVerifier — cite these; differentiate on *what* the gate
  governs (tier/quota escalation), not that a gate exists.

## Roadmap

**Stage 1 — harden (in progress):**
- [x] Per-subtask acceptance checks are runnable and enforced outside the model.
- [x] Robust plan JSON extraction with validation + raw dump on failure.
- [ ] Pin CLI + router + model IDs; encode the guard's rules as unit tests.
- [ ] Stub-LLM smoke tests for the guard, decomposer, and tier router (token-free).

**Stage 2 — measure (the result):**
- [ ] Baseline vs. treatment week on `taskcapture` via `measure.py`; defend
      "quota down, ceiling-stalls flat."
- [ ] Nightly live canary per provider path.

**Stage 3 — differentiate & publish:**
- [x] Sovereign tier is a *federation* (`litellm.config.yaml` model groups): a pool
      of institutional endpoints with free-before-metered, health-aware failover
      to the proprietary ceiling — provided natively by LiteLLM (ordered
      deployments + cooldowns), not custom code. See `specs/05` and HANDOFF §2.
- [ ] Reuse `hpc-as-api`/`streamrelay` to expose each endpoint; add HPC-queue /
      allocation-balance awareness (current health is lazy circuit-breaking only).
- [ ] Quota-window awareness reads a recorded /usage (or a real endpoint if
      Anthropic ships one).
- [ ] Release the policy pack + measurement method + the (a)+(b) fusion as the
      novelty, with related-work citations to preempt "already exists."

## Time-sensitivity

The novelty is a mid-2026 snapshot: the quota-aware routers are one changelog away
from adding an ACCESS/HPC tier. If planting the flag on the fusion, the window is
now, and the measurement evidence is what makes it a result rather than a claim.
