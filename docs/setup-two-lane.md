# Two-lane Claude Code build (Max-quota aware, local floor, verified escalation)

> **STATUS: HISTORICAL (2026-07).** This is the original Max-era two-lane
> setup. The Max premise and claude-code-router are both retired — CCR was
> deleted in Phase 2 (docs/phase-1-findings.md) and the staging plan of record
> is LINE-P-ROADMAP.md (S0–S5). Retained for the hooks design and the
> reasoning record; the diagrams below show the retired CCR wiring.

Efficient, high-quality runs that leverage Claude while preventing self-inflicted
rate-limit problems — and escalating flawlessly to Opus for hard tasks. The whole
design turns on one fact: **on Max, cheaper models save quota, not dollars, and
every interactive session draws one shared pool (rolling 5h + two weekly caps).**
So spend that pool only on work that needs it, keep automation off it entirely,
and make escalation *verified* rather than *hoped*.

## What the build actually is

Three moving parts. Everything else is native behavior or config.

```
laneA (interactive, Max)          laneB (automated, off-pool)         local floor
──────────────────────────        ────────────────────────────       ─────────────
native Claude Code                claude-code-router (ccr code)       warm model on
Sonnet 5 default                    background -> local  (free)       the iMac, served
/model opus for judgment            default    -> Sonnet             over Tailscale to
+ pre_compact / session_start       think/long -> Opus                MBP + Jetstream2
  hooks (zero-quota context)      + fail-up guard (verified escalate) 1 resident model
```

```
repo/
├── .claude/
│   ├── settings.json            # wires the two Lane A hooks
│   ├── hooks/
│   │   ├── pre_compact_snapshot.py    # backup + state file before compact
│   │   └── session_start_reload.py    # re-inject state on resume/compact
│   └── state/                   # snapshots + failup-log.jsonl (created at runtime)
├── .claude-code-router/
│   ├── config.json             # Lane B on your machines (background -> local)
│   └── config.ci.json          # Lane B in CI (no local host -> background = cheap)
├── .github/workflows/
│   └── taskcapture-ci.yml       # deterministic test gate -> CCR-routed review
├── src/portage/
│   ├── failup.py                # the verified-escalation guard
│   └── local-serve.sh           # warm the shared local model on the iMac
├── herdr/
│   └── lanes.sh                 # bounded, serialized session orchestration
└── README.md
```

### Request flow

- **Lane A (you, hands on keyboard):** native Claude Code on Max. Sonnet 5 by
  default; `/model opus` for judgment. No router — a proxy here only costs you.
  The hooks snapshot context before a compact and re-inject it on resume, so you
  never re-derive the repo (re-derivation = re-sent context = wasted pool).

- **Lane B (automation / CI / scheduled):** everything runs through `ccr code`,
  which since 2026-06-15 draws the **separate non-interactive credit** (then API
  rates) — not your interactive pool. CCR routes by request class:
  `background -> local` (free, private, the constant summarize/compact traffic),
  `default -> Sonnet`, `think`/`longContext -> Opus`.

### Escalation flow (why hard tasks never fumble)

Three mechanisms, cheapest first — "flawless" comes from the guard, not a smart
classifier:

1. **Hard pins.** Milestone gates and the automated review are pinned to Opus and
   never downshifted. No inference; can't be misrouted.
2. **Predictive routing.** Free heuristics + the free local classifier send the
   obvious cases to the right tier. Allowed to be imperfect.
3. **Fail-up guard (`src/portage/failup.py`).** After a T0/T1 run, a deterministic
   check — non-empty diff + `ruff` clean + `pytest` green — and on failure it
   parks the attempt, resets clean, and retries **one tier up**, to Opus. A
   misclassified hard task fails the check and self-corrects. Every attempt is
   logged to `failup-log.jsonl` (tier, result, seconds) — which is also the seed
   of the measurement layer.

## The local floor

`background` and the classifier point at a local model — free, private, off every
meter. Run `src/portage/local-serve.sh` on the iMac to keep ONE model warm and serve
it to the MacBook and Jetstream2 over Tailscale. Local widens the floor, not the
ceiling: T2 judgment still goes to Opus. Local is also your **privacy tier** — if
a routing step touches clinical data, it stays off third-party APIs entirely.

Caveat: keep weights on the internal SSD. The drive only affects cold-load time,
but eviction from an external drive becomes a stall — `OLLAMA_KEEP_ALIVE=-1`
avoids eviction. And a single local server suits *serialized* background, not
fan-out, so it pairs with the bounded-concurrency discipline below.

## Where Herdr fits

Herdr is tmux-for-agents: real PTYs that survive the laptop closing, semantic
blocked/working/done state, SSH/phone attach, a `wait agent-status` primitive,
and it surfaces the Max 5h/Week bars per pane.

It's an **orchestration/observability layer, not a throughput multiplier** —
every interactive pane draws the same shared pool. Used well it's the behavioral
guardrail:
- **Bound + serialize** interactive work with `wait agent-status` instead of
  firing five panes at once (the behavior that blows the pool).
- **Run Lane B on the always-on iMac / Jetstream2** (off-pool); close the lid,
  nothing dies; reattach from the phone only when a pane goes `blocked`.
- **Watch the 5h/Week bars** — quota stops being an invisible wall.

### The one caution

Running Herdr across multiple Max accounts / round-robin token rotation to
multiply throughput is against Anthropic's terms — that's the account-flagging
behavioral risk, distinct from ordinary rate limits. Bound and sequence within
one account's fair use; push automation onto the separate credit / API.

## To make it run

- Repo secrets for CI: `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`.
- Confirm the test command (`uv run pytest -q` assumed for taskcapture).
- Point the `local` provider `api_base_url` at your iMac's Tailscale name.
- Match the one `ccr code --model` line in `failup.py` to your CCR version's
  model-pinning interface.

## Deliberately left out

Runtime prompt engineer, multi-model fan-out arbiter, from-scratch router, and a
sophisticated difficulty classifier. The fail-up guard is what lets you drop that
last one without losing the best-model-for-the-task guarantee. The novel,
publishable part is the thin measurement layer (quota drawn per unit of work,
baseline vs. treatment) — added after you have a baseline.
