# 08 — Scale tiers (post-landscape-report architecture)

Source: `routing-layer-landscape-2026.md` (uploaded survey). Its verdicts:
**build** the fail-up guard, herdr-meters, and the quality-adjusted-efficiency
metric (all three confirmed as gaps — 112 herdr plugins surveyed, none do
cross-vendor quota; no library does verifier-decides + tier-escalation; no
observability tool ships the stall-gated efficiency metric). **Partially adopt**
OpenSpec (plan schema only), vLLM Semantic Router (classifier backend only),
and Langfuse (trace store only). **Reference, don't adopt** STREAM (no public
repo yet) and FIRST (production at ALCF but DOE-gated, not ACCESS).

**The design rule that falls out:** the custom core — fail-up guard, triage
wrapper (deterministic pins + clarify-before-dispatch), herdr-meters, metric
logic — is *identical at every scale*. Scales differ only in (a) the tier
ladder and (b) which heavy backends are justified. Adopt infrastructure only
when the scale earns it; every adoption below is reversible because the custom
core never depends on backend internals.

> **Updated 2026-07 (Scale-1 transition, `specs/10`–`11`, `REVISION-PLAN.md`).**
> The Scale-1 ladder below has changed: fixed subscription rungs (Claude Max /
> Codex Plus) are removed from the production ladder and replaced by hosted
> open-weight (OpenRouter/Together) + a boundary-gated proprietary **PAYG**
> ceiling. Subscriptions survive only as Parity Bench baseline arms. The
> scale-invariance rule is unchanged.

---

## Scale 1 — Personal (laptop/iMac + open-weight + PAYG ceiling)

Ladder (`policy_mode: hybrid`): `local_fast (iMac) → local_burst (MacBook) →
[local_large: future 128GB] → remote_open (OpenRouter, open-weight allowlist) →
remote_open_direct (Together; DeepInfra optional) → proprietary_payg
(Anthropic/OpenAI PAYG, boundary-gated)`. Perplexity Sonar is the Science-lane
PAYG specialist behind the open research stack, not an app subscription. End
state (`open_weight_only`, `specs/10`) drops the last rung.

| Component | Scale-1 choice | Why |
|---|---|---|
| Proxy spine | **LiteLLM**, one config.yaml per mode | Already decided; lightweight at n=1 |
| Guard / triage / meters plugin | **Custom core, as drafted** | Report confirms no substitute exists |
| Hosted-open aggregation | **OpenRouter** — config, not code; hard open-weight allowlist, provider routing by price/throughput/latency, optional ZDR | The survey confirms provider-restriction + fallback controls are native; do NOT use an unrestricted auto-router that could select proprietary models |
| Hosted-open direct backup | **Together** (serverless per-token), **DeepInfra** optional | Removes OpenRouter as a single dependency; lets the bench compare aggregation vs direct on the same model. Both are just LiteLLM deployments |
| Proprietary ceiling | **Anthropic/OpenAI/Perplexity PAYG** behind LiteLLM budgets, boundary-gated | No fixed subscription rung; reached only on verified open failure / documented specialist / explicit override |
| Classifier backend | **Ollama 7B + keyword rules** — do NOT deploy vLLM Semantic Router | vLLM SR is deployment-grade (BERT models, dashboard, Envoy); overkill for one user, and the report confirms the clarify/override wrapper stays custom regardless |
| Plan schema | plan.json as drafted; **OpenSpec format optional** | Cheap to adopt early (it's just a schema + 28k-star tooling), required at Scale 3 — adopting now avoids a migration |
| Measurement | **measure.py + JSONL** — no Langfuse | A hosted/unit-priced trace store is infrastructure weight one user doesn't need; the JSONL already feeds the metric, now incl. `proprietary_displacement` + rescue efficiency |

This scale is complete with what's in the repo + LiteLLM. **Nothing new to
adopt** — OpenRouter, Together, and the PAYG providers are all LiteLLM config,
not new dependencies. The transition itself is Phase 6a in `REVISION-PLAN.md`.

## Scale 2 — + HPC (Jetstream2)

Everything in Scale 1, plus the **sovereign tier** made real. It already occupies
its slot between free-local and hosted-open in the unified ladder (`T4`); at
Scale 1 it is simply empty. `local → sovereign HPC (free, no quota draw) →
hosted open → proprietary PAYG`.

- **Custom Jetstream2 adapter** (the report confirms nothing turnkey exists:
  STREAM is a June-2026 paper without a confirmed public repo; FIRST is real
  and production — ~35 models behind an OpenAI-compliant gateway at ALCF — but
  gated to DOE accounts, not NSF ACCESS). Borrow both designs: Globus
  Auth/Compute for control plane, OpenAI-compatible exposure, and STREAM's
  dual-channel firewall traversal pattern if off-instance access is needed. In
  EduCloud, **Outfitter owns provisioning/reaping of these nodes**; Portage
  consumes the endpoints Outfitter reports healthy.
- **Deployment mode first, adapter second:** Jetstream2's inference API is
  network-gated, so the zero-adapter path is running Lane B *on* a JS2 VM
  where the endpoint is native — a LiteLLM deployment entry and nothing else.
  Build the external adapter only when off-instance access is confirmed live.
- **Data pin unchanged and non-negotiable:** JS2 is sovereign, *not private*
  (shared infra, admin-visible, research-use-only). Sensitive lanes keep
  `policy_mode: sovereign` (local-only); the sovereign HPC tier is absent by
  construction there.
- Watch item (from the report): Globus-based DOE↔NSF federation could make
  FIRST-style service reachable to ACCESS users "without warning" — recheck
  quarterly; it would replace most of the custom adapter.

## Scale 3 — Full EduCloud (federated, multi-user, published)

Everything in Scale 2, with the pool widened and the heavy backends now earning
their weight:

- **Federation = LiteLLM deployments**, nothing more: multiple sovereign
  endpoints (JS2 + campus HPC + any ACCESS resource) as same-`model_name`
  deployments with `order` = free-before-allocation and native cooldowns.
  The deleted custom broker stays deleted. Per-course virtual keys are the
  course-level meter; Keycloak (Waypoint) fronts authn.
- **Adopt vLLM Semantic Router as the classification backend** (Apache-2.0,
  4.3k stars, weekly releases; ModernBERT intent classification, session-aware
  routing, PII detection that *complements* — never replaces — the
  deterministic sensitive pin). The custom wrapper survives on top: the report
  is explicit that clarify-before-dispatch and pre-model override hooks are
  not in its feature set.
- **Adopt Langfuse as the trace/score store**; the stall-gated efficiency
  metric and `proprietary_displacement` remain custom scores/aggregations on
  its exported traces (~50–100 lines instead of a bespoke logging backend).
  Mind unit-based pricing at institutional volume.
- **Adopt OpenSpec's `changes/` + GIVEN/WHEN/THEN schema** for plans (required
  here for community compatibility); keep the custom runnable-check executor
  and human gate — the report found no SDD tool that makes runnable
  per-subtask acceptance commands a first-class object.
- **Publish:** herdr-meters to the plugin marketplace (confirmed gap), and the
  guard + measurement method + meter-sovereign fusion as the release/paper.
  Novelty verified current: neither 9Router nor OmniRoute (v3.0.0, 67+
  providers) has an institutional tier — both remain commercial-subscription
  arbitrage. The per-lane `proprietary_displacement` measured during pilot terms
  is the evidence base for the "public infrastructure, no proprietary
  dependency" claim in PESOSE/IUSE materials.

## Standing re-evaluation triggers (from the report's time-sensitive flags)

1. vLLM Semantic Router ships clarify-before-dispatch or deterministic
   pre-model overrides → shrink or retire the custom triage wrapper.
2. DOE↔NSF Globus federation opens FIRST-class services to ACCESS users →
   retire most of the JS2 adapter.
3. Any quota router adds a sovereign/institutional tier → the fusion novelty
   erodes; differentiation falls back to the guard + measurement method.
   Recheck quarterly; the publication window is now.
