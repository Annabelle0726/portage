# 13 — Routing paradigm: why verify-then-escalate, and what the field does instead

*2026-08-08. Written after a landscape scan triggered by Morph's Router
(`docs.morphllm.com/sdk/components/router`) and the question of whether the
EduCloud profile should adopt something like it. It should not — but the scan
surfaced three concrete corrections to this ladder, recorded in §4. Full scan
with sources: `routing-gateway-brokering-landscape-2026-08-08.md` (Cowork
project).*

**Status:** positioning + design record. Amends nothing in `02`, `10`, or `11`;
adds the three items in §4 as work for the EduCloud profile and the engine.

---

## 1. The two paradigms

Every system that picks a model per request falls into one of two shapes.

**Classification-first.** Inspect the prompt, predict which model can handle it,
dispatch once. The prediction is never checked against the result. Morph's
Router is the reference commercial instance (three classifier heads — difficulty,
ambiguity, domain — each with a confidence threshold, mapped to a model pick
under a weighted policy). Nearly the entire open-source field is this shape.

**Verify-then-escalate (cascade).** Run the cheapest tier, check the output
against something that can actually fail, escalate only on verified failure.
This is Portage's fail-up guard: non-empty diff + `ruff` + `pytest`, with the
five-class taxonomy separating `unavailable` (skip, not a model failure) from
`not_good_enough` (real escalation trigger).

The distinction is not a tuning preference. Per `portage-scale-mapping.md` §2,
the verifier invariant — *no module trusts a model's, or a provider's,
self-report* — is the platform's stated thesis, shared with Cairn's sandboxed
autograder and Belay's leak gate. A classify-once-and-commit router is that
invariant inverted: it bets correctness on a classifier guessing right, which is
precisely the bet the fail-up guard exists not to make.

## 2. What the field actually has

**Classification-first, maintained:** vLLM Semantic Router (Apache-2.0, active
under the vLLM org — the most production-credible OSS router today), LLMRouter
(MIT, UIUC — a library of 16 predictors, useful as a benchmark baseline),
Arch-Router (gateway Apache-2.0 but the router *model* ships under a bespoke
non-OSI licence — disqualifying here). RouteLLM (Apache-2.0) is the historical
reference and is stale: last release 2024-07-08.

**Cascade / verify-then-escalate:** research code only.
- **FrugalGPT** (Apache-2.0, TMLR 2024) — genuinely cascade-shaped, but the gate
  is a *learned confidence scorer*, not a deterministic check.
- **eth-sri/cascade-routing** (Apache-2.0, ICML 2025, arXiv 2410.10347) — proves
  routing and cascading are special cases of one optimal strategy and that
  unified cascade routing dominates both. **This is the formal citation for why
  this ladder is the right shape**; cite it rather than asserting the design.
- **"Cluster, Route, Escalate"** (arXiv 2606.27457, 2026) — the closest published
  analogue to the fail-up guard; no code released.

**LiteLLM's own routing** (the substrate this runs on) has no
capability-, quality-, or verification-based routing. `lowest_cost` means
*cheapest deployment of a model group already chosen*, not *cheapest model
capable of this task*. LiteLLM supplies transport, fallbacks, cooldowns, and
spend; the escalation policy and the verifier are ours.

**Conclusion:** the OSS field is saturated with classification-first routers and
has no maintained verify-then-escalate system. The nearest artifacts gate on
learned confidence. **Deterministic verification as the escalation trigger is
uncontested, and has ICML-published theoretical backing.** That is a positioning
fact for the grant narratives, not just an implementation detail.

## 3. Why not adopt Morph's Router

Three reasons, in order of weight:

1. **Paradigm** (§1). It replaces the verifier with a guess.
2. **Sovereignty.** It is hosted-only — no OSS component, no documented
   self-hosting path, classifier architecture and training data undisclosed.
   EduCloud's standing rule is no proprietary models; whether that extends to
   proprietary *routing infrastructure* has never been decided explicitly. It
   should be. A hosted classifier on the critical path is arguably a larger
   sovereignty problem than a proprietary model in a disabled rescue tier,
   because every request touches it.
3. **Evidence.** The published claims ("40–70% cost reduction," "under 2%
   quality loss," "85–95% classifier accuracy") come with no eval harness, no
   dataset, no named baseline, and no accuracy-vs-oracle number. The stated
   accuracy band is about trained domain classifiers *in general*, not measured
   on their router. Docs and marketing pages also disagree on both price
   ($0.005 vs $0.001 per call) and latency (~180ms vs ~430ms). Not a basis for
   a platform dependency.

## 4. Three corrections this scan produced

These are real, and they are the reason this document exists.

### 4.1 Escalation is not free — account for the discarded prefix

Morph's strongest technical point, and a genuine critique of any cascade:
**a model switch is a full re-prefill.** Their own numbers: cached input
$0.22/M vs $1.10/M uncached — an ~80% discount forfeited on every switch. A
verify-then-escalate ladder switches models mid-task *by design*, so it pays
this on every escalation, and today's cost accounting does not model it.

**Work:** `tier_pricing`'s cost capture should treat an escalation as
discarding the cached prefix, so the recorded cost of a two-rung task reflects
re-prefill rather than assuming cache continuity. This makes the ladder's real
cost visible instead of flattering it — which matters most for exactly the
comparison the paired baseline exists to make.

Their derived guidance is also worth respecting where it doesn't conflict with
the verifier: prefer few rungs over many; treat session/task boundaries and
context compaction as the free switch points; keep timestamps and UUIDs out of
system prompts, since they void every downstream cache hit.

### 4.2 Classification decides *where to start*; verification still decides *whether it worked*

The useful half of the classification-first idea, without its bet. The T1
classifier tier (Gemma 4 E4B) already exists and already does rough triage. Let
it choose the ladder's **entry rung** rather than always starting at the bottom,
so a task predictably beyond the local tier doesn't have to fail there first.
The verifier remains the sole authority on whether a result is acceptable and
whether to escalate — classification never overrides it, and a
classification-chosen entry that fails verification escalates exactly as it
would have otherwise.

Build this open. vLLM Semantic Router and LLMRouter are the reference
implementations to study; neither is a dependency to adopt uncritically, and
neither replaces the guard.

**Constraint:** this must not silently become classification-first by letting
the classifier skip rungs *and* suppress escalation. If entry-rung selection
ever correlates with reduced verification, that's a regression, not an
optimisation.

### 4.3 Residency must survive failover

OpenRouter is the only mainstream router exposing residency as a real API:
`provider.zdr: true`, `data_collection: "deny"`, `only`/`order` allowlists, an
in-region plane — and critically **`allow_fallbacks: false`**. That last flag is
the whole idea: *a residency guarantee that a fallback can silently violate is
not a guarantee.* Copy the parameter shape.

This deployment's rule — enforced by config absence, never runtime checks
(`docs/policy/data-destinations.md`) — is the stronger form of the same
principle, because a rung that isn't in the loaded config cannot be reached by
any code path, including a fallback. §4.3's work is therefore mostly
confirmation rather than construction: **prove that no failover, cooldown, or
`failover_only` path can route a `sovereign`-mode request to an endpoint absent
from that mode's config**, and add a test that fails if one ever can. The
`failover_only` field exists in the schema with no row setting it
(`CW04-HB0-drift.md`); that test should land before it does.

## 5. What this does not change

The ladder's shape, the five-class taxonomy, the verifier contract, the metric
names, and the policy-mode vocabulary are unchanged — those are the platform
contracts that must survive every scale step (`portage-scale-mapping.md` §1).
Nothing here is a new rung, a new provider, or a new dependency.
