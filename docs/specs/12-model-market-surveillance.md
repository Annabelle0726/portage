# Spec 12 — Model market surveillance

*Should Portage watch the model market and swap in better price/performance
picks automatically? Answer: it should **discover** candidates automatically
and **promote** them only on its own evidence. This spec says why, and what to
build. Authored 2026-07-29 as input to HB-4/S4 and to CC-P2 Step 4.*

---

## 1. What exists today

Nothing. Stated plainly so this isn't rediscovered later:

- No code in `src/portage/` or `plugins/` reads a provider model list at
  runtime — verified 2026-07-29.
- No pricing data exists anywhere in the repository. `models.json` carries
  routing targets, not prices.
- `registry.yaml` pins are hand-authored and re-checked at bench time.
- The only market-facing machinery *specified* is CC-P2 Step 4's Renovate
  datasource, which watches for **renames of models already in use**. It does
  not discover candidates and does not compare prices. It is also not yet
  implemented, since CC-P2 has not run.

So the honest state is: Portage is deliberately pinned, and drift detection is
a manual watch item in `KNOWN_GOOD_VERSIONS.md`.

## 2. Why automatic promotion on published scores would be a defect

The instinct is right — prices fall, new models land, and a pinned registry
goes stale. But the obvious implementation would violate the platform's
founding rule, *no module trusts a model's or a provider's self-report*, and
the 2026 evidence says that rule is load-bearing rather than fastidious.

**Public benchmark scores do not survive contact with held-out data.**
SWE-Bench Pro built a matched private split specifically to measure this:

| Model | Public set | Held-out / private |
|---|---|---|
| Claude Opus 4.1 | 70%+ (SWE-bench Verified) | **22.7%** (SWE-Bench Pro) |
| GPT-5 (High) | 41.8% | **15.7%** (private commercial set) |

That last row is the same benchmark and the same model, differing only in
whether the problems were public — a ~62% relative drop.

**The measurement instrument itself failed.** OpenAI stopped evaluating on
SWE-bench Verified in February 2026, reporting that of 138 audited failures
**59.4% had flawed tests** rejecting functionally correct code, and that *all*
frontier models tested could reproduce the original human-written fix. They
compared it to handing students the exam and the answer key.

**Contamination inflation is 6–40%, and it is not uniform.** A July 2026
systematic review of 55 studies found no contamination-detection method is
consistently reliable. The inflation varies per model according to each lab's
training-data hygiene — which is unobservable from outside. **This is the
decisive point: it means the *ranking* is unreliable, not merely the absolute
scores.** A swap rule keyed to a published quality delta fires on hygiene
differences as readily as on capability differences.

**Preference leaderboards are gameable, and were gamed.** "The Leaderboard
Illusion" (NeurIPS 2025) documented Meta testing 27 private Llama-4 variants
and publishing only the best, with data asymmetry worth up to a 112% relative
gain on the Arena distribution. Automating against Arena rank delegates model
choice to whoever ran the most private variants.

**A cheap model that breaks tool calls is worthless at any price.** HB-0's
Gate 4 exists because of this, and `stream_tools: false` exists because one
real model passed non-streaming and failed streaming. No published score
predicts that; only running it does.

## 3. What is safe to automate

The distinction that resolves this: **prices and capability flags are facts;
quality ranks are claims.** Automate against the facts.

| Source | Gives | Auth | Verdict |
|---|---|---|---|
| OpenRouter `GET /api/v1/models` | Price (string USD/token), `context_length`, `top_provider.max_completion_tokens`, `supported_parameters` incl. `tools` / `tool_choice` / `structured_outputs`, modality | **none** | **Primary.** Rate limit undocumented — self-throttle, cache, back off on 429 |
| LiteLLM `model_prices_and_context_window.json` | Same, plus explicit booleans (`supports_function_calling`, `supports_response_schema`) and `deprecation_date` | none | **Cross-check** |
| OpenRouter Data API `/datasets/rankings-daily` | Real token volume — revealed preference | key | Nomination signal only; it measures popularity, confounded by price |
| Artificial Analysis Data API | Intelligence Index | key, 100/day free | **Ingest, never act on.** Vendor-controlled weights changed unilaterally; no published contamination controls |
| LMArena, SWE-bench Verified, HF leaderboards | — | — | **Do not automate against.** See §2 |

**Cross-check the two price feeds and alert on disagreement.** A >20% spread
between OpenRouter and LiteLLM means one is stale — which is exactly the
condition under which an automated swap does damage.

Note the practical finding on tool calls: the boring capability booleans
predict malformed-call rate better than BFCL scores do, because they reflect
whether the *provider* enforces constrained decoding. Use them as a hard gate
and BFCL as a soft prior.

## 4. The design

Four stages. Each is a thing the platform already does, applied to a new input.

**1. Scout — automatic, read-only.** On a schedule, pull OpenRouter and
LiteLLM. For each capability alias, emit candidates that beat the incumbent on
price *and* declare `tools` + `structured_outputs` *and* meet the alias's
context floor. Writes a report. **Never edits live config.**

**2. Gate — the same gate everything else passes.** A candidate is not
eligible until it passes HB-0 Gate 4 (per-model tool-call smoke test,
streaming and non-streaming) and a bench cut on the representative task set.
This is where per-model quirks surface, and it is not skippable.

**3. Promote — on our own evidence only.** The decision metric is
`measure.py`'s cost-per-verified-task on our own telemetry, never an external
score. This is HB-4's LinUCB bandit with its collapse guards, exploration
fraction and rolling windows — already the specified mechanism; the scout
merely widens the arm set it chooses among.

**4. Deliver as a pull request.** Against `registry.yaml`, the same shape
CC-P2 Step 4 gives Renovate. Rollback is the pin that already exists. The
quality gate from Line P's standing rules applies unchanged: *a cost win that
drops verified success reverts.*

External rankings' only role is **nomination** — narrowing what is worth
testing. They never promote.

## 5. Sequencing

**Not now.** Cairn owns the build clock through August 28, and this changes no
outcome before then.

- **HB-4 / S4** is the natural home for stages 3 and 4 — the bandit is already
  scoped there, and this spec only widens its arm set.
- **CC-P2 Step 4** should adopt stage 1 as an extension of its Renovate
  datasource: same delivery mechanism (a PR), broader trigger (a cheaper
  candidate, not only a rename).
- **One piece is worth pulling forward cheaply**, because it pays a debt that
  already exists: the scout's read-only half can fill registry fields that are
  currently blank. Four rows carry `license: UNVERIFIED`, and `max_context` on
  the Scale-2 rows is marked TODO. OpenRouter returns context and capability
  as facts, today, in one unauthenticated call. That is a small script with
  immediate value and no promotion logic attached.

## 6. On "the best resource to rank LLMs"

There isn't one, and that is a finding rather than a gap to fill. The best
available external index is a vendor's weighted blend of public benchmarks,
reweighted unilaterally, with no published contamination controls — and public
benchmarks carry a documented 6–40% inflation that varies unobservably by
model.

Portage already has the right instrument and it is called the **Parity Bench**:
a preregistered, held-out evaluation on the actual task distribution, with a
resource-tier factor. Given a public-versus-private gap of up to ~62%
relative, a held-out eval on your own workload is not a second-best substitute
for a leaderboard. It is the only trustworthy ranking that exists, and the
project was already building it.

The displacement metric is the same argument in a different direction: it
answers "can the open ladder do this work" empirically, rather than asking a
leaderboard whether it should be able to.

---

*Sources: OpenRouter models API and Data API docs; LiteLLM
`model_prices_and_context_window.json`; Artificial Analysis Data API and
Intelligence Index v4.1; SWE-Bench Pro (arXiv 2509.16941); OpenAI, "Why we no
longer evaluate SWE-bench Verified" (Feb 2026); "Are LLM Benchmarks Already
Contaminated?" (GEM 2026); "The Leaderboard Illusion" (arXiv 2504.20879);
BFCL V4 leaderboard and paper. Retrieved 2026-07-29.*
