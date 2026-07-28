# 09 — The local model: roles, prompt adaptation, and specialization

One small local model does every cheap, private, always-on job in the platform.
This spec defines **all** of its jobs explicitly, adds the final component
(target-conditioned prompt adaptation), and sets the path from prompted roles to
a specialized model — without pre-training anything.

## 1. Why one model, many roles

The local tier is free, private, offline-capable, and already resident. Every job
that is high-frequency, low-stakes, or privacy-bound belongs here. Using one base
model with **per-role system prompts** (later: per-role LoRA adapters) keeps a
single set of weights in memory instead of N models competing for it.

## 2. The role charter (explicit)

| # | Role | Input → Output | Deterministic layer that runs first |
|---|---|---|---|
| R1 | **Triage** | task → {specified? missing[], one clarifying question} | vagueness/length heuristics |
| R2 | **Routing** | task → {provider, model, effort, confidence} | sensitive pins, `@overrides`, research phrasing, **open-weight license/allowlist check** (a non-allowlisted model is never a candidate) |
| R3 | **Prompt adaptation** (new, §3) | (task, target, lane) → adapted prompt | template selection by exact key |
| R4 | **Background/throwaway** | compaction, summaries, renames, extraction, commit messages | n/a |
| R5 | **Sensitive-lane execution** | all work in sovereign/clinical workspaces | config absence — no other tier exists |
| R6 | **Plan critique** (advisory) | plan.json → flags: subtasks lacking *runnable* checks, suspect seams | schema validation |
| R7 | **Verifier drafting** (advisory, human-approved) | subtask goal → candidate acceptance command | never auto-accepted; a human vets every check |

R6/R7 are advisory only. A model must never author *and* approve its own
acceptance criteria — that would collapse the verifier independence the whole
platform rests on.

## 3. Prompt adaptation (the last component)

**Where it sits:** after routing, before dispatch. Once the target is decided
(model family + framework + lane), the prompt is adapted to *that* target's
known conventions.

**What it is:** template selection + slot filling. **What it is not:** free-form
rewriting. The distinction is the whole safety argument — a small model
reinterpreting your intent is worse than no adaptation. So:

- Templates live in `plugins/herdr-meters/prompts/`, keyed
  `{lane}.{model_class}.md` (e.g. `code.open.md`, `code.remote-open.md`,
  `code.frontier.md`, `science.any.md`). Selection is a **deterministic dict
  lookup**, no inference. `remote-open` (hosted open-weight) gets more explicit
  scaffolding than local-open, less than frontier.
- Slots are filled from structured facts already known: task text, repo
  conventions (from CLAUDE.md/AGENTS.md), the subtask's acceptance command,
  files named, tier constraints.
- The local model is used only for **bounded extraction** — pulling file paths
  or symbols out of the task to fill slots. It never rephrases the goal.
- Frontier targets get *less* scaffolding (they handle ambiguity); open-weight
  targets get *more* (explicit paths, output-format constraints, no-prose
  instructions, worked examples). That asymmetry is the entire point of
  adapting per target.

**Why this is defensible when runtime prompt-rewriting wasn't:** it's
deterministic selection rather than generation, it's free (local), and — most
importantly — **it's measurable.** Every dispatch logs `template_id`, so
verified success rate can be attributed per template. Prompt engineering stops
being taste and becomes an A/B test against the verifier.

**Optimization path:** once a template has enough paired outcomes, optimize it
offline with DSPy/GEPA-style search against verified-success-rate, then ship the
winner as a static template. Offline optimization, static deployment — never a
model rewriting prompts at runtime.

## 4. Specialization path (no pre-training)

Three stages, each shippable, each earning the next:

**Stage A — Prompted roles (now).** One base model (Qwen2.5-Coder-7B class),
one system prompt per role, strict JSON output contracts. Zero training. This is
what's already built for R1–R2 and what §3 adds for R3.

**Stage B — Collect (automatic).** The platform labels its own data:

| Role | Label source | Ground truth |
|---|---|---|
| R2 routing | fail-up guard log | the **cheapest tier that passed** is the correct route, by construction |
| R1 triage | clarify events + one-shot rate | tasks that needed clarification vs. those that one-shot |
| R3 adaptation | `template_id` × verified outcome | which template wins per (lane, target) |

No hand-labeling. `src/portage/distill.py` turns these logs into SFT/preference
datasets.

**Stage C — Specialize (when the log earns it).** At roughly a few hundred
verified outcomes per role, train **per-role LoRA adapters** on the same base
model and hot-swap them (Ollama adapters / vLLM multi-LoRA). Adapters are small,
so all roles still share one resident base model. Gate every adapter behind the
platform's non-inferiority rule: a new adapter ships only if it beats the
prompted baseline on a held-out split **without** raising the ceiling-stall
rate. Versioned, reversible, measured — same discipline as router retraining.

## 5. Guardrails (non-negotiable)

1. Deterministic layers run first and win — pins, overrides, template keys.
2. Adaptation shapes; it never reinterprets. Uncertainty escalates upward.
3. The model may draft acceptance checks (R7) but never approve them.
4. Every role's output is logged with its input and the eventual verified
   outcome, or it can't be improved and shouldn't be trusted.
5. Sensitive workspaces: the local model is the *only* model, by config
   absence — and its adapters must be trained only on non-sensitive logs.

## 6. Honest limits

- A 7B model is a weak router on genuinely ambiguous tasks; the fail-up guard,
  not the classifier, remains the correctness mechanism. Specialization narrows
  the gap, it doesn't close it.
- LoRA on self-generated labels risks reinforcing the platform's own biases
  (it learns *your* ladder, not the optimal one). Keep a held-out human-judged
  slice as an anchor.
- Template proliferation is a real maintenance cost — cap the pack, prune by
  measured performance, and keep model-class buckets coarse (`open` /
  `frontier`), not per-model.
- Per-role adapters add serving complexity; if hot-swap latency hurts, keep
  prompted roles for low-frequency jobs and specialize only R1/R2/R3.

## 7. Training-record schema and evaluation gate

Written by joining the existing loggers on `run_id`; no new instrumentation.

```json
{
  "run_id": "…", "ts": "…",
  "task_original": "verbatim user text",
  "context": {"repo": "…", "lane": "code", "mode": "hybrid",
              "meter_state": {"claude": "available", "codex": "cooling"}},
  "decisions": {"triage": {"missing": [], "clarify": null},
                "class": "code", "target": "claude.default",
                "template_id": "code.frontier", "adapted": "…",
                "proposed_checks": ["uv run pytest tests/test_x.py -q"]},
  "outcome": {"verified": true, "win_tier": 1, "escalations": 0,
              "clarify_rounds": 0, "human_edit_distance": 12,
              "seconds": 41, "quota_drawn": {"opus_pct": 0.4}}
}
```

**Reward signal**, in priority order: verified pass (hard requirement) → resolved
at or below the predicted tier → no escalation needed → no clarification
round-trip a better triage would have caught → fewer human edits.

**Gate.** A specialized local model ships only if it beats the prompted+rules
baseline on a held-out task set on verified success rate, within the platform's
non-inferiority margin, with no rise in ceiling-stalls or clarification rounds.
Versioned, with instant rollback to the prior model or to pure rules.

**Feedback-loop collapse is the live risk.** Training on your own routing logs
teaches the model to predict what it already did. Mitigate with an exploration
fraction (route ~5–10% of tasks off-policy) so the log retains counterfactual
evidence, and always evaluate on held-out tasks. Related: the model optimizes
whatever the verifier measures — where a lane's verifier is weak (Design more
than Code), the training signal is weak too. Strengthen the verifier before
trusting the tune.

