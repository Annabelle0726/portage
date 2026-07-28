# 03 — Claude-only 5x efficiency pilot

> **STATUS: HISTORICAL — pilot complete, retained as analysis.** The Claude-only
> efficiency pilot is done and the fixed Claude Max / Codex Plus subscription
> rungs are exiting the production ladder (`specs/10`–`11`, `REVISION-PLAN.md`);
> the project moved to the open-first platform (PLATFORM.md). Nothing here is a
> current routing instruction. The quota mechanics — three parallel caps, one
> shared wallet, why cheaper models barely help a weekly cap — are **preserved
> for the Parity Bench cost accounting** (PLATFORM.md §5.4) and the amortized /
> quota-share pricing of the subscription baseline arms.

Make the subscription you're paying for efficient before adding any paid meter.
No OpenRouter, no local, no Jetstream, **no router** — this version is native
Claude only. Prove out automatic model+effort escalation and quota-aware limits
here first.

## The limit structure this is designed around (mid-2026)

Three caps run in parallel; hitting **any** of them blocks new prompts even if
the others have headroom. All of it is **one wallet** shared across Claude chat,
Claude Code, and Cowork.

1. **5-hour rolling window** — resets 5 hours after your first message.
2. **Weekly all-models cap** — 7-day rolling window.
3. **Weekly Opus cap — separate and tighter.** Max 5x users routinely run out of
   Opus while still holding Sonnet headroom.

Read live values with `/usage` (or `/status`) in Claude Code; the numbers get
revised, so don't hardcode them.

## The insight that inverts the routing

On per-token billing, you start cheap (Haiku) and escalate. **On a subscription,
that's often wrong**, for two reasons rooted in the caps above:

- **The weekly all-models cap barely rewards cheaper models.** Switching Haiku↔
  Sonnet spends against the same bucket; the only way to extend a weekly window
  is *fewer messages, not cheaper ones*. So a Haiku attempt that fails and
  escalates spends **two** turns against the weekly cap where starting at Sonnet
  would spend **one**. The quota-optimal start tier is the one most likely to
  pass in a single shot, not the cheapest.
- **The Opus cap is the scarce one.** Every escalation to Opus draws the tightest
  budget you have.

**Therefore the two real levers are: (1) reserve Opus, and (2) reduce total
volume (turns + context).** Model micro-routing below Opus is a minor lever.

## The two efficiency moves, concretely

**A. Reserve Opus (protect the tight cap).**
- Default everything to Sonnet 5.
- The execution ladder is **Sonnet → Opus** (`tiers.claude.json`), starting at
  Sonnet. Haiku is reserved for genuinely trivial background/classification that
  reliably one-shots — it is *not* in the execution ladder, because a failed
  Haiku attempt just double-spends the weekly cap.
- Milestone-gate and plan decisions are hard-pinned to Opus and never
  downshifted — that's the one place Opus quota is worth spending outright.

**B. Reduce volume (protect the all-models cap + 5-hour window).**
- Lean CLAUDE.md; deliberate `/compact` and `/clear`; the snapshot/reload hooks
  so context isn't re-derived (re-derivation = extra turns).
- Plan-first for large tasks so you don't burn turns thrashing.
- Serialize with Herdr `wait` — parallel panes all draw the same wallet, so
  concurrency is the fastest way to hit a wall.

## Automatic model + effort selection

Effort is a second axis and a real lever: elevated/"ultrathink" effort can
multiply consumption ~5x, which eats the 5-hour window fast.

The fail-up guard now escalates over **(model, effort) pairs** together
(`tiers.claude.json` uses `{model, effort}` objects). The task gets exactly as
much model and effort as it needs to pass the deterministic check, and no more —
that *is* the automatic "best model + effort for the task":

```
Sonnet @ default  ──fail──▶  Opus @ high
        │pass                     │pass
        ▼                         ▼
      ship                      ship
```

- Default effort on Sonnet; effort rises only when the model rises to Opus.
- Never pair elevated effort with routine execution.

## Quota-aware guard (considering usage limits)

The guard takes a **budget-pressure ceiling** (`--max-tier`):

- Before a run (or on a schedule), check `/usage`. If the **Opus** weekly cap is
  low, invoke the guard with `--max-tier 0` (Sonnet only). If a task then can't
  pass on Sonnet, it **stops and flags a human** — it does *not* spend the last
  of your Opus quota automatically. Quota-vs-quality is surfaced, not hidden.
- With Opus headroom, run uncapped (`Sonnet → Opus`).
- Native Claude Code also auto-downshifts Opus→Sonnet past a usage threshold in
  Lane A; the ceiling is the Lane B equivalent you control.

## Where it runs

- **Lane A (interactive, the 5x pool):** native Claude Code. Efficiency here is
  defaults + discipline + subagent model pins + the auto-downshift — there's no
  headless auto-escalation on the interactive pool, and that's fine.
- **Lane B (automated escalation):** native `claude -p` via the guard
  (`failup.py --runner "claude -p" --tiers .claude/tiers.claude.json`). Since
  2026-06-15 this draws the **separate credit**, not the 5x interactive pool — so
  piloting escalation doesn't eat the quota you're trying to make efficient.

## Pilot protocol

1. **Baseline week:** normal use, no ceiling. Log `failup-log.jsonl` and snapshot
   `/usage` daily — track the **Opus cap** and the all-models cap separately.
2. **Treatment week:** Sonnet-default, guard with a ceiling tied to Opus-cap
   pressure, effort discipline, Herdr serialization.
3. **Compare:** did you hit walls less often, and did the Opus cap last the week,
   **without** a rise in tasks that stalled at the ceiling? If tasks stall a lot
   on Sonnet, your ceiling is too aggressive or the work is genuinely Opus-heavy —
   which is itself the signal for whether the 5x plan fits the workload.

Only once this is stable and measured do you add OpenRouter/local as *additional*
tiers below Sonnet — and by then you'll know from the log whether you even need
them.
