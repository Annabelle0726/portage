# CC-P7 — Rewrite the six ladder documents CW-04 and CC-P6 left stale

*Claude Code prompt. Authored in Cowork, 2026-08-05. `CW04-HB0-drift.md` §6
found that the pointer banners placed in these six files on 2026-08-04 were
the only mitigation for a rewrite that had never happened — five of seven
documents still draw OpenRouter as a routable T4 rung. CC-P6 (2026-08-05) then
rendered `registry.yaml` against the real ladder, which raises the cost of
leaving these six stale: the registry now actively disagrees with the docs in
code, not just in a memo. This prompt closes that gap. It is a transcription
job, like CC-C5 and CC-P6 before it — every occupant, tier, and caveat below is
already decided; nothing here is a new design call except where §3 says so
explicitly.*

---

## 0. Read before touching anything

- `portage-local/docs/reports/CW04-model-roster.md` — the decisions (§2.1–2.7
  especially), and §7's amendment index
- `portage-local/docs/reports/CW04-HB0-drift.md` §6 — why the banners exist,
  and its explicit note that the stale content "invalidates the tier diagrams
  in `docs/specs/10` and `11` as drawn"
- `portage-local/docs/reports/P6-report.md` — what CC-P6 shipped **beyond**
  CW-04, all of which the docs also need to reflect:
  - `proprietary_code` (Anthropic/Claude) is **deleted from the registry
    outright**, not capped. CW-04 §2.3/§2.7 still names "Claude Opus 5,
    capped" as the T6 occupant — that is superseded. Where the registry and
    CW-04 disagree, **the registry is ground truth**; treat CC-P6 as the
    amendment of record on this point, the same way CW-04 amended CW-02.
  - The Kimi K3 **Fable tier** — a confirm-gated, alias-level flag
    (`fable_tier: true` + `enabled: false`), not a routine escalation rung and
    not a T-number. §1 below says how to draw it.
  - `license_family` — `open_weight_only` now tests this field, not
    `open_weight: true/false` alone. Anywhere a doc implies published weights
    imply an acceptable license, that's now wrong.
  - The "Flash Max" rung — DeepSeek V4 Flash re-run at `effort: max`, a second
    rung on the same checkpoint, sitting between the primary hosted occupant
    and the Fable tier.
  - `failover_only` exists as a schema field for OpenRouter's demotion, but
    **no row uses it yet** — the mechanism that would make a row actually
    non-routable is HB-2 work. Describe this as a real gap, not a solved one.
- The live `registry.yaml` itself — read it directly rather than trusting any
  memo's transcription of it, including this prompt's.

---

## 1. The tier table every diagram and table must converge on

```
T1  local              classifier: Gemma 4 E4B (iMac, warm, keep-alive -1)
                        code_small: Gemma 4 12B Q4 (MacBook, primary) + Gemma 4
                        E4B (fallback)
T2  local_large         DORMANT — future 128GB node, enabled: auto. Unchanged.
T3  remote_open_direct  DeepSeek, first-party (api.deepseek.com). V4 Flash is
                        the cheap first attempt (MIT, license_family:
                        permissive); V4 Pro is the primary occupant (license
                        unverified). Direct because DeepSeek's automatic
                        prefix caching is the reason this rung isn't
                        aggregated.
T4  remote_open_broad   Morph (bf16, no quantization, one key). MiniMax M3 is
                        the primary occupant; GLM-5.2 and Qwen sit in-slot
                        without a new account if ever needed. A second
                        DeepSeek V4 Flash rung at `effort: max` ("Flash Max" —
                        same checkpoint, not a separate model) sits after this
                        occupant, before the Fable tier.
T5  remote_open_reserve DORMANT. Renamed from `remote_open_direct` (CW-02's
                        name; CW-04 reassigns that name to T3 above — don't
                        let the two `remote_open_direct`s collide in prose).
                        Absorbs Together. Two independent re-enable triggers:
                        (a) a latency-sensitive alias no local rung can serve
                        → Groq GPT-OSS 120B, benched as its own capability
                        cell, never a route to an existing roster model;
                        (b) sustained Morph unavailability → Together.
T6  proprietary         ONE occupant: GPT-5.6 Sol (`proprietary_research`),
                        disabled by default, reached only through CW-02 §3's
                        T6 mechanism — which P6-report §1 found is a policy
                        sentence plus `enabled: false`, not code; there is no
                        confirm-prompt or logged-reason mechanism to point to.
                        Claude/Anthropic (`proprietary_code`) is GONE — not
                        present, not capped, not gated. Six aliases are
                        declared by the deployment now, not seven.

OpenRouter — OFF THE LADDER. Not a rung at any T-number. A non-routable
failover path, reachable only when a first-party endpoint health-checks down,
tagged `unbenched`. The schema has a `failover_only` field for this but no row
sets it yet (see §0) — say so plainly, don't describe the failover path as if
it already routes.

FABLE TIER (Kimi K3) — NOT a T-number, sits outside the ordinary escalation
chain entirely. Every diagram that draws T1→T6 as a chain must show this
visibly apart from that chain (a dashed branch, a footnote, a separate box —
whatever fits the existing diagram style), never as if it were rung 7.
Reachable only by an explicit human declaration that a specific task warrants
it, logged — never by ordinary stall/failure escalation.
```

---

## 2. Per-file scope

### `docs/PLATFORM.md` (§2–3, roughly lines 74–114)

Rewrite the ladder diagram and the policy-mode-vs-tier-range table against §1
above. The escalation-policy sentence needs the Fable-tier caveat added
explicitly (it is not part of "open-to-open first"). Check lines ~282 and
~294 — they mention "OpenRouter (allowlisted) + Together as LiteLLM deployment
groups" and "wire T7"; read the surrounding context and update or flag rather
than assuming what T7 still means once T6 has one occupant and Fable sits
outside the numbering.

Remove the banner (current lines 4–10) once this section is accurate. Replace
it with a short provenance line — "ladder rewritten 2026-08-05 per CW-04 and
CC-P6; decision record in `portage-local/docs/reports/`" — not a staleness
warning, since it won't be stale anymore.

### `REVISION-PLAN.md`

- §3's ladder diagram (roughly lines 134–155): same rewrite as PLATFORM.md.
- §4 is **already marked historical** ("§4's file-by-file rows below predate
  this revision... read those rows as history") — **do not touch it.** It's a
  record of what CW-03 already executed, not a live spec.
- §5, "Phase 6a" (roughly lines 172–196): this describes *future* work to wire
  OpenRouter and Together deployment groups. CC-P6 already rendered a
  registry with DeepSeek/Morph/Moonshot groups instead — Phase 6a as written
  describes work that both didn't happen as planned and doesn't need to
  happen anymore. Don't silently delete it or renumber phases. Add a note
  that Phase 6a executed differently than specified here, pointing to
  `CC-P6-registry-rewrite-and-fable-tier.md` and `P6-report.md` as the actual
  execution record, and list what P6-report §4 still flags as open (HB-0
  Gates 2–4, console budget caps, native model-ID confirmation) as the real
  remaining Phase 6a work. This is a judgment call on annotation, not a
  mechanical replace — say what you decided and why in the report.

### `docs/specs/02-local-and-educloud.md`

- Lines ~14–15, 36–37, 64: the Line-P local ladder diagram and prose — rewrite
  against §1.
- Lines ~70–100 (the EduCloud/"B. EduCloud version" section): this ladder uses
  named tiers (`sovereign`, `remote_open`, `proprietary_payg`), not T-numbers,
  and per `CW04-HB0-drift.md` §3 the Scale-2 profile's occupants are
  **explicitly out of scope** for this pass (institutional placeholder IDs,
  unaffected by CW-04). Leave the `sovereign` tier and its Jetstream2 framing
  untouched. Do update what "`remote_open`" means when this doc discusses it
  generically (e.g. line ~127's "`remote_open` is defense-in-depth for
  *ordinary* work only") — that generic reference should reflect the T3/T4
  split now underneath it, not imply a single undifferentiated rung.

### `docs/specs/08-scale-tiers.md`

- The Scale 1 section (roughly lines 31–65): full rewrite of the ladder line
  and the "Hosted-open fast / aggregation / direct backup" table rows against
  §1. The "Nothing new to adopt" sentence still holds (DeepSeek/Morph/Moonshot
  are LiteLLM config, same as OpenRouter/Together were) — keep that framing,
  just with the new names.
- The Scale 2/3 section is **already relocated** to the EduCloud umbrella
  ("Relocated... only the ladder and backend adoption differ, which is
  exactly why that content now lives with the umbrella's other Scale-2/3
  planning material") — confirm the pointer path is still correct, don't add
  content back here.
- Remove the banner (current lines 3–10) once done, same replacement pattern
  as PLATFORM.md.

### `docs/specs/10-local-platform-open-weight-only.md` and `docs/specs/11-local-platform-hybrid-payg.md`

The two large, technically dense specs — full per-tier prose sections
(`### 4. remote_open`, `### 5. remote_open_direct`, etc.), embedded YAML
deployment examples, and their own copies of the ladder diagram. This is the
highest-volume and highest-risk part of the job:

- Every section named for a superseded tier/provider (the `remote_open`
  section describing OpenRouter, the `remote_open_direct` section describing
  Together) needs its prose body rewritten for the actual occupant now there,
  per §1 — not just the heading relabeled.
- Every embedded YAML deployment block referencing `openrouter:` or `groq:`
  (specs/10 roughly lines 217–243 and ~484–488; specs/11 roughly lines
  186–223, 367–374, and 541–551) needs rewriting to show `deepseek:`,
  `morph:`, and `moonshot:` provider blocks matching what CC-P6 actually
  rendered. Pull the real shape from the live `registry.yaml` and
  `render_config.py`'s output — don't invent a schema shape from memory.
- The ASCII ladder diagrams in both files (roughly lines 16–79) get the same
  occupant rewrite as the smaller files' diagrams; preserve the existing
  drawing style, just relabel.
- **These two land in their own commit**, separate from the four documents
  above — they're different enough in size and technical depth that mixing
  them into one review is a disservice to whoever reads the diff.

### `CLAUDE.md`

Just the banner (current lines 4–8). Update it **last**, after the five
documents above are verified accurate, to the same short provenance-pointer
style — its claim needs to be true when it lands, not aspirational.

---

## 3. What this prompt does not do

- Does not relitigate CW-04's or CC-P6's decisions — this is transcription of
  already-decided content into prose, the same instruction CC-C5 and CC-P6
  operated under.
- Does not touch `REVISION-PLAN.md` §4 — already a historical record, leave
  it exactly as is.
- Does not change Scale-2/EduCloud's institutional occupant content in
  `docs/specs/02` — out of scope per the drift memo, confirmed above.
- Does not build the `failover_only` mechanism, the OpenRouter health-check
  call path, or any confirm-gate machinery for the Fable tier. All three are
  HB-2 work. Describe the current state accurately (schema field exists,
  unused; gate is policy plus a flag, not code) rather than describing an
  aspirational future as already built.
- Does not touch `registry.yaml`, any schema, or any source code. Docs only.

---

## 4. Report

Append to `portage-local/docs/reports/`, matching where `P6-report.md` and
`CW04-HB0-drift.md` live — this is a decision-record closure, not engine code,
even though the files it touches are in `portage`. Cover:

1. Every section changed per file, with a before/after summary — not a full
   diff dump, but enough that a reviewer can spot-check without reopening
   every file
2. How the PLATFORM.md T7 reference (§2 above) and the specs/02 generic
   `remote_open` reference were resolved
3. What was decided for REVISION-PLAN.md §5's Phase 6a annotation, and why
4. Confirmation `CLAUDE.md`'s banner was updated last
5. Anything the specs/10/11 rewrite surfaced that needs a further
   reconciliation pass (e.g., if the real rendered YAML shape doesn't fit
   cleanly into the existing prose structure)

---

## Acceptance

- No file describes Groq, OpenRouter, or Together as a routable or live rung,
  anywhere in prose, table, or diagram — OpenRouter appears only as the
  tagged, non-routable failover CW-04 §2.2 defines, and only where the schema
  affordance is described as unused
- Every named occupant (DeepSeek V4 Flash/Pro, MiniMax M3 via Morph, GPT-5.6
  Sol) matches the live `registry.yaml` exactly, including that
  `proprietary_code` (Anthropic) is absent, not capped
- The Kimi K3 Fable tier appears in every document that draws the escalation
  ladder, visibly separated from the T1–T6 chain, never silently omitted and
  never drawn as an ordinary rung
- `license_family` vs. `open_weight` is stated correctly everywhere
  `open_weight_only` is discussed
- `REVISION-PLAN.md` §4 is byte-for-byte untouched
- `docs/specs/10` and `docs/specs/11` land in their own commit, separate from
  `PLATFORM.md` / `REVISION-PLAN.md` / `specs/02` / `specs/08`
- `CLAUDE.md`'s banner no longer says the rewrite hasn't been performed, and
  is the last file touched
- no change to `registry.yaml`, any schema file, or any source code

## Model and effort

`opus` at `high`. Every individual fact is already decided and sourced (CW-04,
`CW04-HB0-drift.md`, `P6-report.md`, the live registry) — this is not a design
task. What makes it `high` rather than `medium` is volume and reconciliation
risk: six documents, two of them (`specs/10`, `specs/11`) several hundred
lines of dense technical prose and embedded YAML apiece, three separate
source decisions to merge without contradiction (CW-02's original tier
semantics, CW-04's amendment, CC-P6's further divergence on Anthropic and the
Fable tier), and several places (PLATFORM.md's T7 mention, specs/02's generic
`remote_open` reference) where a tier-number reference needs active
verification rather than a mechanical find-and-replace.

Launch at `~/dev/portage`.
