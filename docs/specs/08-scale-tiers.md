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

> **Updated 2026-07 (Scale-1 transition, `docs/specs/10`–`11`, `REVISION-PLAN.md`).**
> The Scale-1 ladder below has changed: fixed subscription rungs (Claude Max /
> Codex Plus) are removed from the production ladder and replaced by hosted
> open-weight (OpenRouter/Together) + a boundary-gated proprietary **PAYG**
> ceiling. Subscriptions survive only as Parity Bench baseline arms. The
> scale-invariance rule is unchanged. Ladder revised again 2026-07-28 per
> CW02-decisions.md §3 (dormant-slot synthesis; Groq at T3). The Scale-2/3
> sections below move to the EduCloud umbrella at CC-P0 v2 (CW02 §4).

---

## Scale 1 — Personal (laptop/iMac + open-weight + PAYG ceiling)

Ladder (`policy_mode: hybrid`): `local_fast (iMac + MacBook, two deployments)
→ [local_large: future 128GB, dormant] → remote_open_fast (Groq) →
remote_open_broad (OpenRouter, open-weight allowlist) → [remote_open_direct:
Together, dormant] → proprietary (Anthropic/OpenAI PAYG, boundary-gated)`.
Perplexity Sonar is the Science-lane
PAYG specialist behind the open research stack, not an app subscription. End
state (`open_weight_only`, `docs/specs/10`) drops the last rung.

| Component | Scale-1 choice | Why |
|---|---|---|
| Proxy spine | **LiteLLM**, one config.yaml per mode | Already decided; lightweight at n=1 |
| Guard / triage / meters plugin | **Custom core, as drafted** | Report confirms no substitute exists |
| Hosted-open fast tier | **Groq** (T3) — pinned model IDs, per-model compatibility record | Fast open-weight escalation before OpenRouter for iterative agent/repair loops (pilot-reconciled §2); automatic prompt caching on the Kimi/GPT-OSS families |
| Hosted-open aggregation | **OpenRouter** (T4) — config, not code; hard open-weight allowlist, provider routing by price/throughput/latency, optional ZDR | The survey confirms provider-restriction + fallback controls are native; do NOT use an unrestricted auto-router that could select proprietary models |
| Hosted-open direct backup | **Together — DORMANT slot** (deferred per CW02; re-enable on OpenRouter-unavailability telemetry), **DeepInfra** optional | Removes OpenRouter as a single dependency; lets the bench compare aggregation vs direct on the same model. Both are just LiteLLM deployments |
| Proprietary ceiling | **Anthropic/OpenAI/Perplexity PAYG** behind LiteLLM budgets, boundary-gated | No fixed subscription rung; reached only on verified open failure / documented specialist / explicit override |
| Classifier backend | **Ollama 7B + keyword rules** — do NOT deploy vLLM Semantic Router | vLLM SR is deployment-grade (BERT models, dashboard, Envoy); overkill for one user, and the report confirms the clarify/override wrapper stays custom regardless |
| Plan schema | plan.json as drafted; **OpenSpec format optional** | Cheap to adopt early (it's just a schema + 28k-star tooling), required at Scale 3 — adopting now avoids a migration |
| Measurement | **measure.py + JSONL** — no Langfuse | A hosted/unit-priced trace store is infrastructure weight one user doesn't need; the JSONL already feeds the metric, now incl. `proprietary_displacement` + rescue efficiency |

This scale is complete with what's in the repo + LiteLLM. **Nothing new to
adopt** — OpenRouter, Together, and the PAYG providers are all LiteLLM config,
not new dependencies. The transition itself is Phase 6a in `REVISION-PLAN.md`.

---

## Scale 2 and Scale 3

Relocated to the EduCloud umbrella at CC-P0 v2 (CW02 §4):
`~/dev/educloud/docs/specs/portage-scale-2-3.md`. The scale-invariance rule
above still holds across all three scales; only the ladder and backend
adoption differ, which is exactly why that content now lives with the
umbrella's other Scale-2/3 planning material rather than in the engine.

---

## Standing re-evaluation triggers (from the report's time-sensitive flags)

1. vLLM Semantic Router ships clarify-before-dispatch or deterministic
   pre-model overrides → shrink or retire the custom triage wrapper.
2. DOE↔NSF Globus federation opens FIRST-class services to ACCESS users →
   retire most of the JS2 adapter.
3. Any quota router adds a sovereign/institutional tier → the fusion novelty
   erodes; differentiation falls back to the guard + measurement method.
   Recheck quarterly; the publication window is now.
