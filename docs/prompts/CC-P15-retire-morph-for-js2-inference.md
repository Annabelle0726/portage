# CC-P15 — Retire Morph as T4; the Jetstream2 Inference Service takes its place

*Claude Code prompt. Authored in Cowork, 2026-08-09, from a direct instruction
from Greg: don't use Morph to serve EduCloud model traffic. Priority order,
his words: Jetstream2 inference first, self-hosted local mostly, an open
source alternative otherwise, and a proprietary service only as a fallback
that won't keep charging — never Morph specifically, regardless of category.

**Audit finding: Morph is not live yet, which is why this is cheap to fix
now.** `config/profiles/scale2.educloud.*` — the actually-rendered EduCloud
Scale-2 config — has **zero** references to Morph, and `MORPH_API_KEY` has
never been provisioned (absent from `KNOWN_GOOD_VERSIONS.md`, `CHANGELOG.md`).
Nothing needs to be torn down on a live deployment. But Morph **is** the
documented T4 (`remote_open_broad`) rung across the core architecture:
`docs/PLATFORM.md`, `docs/specs/02-local-and-educloud.md`,
`docs/specs/08-scale-tiers.md`, `docs/specs/10-local-platform-open-weight-only.md`,
`docs/specs/11-local-platform-hybrid-payg.md`, `REVISION-PLAN.md`, plus
`schema/registry.schema.json`'s `provider_route` enum, a real branch in
`render_config.py` (~line 201, `elif route == "morph"`), and fixtures in
`tests/test_render_config.py` (~lines 326, 329). Several TODOs point toward
reconciling the Scale-2 profile with this newer ladder shape — if that
happens before this prompt runs, Morph ships into a live deployment. Fix the
plan before that, not after.

**What replaces it: Jetstream2 already runs its own LLM Inference Service.**
This is distinct from the sovereign vLLM deployment the roster already uses
at `order: 1` (`SOVEREIGN_BASE_URL`/`SOVEREIGN_TOKEN`) — that's a dedicated
instance EduCloud provisions itself. The Inference Service is a
separate, shared, OpenAI-compatible endpoint IU/Jetstream2 runs for the whole
ACCESS community: free (no SU cost, an ACCESS account is the only gate),
currently hosting DeepSeek R1 (671B reasoning), Llama 4 Scout (vision), and
gpt-oss-120b. Two access paths exist — a public token-gated proxy
(`https://llm.jetstream-cloud.org/api/`) and an unauthenticated direct
vLLM/SGLang path per model (`.../sglang/v1/`, etc.) that only works from
inside Jetstream2/IU Research Cloud networks. [Sources: the Jetstream2 LLM
inference service announcement and update posts, and
`docs.jetstream-cloud.org/inference-service/overview/` and `/api/`.] This is
still Jetstream2, still free, still open-weight — the natural replacement,
not a new vendor relationship.

**One open question this prompt must resolve, not assume.** T4 was Morph
specifically because Morph documents bf16/no-quantization serving, which is
this platform's stated reproducibility bar for every benchmarked alias
(CW-04 §2.2, repeated in specs 08/10/11 — "an aggregator free to change
quantization under a stable model ID makes that cell irreproducible").
Nothing found so far says what precision the JS2 Inference Service serves
at. Don't port Morph's justification onto a new vendor by find-and-replace —
verify it, or say plainly that it isn't verifiable yet.

---

## 1. Verify the JS2 Inference Service empirically — this platform doesn't take a provider's word for anything

- Confirm which access path applies from wherever Portage's rendered config
  actually reaches it — the sovereign deployment may already run inside
  Jetstream2's network, in which case the unauthenticated direct path is
  simpler and doesn't need a token/secret at all; if not, use the token-gated
  proxy and note where that token is provisioned/stored.
- Confirm the **current** model catalog by hitting the service, not by
  trusting the docs snapshot above — "this service is evolving," per its own
  documentation.
- **Confirm serving precision** — bf16, some quantization, or undocumented.
  Check vLLM/SGLang launch flags if reachable, ask IU/Jetstream2 support if
  there's a channel for that, or state clearly that it could not be
  confirmed. This is the load-bearing fact for whether this rung keeps the
  platform's reproducibility guarantee or weakens it.
- Get a real throughput/latency number for whichever model ends up occupying
  the slot (the docs cite a 36-180 tok/s range depending on model/backend —
  that's not precise enough to plan around).
- Confirm rate limits, if any are enforced or documented, since "shared
  community resource with no SU cost" implies some kind of fair-use ceiling
  probably exists even if undocumented.

## 2. Replace the T4 occupant, doc by doc

Update `docs/PLATFORM.md`, `docs/specs/02`, `08`, `10`, `11`, and
`REVISION-PLAN.md` to name the JS2 Inference Service (and whichever specific
model clears step 1 — gpt-oss-120b and/or DeepSeek R1 are the likely
candidates given the roster's existing code/reasoning aliases) as the T4
`remote_open_broad` occupant, in place of Morph/MiniMax M3. Keep T3
(DeepSeek first-party) untouched — its justification (automatic prefix
caching economics) has nothing to do with this change. Where step 1 couldn't
confirm precision, write that honestly in the spec rather than asserting
parity with what Morph offered.

## 3. Re-examine the T5 dormant reserve now that this exists

T5's trigger-(a) occupant is Groq's gpt-oss-120b, justified as "a
latency-sensitive alias no local rung can serve." If the JS2 Inference
Service already serves gpt-oss-120b for free at acceptable latency (step 1's
numbers), that trigger may be redundant — Groq would no longer be the only
place to get it. **Don't retire it on assumption.** Decide with the real
latency numbers from step 1, and write down what they were and why the
decision went the way it did.

## 4. Schema and code

- `schema/registry.schema.json`: update the `provider_route` enum and its
  description (~lines 36-39, ~118) — drop `morph` from anything describing
  EduCloud's actual ladder. Check first whether the JS2 Inference Service
  even needs a new `provider_route` value: it's OpenAI-compatible, and the
  sovereign rows already use the plain `openai` shape (`api_base` +
  `api_key`) for a first-party-style endpoint that isn't literally
  api.openai.com. If JS2 Inference fits that same shape, prefer reusing it
  over inventing a new schema concept — distinguish rows by
  `data_classification`/`order`/endpoint, not by a new provider_route.
- `render_config.py`: remove or repoint the `elif route == "morph"` branch
  (~line 201) accordingly.
- `tier_pricing.py` and `tests/test_render_config.py`: update the Morph
  fixtures (~lines 326, 329) to match whatever the new T4 row actually is.

## 5. Budgets

The `$5/30d` Morph budget line (specs/11's pricing table) either disappears
entirely (if the JS2 Inference Service genuinely costs nothing, confirmed in
step 1) or gets replaced with whatever cap makes sense for a free
community-shared service — likely none needed today, but note this
platform's existing budget-guard pattern in case JS2 meters it later.

## 6. Leave `portage-local` alone

That repo has its own Morph rows (CC-P9, GLM-5.2/Qwen in-slot) in a personal
deployment Greg put on hold earlier this session. This prompt is EduCloud-scoped
— don't touch `portage-local`.

## 7. If JS2 Inference doesn't fully pan out — named fallback candidates, screened for billing behavior

Greg's objection to Morph is specific: **its account defaults to automatically
reloading paid API usage credits** (auto-recharge) rather than stopping and
asking. That's the axis to screen every fallback candidate against — not just
price or catalog. Two real candidates, researched here so this isn't a blind
name-drop:

- **Fireworks AI** — prepaid credits; its "Auto Reload" feature is
  **opt-in, off by default** (`docs.fireworks.ai/faq/billing-pricing-usage/billing/billing-management`).
  Notably, Fireworks also exposes per-model precision as a **queryable API
  fact** (`firectl model get`, `docs.fireworks.ai/models/quantization`) rather
  than a static marketing claim — that's arguably a *stronger* fit for this
  platform's "verify, don't trust self-report" rule than Morph's own bf16
  claim ever was, since it can be checked per request instead of taken on
  faith. No pre-built table exists across their catalog, so whichever model
  is considered needs its precision queried individually before it earns a
  registry row.
- **Together AI** — already the T5 trigger-(b) reserve occupant, and its
  billing turns out to match what Greg wants without any change needed:
  fully prepaid, credits never expire, and auto-recharge is **opt-in, off by
  default** — if the threshold trips with no auto-recharge configured, API
  access simply suspends rather than silently billing further
  (`docs.together.ai/docs/billing-credits`). Nothing to fix here; worth
  stating plainly so it isn't second-guessed later.
- **Groq — a genuine mismatch worth flagging, not assuming away.** Groq (the
  existing T5 trigger-(a) occupant) has no prepaid-credit gate at all: it
  bills automatically at spend thresholds ($1/$10/$100/$500/$1,000) and then
  monthly once past $1,000 lifetime — payment is withdrawn automatically at
  each milestone, with no "balance hit zero, now what" moment
  (`console.groq.com/docs/billing-faqs`). That's structurally closer to what
  Greg dislikes about Morph than either of the other two candidates is, even
  though Groq's dormant/trigger-only role means it rarely bills at all in
  practice. Groq does offer a **Spend Limits** feature (automated caps +
  proactive alerts) — configuring one explicitly should be a condition of
  Groq staying in the roster at all, not an optional nice-to-have.

**Turn this into a standing rule, not a one-off finding.** The registry
already requires `price_source`/`price_confirmed_date` before a price field
can be non-null (HB-2b). Apply the same discipline to billing safety: no
paid third-party `provider_route` should go live without confirming (a) any
auto-recharge/auto-reload toggle is off, or (b) where the provider's billing
model has no such toggle (Groq's shape), an explicit spend cap is configured
instead — both recorded with a date, the same way price confirmation already
is. Decide during this prompt's execution whether that belongs as a new
schema field or an operator checklist in `docs/deploy.md`-equivalent
documentation; either is fine, but the requirement itself should end up
written down somewhere a future row can't skip.

This section does not change Morph's status — Morph stays excluded
regardless of what these alternatives' billing looks like. This is about
what backs up JS2 Inference if step 1 finds a real gap (precision
unconfirmable, model unavailable, capacity), and about tightening the
existing T5 reserve rows while this prompt is already touching this part of
the roster.

## 8. Report

- What step 1's verification actually found: access path used, real model
  catalog, precision (confirmed, or explicitly not confirmable), real
  latency/throughput numbers.
- Every doc/schema/code file changed and how.
- The T5/Groq redundancy decision from §3, and the evidence behind it.
- Test suite green (`pytest` or whatever the repo's actual command is).
- Anything that needed a real GPU/model call this environment couldn't make,
  flagged explicitly rather than silently assumed to be fine.
