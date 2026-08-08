# CC-P11 — Prove residency survives failover, before `failover_only` gets a row

*Claude Code prompt. Authored in Cowork, 2026-08-08, after a routing/gateway/
brokering landscape scan (`routing-gateway-brokering-landscape-2026-08-08.md`,
Cowork project) that produced `docs/specs/13-routing-paradigm.md` (still
untracked in this repo — commit it as part of this prompt's work, it is not
optional background reading). §4.3 there is the source of this task.

The finding: `schema/registry.schema.json` has carried a `failover_only`
field since CW-04 §2.2, wired through in `render_config.py:247`, referenced
in six spec documents (`08`, `10`, `11`, `13`, `REVISION-PLAN.md`,
`CC-P7-ladder-docs-rewrite.md`) — and **no row has ever set it, and nothing
asserts that a `sovereign`-mode request can't be failed over to an endpoint
absent from that mode's config.** `tests/test_scale2_profile.py` is close but
not this: it asserts the *student registry contains* no off-institution row.
It does not assert that LiteLLM's own retry/fallback/cooldown machinery
*cannot construct a path* from a sovereign alias to one, because today
there's nothing to construct a path *to* — the moment a `failover_only` row
is added to a shared alias, that changes, silently, unless a test exists
first. OpenRouter is the reference for why this matters:
`allow_fallbacks: false` is the whole idea, because a residency guarantee a
fallback can silently violate is not a guarantee.

**This prompt lands the test before the mechanism, on purpose** — per spec
13 §4.3: "prove residency survives failover... land it before any row sets
`failover_only`, which currently exists in the schema unused."*

---

## 1. Read first

- `docs/specs/13-routing-paradigm.md` §4.3 (the task, in the scan's own words)
- `schema/registry.schema.json`'s `failover_only` field description
- `src/portage/render_config.py` around line 247 (how the field renders today)
- `tests/test_scale2_profile.py` (the nearest existing test — read it to see
  what it does NOT cover, don't duplicate what it already asserts)
- `docs/specs/08-scale-tiers.md`, `10-local-platform-open-weight-only.md`,
  `11-local-platform-hybrid-payg.md` — each has a paragraph on why this path
  is deliberately unbuilt; skim for the reasoning, not for new instructions

## 2. Write the test first, confirm it can fail

Add `tests/test_failover_isolation.py`. The core assertion, stated precisely:
**for a `sovereign`-classification alias, no combination of `failover_only`
rows, LiteLLM `router_settings` (`allowed_fails`, `cooldown_time`), or
model-group fallback config can route a request to an endpoint whose
`provider_route` is off-institution** (`openrouter`, `anthropic`,
`perplexity` — same set `test_scale2_profile.py` uses).

Do this as a **construction test**, not a runtime/network test: build (or
reuse a fixture building) a registry where someone has — hypothetically —
added an off-institution `failover_only: true` row to a `sovereign`-tagged
alias, and assert that `render_config.py` refuses to render it (raises, or
drops the row with a loud warning — your call, but pick the one that matches
this repo's existing fail-closed posture elsewhere, e.g. `code_profile.py`'s
posture) rather than silently producing a working fallback path. This is
what "config absence is the enforcement" cashes out to as a machine check:
if the config *can't* express the violation, there's nothing for LiteLLM's
retry logic to find.

Before writing the fix, confirm the test actually fails against
`render_config.py` as it stands today (it should render the hypothetical row
today, since nothing stops it) — that failing-red state is the evidence this
task was real, not a test written to already pass.

## 3. Make it pass

Add the check to `render_config.py` (or wherever the schema validation
already lives — check for an existing validation pass before adding a new
one). The rule: a `failover_only: true` row is only ever legal on an alias
whose `data_classification` is `public` (mirrors
`test_off_institution_rows_are_public_only`'s existing logic in
`test_scale2_profile.py` — reuse that reasoning rather than inventing a
second rule that could drift from it).

Do not touch `config/profiles/scale2.educloud.*` — this profile still sets
no `failover_only` rows anywhere, and should stay that way. This task is
entirely: schema/renderer + test. Zero rows change.

## 4. Commit `docs/specs/13-routing-paradigm.md`

It is currently untracked (confirm with `git status --porcelain`). Commit it
in the same change as the test, or as an immediately preceding commit — your
call — but do not leave it stranded untracked once this prompt is done.

## 5. Report

- Confirm the red-then-green sequence: paste the failing assertion output
  before the fix, and the passing suite after.
- State plainly whether the fix lives in `render_config.py` or elsewhere, and
  why.
- `uv run ruff check .` and `uv run pytest -q` both green.
- Anything in spec 13 §4.3 you interpreted differently than written above —
  flag it rather than silently deciding.
