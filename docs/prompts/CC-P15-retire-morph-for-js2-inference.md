# CC-P15 — Retire Morph as T4; Jetstream2 and AI Verde take its place

*Claude Code prompt. Authored in Cowork, 2026-08-09, from a direct instruction
from Greg: don't use Morph to serve EduCloud model traffic. Priority order,
his words: Jetstream2 inference first, self-hosted local mostly, an open
source alternative otherwise, and a proprietary service only as a fallback
that won't keep charging — never Morph specifically, regardless of category.
**Updated same day**, Greg added a second named institutional option ahead of
any commercial fallback: **AI Verde** (University of Arizona's Data Science
Institute, arXiv:2502.09651) — "I'd rather use this than a different platform
besides JS2 anyway." Keep JS2 in mind for now alongside an ACCESS allocation;
AI Verde sits alongside it, not behind it. He also asked explicitly:
**whatever Portage was gaining from Morph needs to survive this change** —
this isn't just a find-and-replace, see §9.

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
Nothing found so far says what precision either the JS2 Inference Service or
AI Verde (§2 below) serves at. Don't port Morph's justification onto a new
vendor by find-and-replace — verify it, or say plainly that it isn't
verifiable yet.

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

**Exact endpoints, confirmed this session** (`docs.jetstream-cloud.org/inference-service/api-examples/`):

| Model | Base URL |
|---|---|
| `llama-4-scout` | `https://llm.jetstream-cloud.org/llama-4-scout/v1` |
| DeepSeek R1 | `https://llm.jetstream-cloud.org/sglang/v1` |
| `gpt-oss-120b` | `http://llm.jetstream-cloud.org/gpt-oss-120b/v1/` |

Append `/models` to any of these to pull the **live** catalog for that
backend rather than trusting this table — the docs themselves say this is
the way to check what's actually current, which is exactly the "verify,
don't trust the doc" move this platform already requires everywhere else.

## 2. Verify AI Verde — Greg's own institution's platform, possibly reachable today with his NetID

AI Verde is a real, operating platform, not a research prototype only: the
University of Arizona's Data Science Institute has run it since a May 2024
pilot (paper: arXiv:2502.09651, "AI-VERDE: A Gateway for Egalitarian Access to
Large Language Model-Based Resources For Educational Institutions"). Verified
this session:

- **Stack**: Kubernetes orchestration, vLLM for open-model serving, **LiteLLM
  as the reverse proxy** exposing an OpenAI-compatible API — the same proxy
  layer Portage's own `render_config.py` targets. Wiring this in is very
  likely the same `openai`-shaped row the sovereign deployments already use
  (api_base + api_key), not a new provider_route — same conclusion §5 reaches
  for JS2 Inference, for the same reason.
- **Access**: CILogon federated login with university credentials, individual
  API keys, and — notably — **faculty manage class-specific user groups with
  per-course budgets and student access lists.** That's close to prior art
  for exactly the instructor/student budget-isolation pattern
  `scale2.educloud.staff` vs `.student` already implements. Worth reading the
  paper section on this before assuming EduCloud's own design has nothing to
  learn from it.
- **Access gate, confirmed just now, and it matters:** "Currently, AI Verde is
  available only to the University of Arizona community and a U of A NetID is
  required" (`datascience.arizona.edu/research/tools/ai-verde`,
  `cyverse.org/ai-verde`). Given the course codes already in this repo
  (INFO-523-S26, INFO-526-SU26) are University of Arizona courses, Greg likely
  already has a NetID and may be able to get direct access. **This is Greg's
  action, not something this prompt can do.**
- **Named contacts, per Greg, both confirmed:** **Tyson Swetnam** and
  **Wolfgang Jentner**. Jentner: University of Arizona Research &
  Partnerships (LinkedIn). Swetnam: primary appointments at the University
  of Arizona (BIO5 Institute, School of Natural Resources and the
  Environment) **plus an affiliated-faculty appointment in UNM's Department
  of Computer Science** (`cs.unm.edu/directory/faculty-profiles/tyson-swetnam.html`,
  corroborated via UNM CS's own affiliated-faculty directory) — this is the
  real UArizona/UNM bridge Greg described, resolved: not two separate
  AI Verde deployments, but a person with a foot in both institutions. The
  public AI Verde pages still say a UArizona NetID is required for direct
  platform access, so this doesn't necessarily mean UNM users get their own
  login — but Swetnam is exactly the right person to ask about that,
  including whether UNM affiliation itself is a path in. The current page's
  listed contact is `mithunpaul@arizona.edu` — worth checking whether that's
  still the right first email, or whether Jentner/Swetnam are the better
  route now.
- **AI Verde supports bringing your own API key, per Greg** — for external
  providers, from any account, not just AI Verde-managed ones. Flagging a
  real tension with what's publicly documented: the arXiv paper describes
  the opposite — a **surrogate-key system**, where the institution holds
  master keys for commercial providers (OpenAI, Anthropic) and issues
  scoped surrogate keys to users/courses for budget control, not BYOK.
  Both can be true at once (surrogate keys as the default managed path, BYOK
  as an option added since the Feb 2026 paper — the model catalog has
  already moved since then per the point above, so a feature addition
  wouldn't be surprising). Confirm which is actually live when talking to
  Swetnam/Jentner, and if BYOK is real, it's independently useful for this
  platform's own registry pattern: it would mean routing through AI Verde
  doesn't require putting a *new* institutional key in Portage's own budget
  tracking for the proprietary rows already provisioned (OpenAI/Anthropic/
  Perplexity) — those existing keys could potentially route through AI
  Verde's proxy layer instead of direct, if there's ever a reason to.
- **Model catalog**: the paper (Feb 2026) lists Llama 3.2, Mistral, Phi-3 as
  open models served, plus commercial proxying (OpenAI, Anthropic, AnvilGPT)
  via the same LiteLLM layer; the current site lists LLaMA4, Gemma, and Phi-4
  instead — **the catalog has clearly moved since the paper**, so query it
  live rather than trusting either snapshot.
- **Hardware partners, confirmed**: the paper names CyVerse and **NSF's
  Jetstream2** explicitly as AI Verde's cost-effective hardware partners —
  meaning this may already be partly JS2-backed infrastructure, reinforcing
  rather than competing with keeping JS2 in mind.
- **Not verified, and flagged rather than assumed:** precision/quantization is
  undocumented on every source checked, same open question as JS2 Inference.
  Same rule applies — confirm per model before it earns a registry row, or
  say plainly it couldn't be confirmed.
**Scope note for the ladder itself**: AI Verde's UArizona-only platform gate
(confirmed above, independent of Swetnam's cross-appointment) means it
can't be assumed as a universal default the way JS2 Inference (gated only by
a free ACCESS account, not a specific institution) can — EduCloud is meant to
be reusable by other institutions per its own stated mission. Treat AI Verde
the way the sovereign rows already are: an institution-specific option Greg's
own deployment can use, layered alongside the general ladder, not a
replacement for what a non-UArizona EduCloud operator would fall back to.

## 3. Replace the T4 occupant, doc by doc

Update `docs/PLATFORM.md`, `docs/specs/02`, `08`, `10`, `11`, and
`REVISION-PLAN.md` to name whichever of JS2 Inference / AI Verde clears
verification (both are worth carrying if both check out — they're
complementary institutional options, not competitors) as the T4
`remote_open_broad` occupant, in place of Morph/MiniMax M3. Keep T3
(DeepSeek first-party) untouched — its justification (automatic prefix
caching economics) has nothing to do with this change. Where verification
couldn't confirm precision, write that honestly in the spec rather than
asserting parity with what Morph offered.

## 4. Re-examine the T5 dormant reserve now that this exists

T5's trigger-(a) occupant is Groq's gpt-oss-120b, justified as "a
latency-sensitive alias no local rung can serve." If JS2 Inference or AI
Verde already serves an equivalent model for free at acceptable latency,
that trigger may be redundant — Groq would no longer be the only place to
get it. **Don't retire it on assumption.** Decide with real latency numbers,
and write down what they were and why the decision went the way it did.

## 5. Schema and code

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

## 6. Budgets

The `$5/30d` Morph budget line (specs/11's pricing table) either disappears
entirely (if the occupant genuinely costs nothing, confirmed above) or gets
replaced with whatever cap makes sense for a free community/institutional
service — likely none needed today, but note this platform's existing
budget-guard pattern in case either service meters usage later.

## 7. Leave `portage-local` alone

That repo has its own Morph rows (CC-P9, GLM-5.2/Qwen in-slot) in a personal
deployment Greg put on hold earlier this session. This prompt is EduCloud-scoped
— don't touch `portage-local`.

## 8. If neither institutional option fully pans out — named fallback candidates, screened for billing behavior

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
what backs up JS2/AI Verde if verification finds a real gap (precision
unconfirmable, model unavailable, capacity), and about tightening the
existing T5 reserve rows while this prompt is already touching this part of
the roster.

## 9. What Portage was actually gaining from Morph — keep the substance, not the vendor

Greg was explicit: this is not a find-and-replace. Three distinct things Morph
was providing, assessed one at a time so nothing gets silently dropped:

- **Precision transparency as a reproducibility guarantee.** This is the one
  that matters most and it's already handled: §1 and §2 both require
  confirming serving precision on the replacement(s) before they inherit
  Morph's old justification. Don't consider this section done until that's
  actually resolved one way or the other for whichever occupant lands.
- **The specific model family (MiniMax M3 primary; GLM-5.2, Qwen available
  in-slot on the same key, no new account).** This one does **not** carry
  over automatically — JS2 Inference's catalog (DeepSeek R1, Llama 4 Scout,
  gpt-oss-120b) and AI Verde's (Llama/Mistral/Phi per the paper; Llama4/Gemma/
  Phi-4 per the current site) contain neither MiniMax M3 nor GLM-5.2 nor
  Qwen. Don't paper over this: if nothing in the current roster actually
  depends on MiniMax M3 specifically (check whether any alias's benchmark
  results are pinned to it, or whether it was chosen simply because it was
  *available* on Morph's key), losing access to that exact model family is
  an acceptable trade for what's gained. If something does depend on it,
  the sovereignty-consistent way to get it back is self-hosting the
  checkpoint (locally, or on more Jetstream2 GPU allocation), not a new
  commercial aggregator relationship.
- **One key, low administrative friction, models available without a new
  account or inclusion review.** JS2 Inference and AI Verde both replicate
  this in spirit — one endpoint, no per-model account — for whatever they
  actually host. Note plainly in the spec that adding a model neither
  service hosts still means a fresh inclusion review, same as it always did
  for anything outside whatever key is already provisioned.
- **Existing platform discipline already covers the rest.** `REVISION-PLAN.md`
  states "Parity Bench still benchmarks per endpoint, not per model name,
  before an endpoint earns production traffic" — that gate already applies
  here without this prompt needing to invent anything new. Run it against
  whichever occupant(s) land before they carry real traffic, exactly as any
  other new endpoint would require.

Report which of these three actually transferred cleanly, which didn't, and
why — this is the section Greg will check first.

## 10. Report

- What verification actually found for JS2 Inference and AI Verde: access
  path(s) used, real model catalogs, precision (confirmed, or explicitly not
  confirmable, for each), real latency/throughput numbers.
- Whether Greg's UNM claim about AI Verde was ever resolved (asked him
  directly, found a source, or left genuinely open).
- Every doc/schema/code file changed and how.
- The T5/Groq redundancy decision from §4, and the evidence behind it.
- The §9 accounting — precision, model family, admin friction, Parity Bench —
  point by point.
- Test suite green (`pytest` or whatever the repo's actual command is).
- Anything that needed a real GPU/model call this environment couldn't make,
  flagged explicitly rather than silently assumed to be fine.
