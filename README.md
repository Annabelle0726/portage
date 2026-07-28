# Portage — meter- and sovereignty-aware agent control plane

*(the EduCloud inference plane; prior working name "Commons" — see the
umbrella's `SYSTEM.md` §1 for the name register)*

A self-hostable control plane for coding, research, design, and multi-agent
work. Open-weight by default, escalating to metered models only when a
**deterministic verifier** says the cheaper tier failed — and measured honestly
against the products it aims to replace.

## Read in this order

| | |
|---|---|
| **`PLATFORM.md`** | The capstone: final architecture, the three modes, lane verifiers, and the **Parity Bench** comparison suite. Start here. |
| **`REVISION-PLAN.md`** | The Scale-1 transition work order (2026-07): open-first ladder with a PAYG ceiling, file-by-file edits, pilot sequence, EduCloud deployment plan. Read after PLATFORM. |
| **`LINE-P-ROADMAP.md`** | The staging plan of record: S0–S5, hardware backbone, the 60–90 day calibration window. Where it differs from older plans, it wins. |
| **`HANDOFF.md`** | Build instructions: buy-vs-build resolution, phases 0–10 (+6a), acceptance criteria, standing rules. |
| `PROJECT.md` | Mission and the novelty claim (what is actually new vs. the ecosystem). |
| **`KICKOFF-PROMPT.md`** | The prompt to paste into Claude Code for a session, and how to scope it. |
| `EDUCLOUD-BRIEF.md` | Positioning brief for EduCloud stakeholders: decentralized AI as public infrastructure, and why education specifically needs it. |
| `specs/00`–`09` | The reasoning record. Each spec explains *why*, not just what. |
| `specs/10`, `specs/11` | Scale-1 target architectures: **10** = open-weight-only (end state), **11** = hybrid open-first + PAYG ceiling (current mode). Normative inputs to the revision plan. |

## The five ideas

1. **Meters, not models.** The scarce resource is a budget the router must
   respect — a PAYG dollar ceiling, an institutional allocation, or the
   open-only-displacement headroom — not per-token dollars in the abstract.
   Route free-before-metered, sovereign-before-scarce, proprietary-last.
2. **The verifier decides, never the model.** A runner (tests + lint +
   non-empty diff, or lane-specific checks) determines success; failures
   escalate one tier and retry. This is what makes cheap tiers safe to default
   to. An unreachable tier is *skipped as unavailable*, never scored as a failure.
3. **Triage before routing.** A free local model catches underspecified tasks
   *before* they waste an expensive turn — the largest real source of waste.
4. **Sensitive data is pinned by absence.** Regulated work runs against a
   config whose model list contains only local deployments. Not a runtime check,
   and not a provider's retention promise.
5. **No efficiency claim without a quality gate.** Cost/speed wins are void if
   verified-success rate drops. Enforced in code, not in prose.

## Operating mode

Current mode is **`hybrid`** (specs/11): local open → sovereign → hosted open →
Anthropic/OpenAI/Perplexity **PAYG only after verified open failure**. Fixed
Claude Max / Codex Plus subscription rungs are leaving the production ladder
(they remain only as Parity Bench baseline arms). The end state is
**`open_weight_only`** (specs/10); the switch is a config-variant swap, triggered
empirically by the `proprietary_displacement` metric, not by calendar. See
`REVISION-PLAN.md`.

## Layout

```
PLATFORM.md REVISION-PLAN.md HANDOFF.md PROJECT.md   read in that order
litellm.config.yaml                  the routing spine (tiered model groups)
litellm.sensitive.yaml               sovereign mode: local-only by construction
specs/                               00-11, the reasoning record
scripts/
  failup.py      deterministic fail-up guard  (core contribution)
  plan.py        plan-first decomposer, runnable per-subtask checks
  measure.py     report | downscale - quality-gated efficiency metrics
  distill.py     turn verifier logs into training data (self-labeling)
  scheduler.py   off-hours queue drain
  local-serve.sh keep one local model warm, shared over Tailscale
herdr-meters/                        Herdr plugin: cross-vendor meter routing
  meters.py      board / picker / dispatch / mark / research / loguse
  classify.py    triage -> classify -> route (deterministic rules first)
  adapt.py       target-conditioned prompt templates (emits template_id)
  prompts/       the templates themselves
  models.json    the routing target catalog + open-weight allowlist manifest
.claude/                             native Claude Code: hooks, agents, skills,
                                     tier ladders, source registry
herdr/lanes.sh                       one pane per meter
.github/workflows/                   deterministic gate + automated review
docs/setup-two-lane.md               the original personal two-lane setup guide
```

## Quick start (Scale 1 — personal)

```sh
uv sync
ollama serve && ollama pull qwen2.5-coder:7b && ollama pull qwen2.5-coder:32b
litellm --config litellm.config.yaml --port 4000
herdr plugin link ./herdr-meters && herdr plugin action invoke meters.hybrid.board
```

Then read `HANDOFF.md` Phase 0 and start there. The Scale-1 transition (add
hosted-open + PAYG ceiling, cancel subscriptions) is Phase 6a in
`REVISION-PLAN.md`; Scale 2 (add sovereign HPC) and Scale 3 (federated,
published) are in `specs/08`.

## Status

Phases 0 and 1 are done: `uv run ruff check .` and `uv run pytest` are green,
versions are pinned in `KNOWN_GOOD_VERSIONS.md`, and the LiteLLM spine has been
started and smoke-tested (round-trip, ordered failover, sensitive-config pin).

**Claude Code talks to LiteLLM directly — claude-code-router is not needed.**
See `docs/phase-1-findings.md`, which also lists the four defects execution
found in the drafted code and the substitutions the smoke test had to make.

**Next up: Phase 6a** (the Scale-1 transition — hosted-open allowlist + PAYG
ceiling as LiteLLM config, `unavailable`/`failed` split, displacement telemetry,
bench baseline, then cancel subscriptions). It is config + telemetry, not new
architecture. See `REVISION-PLAN.md` §5.

Still unverified: the Codex CLI (not installed), the Herdr plugin API, and
whether a small local model can actually *drive* an agentic loop as opposed to
merely being reachable. Treat the rest of the drafted code as a well-reasoned
starting point, not as working software.
