# CC-P8 — Record the Fable-tier exclusion requirement for `proprietary_displacement`, don't build the metric

*Claude Code prompt. Authored in Cowork, 2026-08-05. While reviewing CC-P7's
build report, its own §"Ambiguities" flagged an inference: `proprietary_displacement`
"now has to measure removal of T6 and the Fable tier, since Kimi K3 is
non_permissive and fails `open_weight_only` too — otherwise K3 rescues would
score as open-ladder wins." Checked directly before acting on it: `proprietary_displacement`
does not exist in any `.py` file in this repo — it is referenced in nine
markdown documents and implemented nowhere. `measure.py`'s `summarize()`
reads only `failup-log.jsonl`, produced by `failup.py` walking `.claude/tiers.json`'s
ladder (rungs named `local-small`, `local-big`, `sovereign-work`, `sonnet`,
`opus`). Kimi K3 lives only in `registry.yaml`, a structurally separate
system `failup.py` never opens (the schema's own `fable_tier` description
already says so). So a K3 call cannot appear in `measure.py`'s output today —
there is no live bug to fix. The concern is real but future-facing: it only
becomes live if someone later builds a measurement path over direct
registry-alias LiteLLM traffic. This prompt records that requirement where an
implementer will find it, and builds nothing else. Do not implement
`proprietary_displacement` here — there is no traffic to measure it against
yet, and building it now would be speculative code against a system that has
produced zero real runs (no `failup-log.jsonl` exists anywhere on disk, per
the CC-P6 report).*

---

## 1. Add the requirement to `measure.py`

Add a note near the top of `measure.py` — either in the module docstring or
as a comment directly above `summarize()`, whichever reads more naturally
without disrupting the existing docstring's flow. Content, not verbatim
wording:

- `measure.py` currently measures only the `.claude/tiers.json`-driven ladder
  (`failup-log.jsonl`). It has no visibility into `registry.yaml`'s
  alias-based LiteLLM deployments, including the Kimi K3 Fable tier
  (`fable_tier: true`, `registry.schema.json`).
- If `proprietary_displacement` (or any future metric over registry-alias
  traffic) is ever implemented, it must exclude any row where
  `fable_tier: true` **and** any row whose `license_family` is not in the
  `open_weight_only` allowlist from counting as an "open-ladder win."
  Otherwise a Kimi K3 rescue — reachable in principle through LiteLLM's own
  retry/fallback even while `enabled: false` (see the CC-P6 report §1's
  "honest limit of a declarative gate") — would misreport as an open-weight
  success.
- Source: CW-04 §2.5 (`portage-local/docs/reports/CW04-model-roster.md`),
  and the ambiguity note in `portage-local/docs/reports/P7-report.md`.

## 2. Cross-reference from the schema

`schema/registry.schema.json`'s `fable_tier` field description already states
it is invisible to `failup.py`. Add one sentence to either `fable_tier`'s or
`license_family`'s description noting that any future consumer computing an
"open-ladder win" or displacement-style metric over this registry must treat
`fable_tier: true` rows, and rows whose `license_family` fails the
`open_weight_only` allowlist, as excluded — pointing to `measure.py`'s new
comment (§1) so the two notes don't drift apart. One sentence, not a
restatement of the whole field's existing description.

## 3. Report

A short append to `portage-local/docs/reports/` (`P8-report.md`), covering:
what was checked to establish there is no live bug (the `.py` grep result,
the `failup.py`/`registry.yaml` separation, the absence of `failup-log.jsonl`),
exactly what was added and where, and a one-line statement that no
functional code was written — this is a requirement recorded for a future
implementer, not a metric implementation.

State explicitly in the report that this is a deliberate stopgap, not a
final decision to skip the metric: the full `proprietary_displacement`
implementation is deferred to a future Claude Code prompt, to be scoped once
there is real registry-alias LiteLLM traffic to measure against (i.e., after
HB-0's Gates 2–4 run and a live proxy actually produces logs). This prompt's
job is only to make sure that future build can't miss the Fable-tier/
`license_family` exclusion — not to declare the metric out of scope
permanently.

---

## What this prompt does not do

- Does not implement `proprietary_displacement`, `win_tier_distribution`
  changes, or any new measurement logic. There is no traffic to validate it
  against, and building it now is exactly the kind of speculative code this
  repo's own conventions (see `KNOWN_GOOD_VERSIONS.md`'s stated purpose) warn
  against.
- Does not touch `registry.yaml`, `failup.py`, or any test file.
- Does not change `fable_tier`'s or `license_family`'s `type`, `enum`, or
  required-ness — description text only.

## Acceptance

- `measure.py` carries a clear, accurate note recording the exclusion
  requirement, placed where a future implementer extending it to
  registry-alias traffic would actually see it
- one of `fable_tier` or `license_family` in `registry.schema.json` carries a
  one-sentence cross-reference to that requirement
- no new functions, no new metric fields, no test changes
- `git diff` outside `measure.py`, `schema/registry.schema.json`, and the new
  report file is empty
- one commit

## Model and effort

`sonnet` at `medium`. This is locating the right two files and writing two
short, accurate notes — the investigation that determines *what* to write is
already done above; the agent's job is placement and precise wording, not
new judgment calls.

Launch at `~/dev/portage`.
