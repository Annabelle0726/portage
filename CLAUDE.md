# EduCloud ecosystem — shared conventions

This repo (`portage`) is the LLM routing engine of the EduCloud ecosystem, an
open-source GitHub Classroom replacement. Siblings: `cairn` (classroom/LMS),
`belay` (AI tutor), `outfitter` (compute broker), `waypoint`
(hosting/identity), `educloud` (umbrella strategy/decisions/SYSTEM.md).
`portage-local` is a separate personal deployment, currently on hold — not
part of this ecosystem's active work; prompts here are **EduCloud-scoped
only**, don't touch `portage-local`.

## The platform invariant

No component trusts a model's — or a provider's — self-report. A
deterministic check decides success, always. Before citing a vendor's claim
(pricing, precision/quantization, model catalog, uptime, API behavior) as
fact in a spec or a decision, verify it against the live API/service, not
the marketing page. This has mattered concretely more than once already —
Morph's serving-precision claim was this ladder's whole reason for existing
at T4, and replacing it (CC-P15) required re-verifying that same claim
against Jetstream2's Inference Service and AI Verde rather than assuming
parity.

## The CC-* prompt namespace — check before you number

Claude Code prompts across all six repos share one numbering namespace:
`CC-P*` (Portage — this repo), `CC-CA*` (Cairn), `CC-B*` (Belay), `CC-O*`
(Outfitter), `CC-W*` (Waypoint), `CC-HB*`/`CC-C*` (historical, closed
series). **A number means one thing platform-wide — collisions have
happened twice already** (CC-P9/P10 reused by accident — those numbers
belong to `portage-local`'s own history — and CC-C1 reused by accident).
Before creating a new prompt:

1. Read `../educloud/DOCUMENTATION.md`'s "Prompt-number namespace" section
   for the next free number in your series (find the actual path — it's a
   sibling directory, don't assume the relative path is exactly `../educloud`
   without checking).
2. Also check this repo's own `docs/prompts/` directory directly — the
   registry can drift; the directory listing is ground truth. Note `portage`
   deliberately skips P9-P10 (claimed by `portage-local`).
3. Use one higher than the max of both, then update the registry.

The `/new-cc-prompt` custom command in this repo does steps 1-3
automatically — prefer it over doing this by hand.

Prompt files live in `docs/prompts/CC-<series><n>-<slug>.md` and follow this
shape: a real title (not a placeholder); an italicized context block
(`*Claude Code prompt. Authored [where/when], from [what triggered this —
a finding, an instruction, a prior prompt's report]`) stating plainly what's
already known/verified and what this prompt needs to resolve; numbered
sections (what to read first, what to do, in dependency order); a closing
numbered **Report** section listing exactly what the executor must report
back — including anything that diverged from the happy path or couldn't be
verified. Never omit the Report section.

## Git conventions

- No `Co-Authored-By: Claude` trailers in this repo's commits. If unsure,
  `git log -5 | grep -c Co-Authored-By` should return `0`.
- Prefer new commits over amends; never force-push without being asked.

## Where things are

- `../educloud/SYSTEM.md` — the eleven shared platform contracts every
  module implements against
- `../educloud/DOCUMENTATION.md` — the full doc index and the CC-* namespace
  tracker
- `docs/specs/` — the numbered architecture specs (routing paradigm, scale
  tiers, local/hybrid/open-weight-only policy modes); `docs/PLATFORM.md` and
  `REVISION-PLAN.md` are the two documents most specs cross-reference
- `config/profiles/scale2.educloud.*` — the actual rendered EduCloud
  deployment config; specs describe the intended ladder, this is what's
  actually live — check both before assuming a spec change has shipped
- Parity Bench — benchmarks per endpoint, not per model name, before any
  endpoint earns production traffic; this gate already exists, invoke it
  rather than re-inventing verification for a new provider row
