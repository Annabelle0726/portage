# 04 — Scheduling around rate resets (and multi-surface allocation)

Scheduling is the mechanism that enacts the three-surface wallet allocation: run
heavy automated Code off-hours so it never competes with daytime interactive
Science / Cowork / Code on the shared wallet. Implemented by `scripts/scheduler.py`.

## The reset mechanics you're scheduling against

- **5-hour window** — rolling, resets 5h after the *first message* that opened it.
  Unused capacity does **not** roll over.
- **Weekly all-models cap** and **weekly Opus cap** — rolling 7 days from the
  *first message* of the cycle. Both are account-level and shared across Science,
  Cowork, and Code.
- No universal "everyone resets Monday" — resets follow *your* usage rhythm.
- No public API to read `/usage`, so scheduling is anchor-based, not live.

## The caveat that shapes the design

Automated Lane B (`claude -p`) draws the **separate monthly credit** (5x: $100),
then API rates — **not** the 5h/weekly wallet. So "fire exactly at the 5-hour
reset" is mostly moot for the queue: the queue isn't gated by the 5h window at
all. What scheduling actually buys for Lane B:

1. **Contention avoidance (the main win).** Run the queue overnight / off-hours so
   automated Code isn't drawing attention or your machine's resources while you're
   doing interactive Science/Cowork on the wallet during the day. The surfaces
   don't fight.
2. **Credit pacing.** Spread the monthly credit across the month instead of
   burning it in one afternoon batch (`--max-per-run`, `--gap`).
3. **Unattended Opus safety.** Scheduled runs default to a Sonnet ceiling
   (`--max-tier 0`) so a batch can't silently drain the shared, tighter Opus cap
   overnight.

Where the 5h reset *does* matter is **interactive** work (Science, Cowork, Code
on the wallet) — start heavy bursts just after a fresh window opens. The scheduler
can't run those (they're interactive), but `scheduler.py resets` computes the
timing so you can, and you can pair it with a calendar reminder.

## Usage

```
# queue automated tasks (from anywhere — CI, a commit hook, by hand)
scripts/scheduler.py enqueue --task "regenerate fixtures and update snapshot tests"

# drain a few, paced, off-hours — wire to cron/launchd:
#   0 2 * * *  cd /repo && scripts/scheduler.py drain --max-per-run 3 --gap 120
scripts/scheduler.py drain --max-per-run 3 --gap 120

# compute reset timing for your INTERACTIVE bursts
scripts/scheduler.py resets --window-anchor 2026-07-16T09:00:00+00:00 \
                            --week-anchor   2026-07-14T08:30:00+00:00
```

Each queued task runs through `failup.py`, so the deterministic acceptance gate
and the budget ceiling still apply — scheduling changes *when* work runs, not the
quality/quota guarantees around it.

## The allocation this serves

| Surface | Wallet | Escape hatch | Scheduling role |
|---|---|---|---|
| Claude Science | shared (Opus-hungry) | grant credits ($30k/project) | run research bursts in fresh windows; move to grant credits |
| Claude Cowork | shared | none | sequence against Science; daytime |
| Claude Code (interactive) | shared | — | light daytime use |
| Claude Code (automated) | **separate credit** | this is the valve | **queue → drain overnight** |

Reserve Opus everywhere — it's one shared cap across all three surfaces, so a
heavy Science week can exhaust the Opus budget Code's escalations rely on.
