# Commons — quota- and sovereignty-aware agent control plane

*(working name; Apache-2.0 recommended)*

A self-hostable control plane for coding, research, design, and multi-agent
work. Open-weight by default, escalating to metered models only when a
**deterministic verifier** says the cheaper tier failed — and measured honestly
against the subscription products it aims to replace.

## Read in this order

| | |
|---|---|
| **`PLATFORM.md`** | The capstone: final architecture, the three modes, lane verifiers, and the **Parity Bench** comparison suite. Start here. |
| **`HANDOFF.md`** | Build instructions: buy-vs-build resolution, phases 0–10, acceptance criteria, standing rules. |
| `PROJECT.md` | Mission and the novelty claim (what is actually new vs. the ecosystem). |
| **`KICKOFF-PROMPT.md`** | The prompt to paste into Claude Code for session 1, and how to scope later sessions. |
| `EDUCLOUD-BRIEF.md` | Positioning brief for EduCloud stakeholders: decentralized AI as public infrastructure, and why education specifically needs it. |
| `specs/00`–`09` | The reasoning record. Each spec explains *why*, not just what. |

## The five ideas

1. **Meters, not models.** The scarce resource on a flat subscription is quota
   and institutional allocation — not per-token dollars. Route
   free-before-metered, scarce-last.
2. **The verifier decides, never the model.** A runner (tests + lint +
   non-empty diff, or lane-specific checks) determines success; failures
   escalate one tier and retry. This is what makes cheap tiers safe to default
   to.
3. **Triage before routing.** A free local model catches underspecified tasks
   *before* they waste an expensive turn — the largest real source of waste.
4. **Sensitive data is pinned by absence.** Regulated work runs against a
   config whose model list contains only local deployments. Not a runtime check.
5. **No efficiency claim without a quality gate.** Cost/speed wins are void if
   verified-success rate drops. Enforced in code, not in prose.

## Layout

```
PLATFORM.md HANDOFF.md PROJECT.md    read in that order
litellm.config.yaml                  the routing spine (tiered model groups)
litellm.sensitive.yaml               sovereign mode: local-only by construction
specs/                               00-09, the reasoning record
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
  models.json    the routing target catalog (single source of model names)
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

Then read `HANDOFF.md` Phase 0 and start there. Scale 2 (add sovereign HPC) and
Scale 3 (federated, published) are in `specs/08`.

## Status

Specified and drafted; **not yet run end-to-end.** Every external CLI
invocation (`claude -p`, `codex`, `ccr`, effort flags) is written against
documented behavior but unverified against installed versions — `HANDOFF.md`
Phase 2 treats that as the first real task, with token-free stub tests. Treat
drafted code as a well-reasoned starting point, not as working software.
