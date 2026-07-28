# 06 — Unified interface for the personal hybrid

> **STATUS: partly superseded.** The standalone `src/portage/ai` dispatcher was removed in favour of the `herdr-meters` plugin, which does the same job inside the multiplexer. The access-constraint analysis (what is CLI-able vs app-only, and why Sonar API != Perplexity Pro) remains accurate and load-bearing.

One command (`src/portage/ai`) over four meters, plus a Herdr surface with one pane per
meter. This is the **pilot of the EduCloud full version**: same registry shape,
same free-before-metered policy, same reserve-the-scarce-tier rule — at personal
scale, where it's cheap to be wrong.

## What is actually CLI-able (the honest constraint)

The ideal — "CLI calls to each" — is achievable for three of four. The fourth is
not, and pretending otherwise would quietly break the economics.

| Source | Access | Reality |
|---|---|---|
| Claude Code | **CLI** | `claude` / `claude -p`, on your Max subscription |
| Codex | **CLI** | `codex`, included on ChatGPT Plus (web/CLI/IDE/iOS, shared 5h window) |
| Ollama (local) | **CLI** | `ollama run`, free and private |
| Perplexity Sonar | **API** | `api.perplexity.ai` — a *separate* metered product |
| Perplexity Pro | **app only** | Deep Research has **no CLI** |

**The trap this avoids:** Perplexity Pro's consumer tier and the Sonar API are
different meters. Pro includes $5/mo of Sonar credits that "apply against API
spend, not consumer-tier usage." Deep Research — the Opus-powered path, i.e.
Opus-grade reasoning that does *not* touch your Claude wallet — lives only on the
consumer tier. So a "Perplexity CLI" built on Sonar would silently move your best
free lever onto a paid meter. Hence two separate verbs:

- `ai search` → Sonar API. Scriptable, cited, **metered**. Keep it short.
- `ai research` → launches Perplexity Pro. Unscriptable, **subscription**. This is
  the high-value lane.

## The interface

```
ai local  "<prompt>"          free floor   — unlimited, private, offline
ai code   "<task>"            deep repo    — Claude Code (scarce; the good stuff)
ai code --lane codex "<task>" second lane  — Codex, separate 5h meter
ai search "<query>"           scripted     — Sonar API, cited, metered
ai research "<query>"         Opus-grade   — Perplexity Pro Deep Research
ai route  "<task>"            advisory lane suggestion
ai status                     meters, where to read each, what's installed
```

**It is a dispatcher, not a router.** It doesn't try to pick for you or chain
lanes. Two reasons, both learned earlier in this project: (1) cross-checking lanes
against each other is the fan-out pattern that burns quota, and (2) with four
tools the real cost is context-switching, which a script can't fix — but a single
muscle-memory command *can* reduce. `ai route` suggests; it never dispatches.

One rule in `route` is not advisory: anything matching clinical/PHI/student-record
keywords routes to **local**, always. Same data pin as EduCloud — sensitivity beats
cost logic, enforced by the lane, not by trust.

## Herdr surface: one pane per meter

`herdr/lanes.sh` opens claude / codex / local as three panes. The key difference
from the single-vendor setup: **each pane draws a different meter**, so running
them in parallel genuinely adds capacity instead of racing for one wallet.
Serialize *within* a meter (never two claude panes), parallelize *across* meters.
When Herdr's 5h/Week bars on the claude pane run low, push work to the codex or
local pane instead of waiting for a reset.

## What this pilots for EduCloud

| Personal hybrid | EduCloud full version |
|---|---|
| `.claude/sources.json` | `.claude/sovereign-registry.json` |
| four subscriptions | pool of institutional endpoints |
| free-before-metered (local → codex → claude) | free-before-allocation (jetstream2 → campus HPC) |
| reserve the Opus cap | reserve SU allocations |
| clinical work pinned to local | sensitive workspaces get a local-only config |
| "which meter has headroom" | broker health / circuit-breaking |

The open question the pilot answers before institutional scale: **does routing by
task type actually reduce draw on the scarce tier without a rise in failures?**
Same question `measure.py` asks — so log which lane handled what, and after a few
weeks you'll know whether the policy generalizes or just felt tidy.

## Honest limits

- **No public quota API** for Claude or Codex, so `ai status` tells you *where* to
  look (`/status` in-session, Codex usage dashboard) rather than showing numbers.
  Automating the read is the upgrade if either vendor ships an endpoint.
- **Codex's Plus window is shared** with ChatGPT Work and the Excel agent — heavy
  use there eats the coding lane.
- `ai search` costs real money past the $5/mo credits; it is not a free lane.
- Four tools still means four mental models. The dispatcher reduces the friction of
  *choosing*; it doesn't eliminate the cost of *knowing*.
