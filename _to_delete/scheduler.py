#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Reset-aware scheduler (Lane B).

Paces a queue of automated tasks so they run during off-hours — not competing
with daytime interactive Science / Cowork / Code on the shared wallet — and don't
all fire at once.

Honest scope (read this before relying on it):
- Lane B runs via `claude -p`, which draws the separate MONTHLY credit (5x: $100),
  then API rates — NOT the 5-hour / weekly wallet. So "fire exactly at the 5-hour
  reset" mostly matters for wallet-drawing INTERACTIVE work; for THIS queue the
  real levers are (a) avoid daytime contention with the app surfaces, and (b)
  spread the monthly credit evenly instead of burning it in one batch.
- There is no public API to read /usage, so timing is anchor-based and
  conservative, not live-quota-aware.
- Unattended runs default to a Sonnet ceiling (--max-tier 0) so a scheduled batch
  can't silently drain the shared, tighter Opus cap while you're asleep.

Commands:
  scheduler.py enqueue --task "..." [--project P] [--max-tier N]
  scheduler.py drain   [--max-per-run K] [--gap SECONDS] [--max-tier N]
  scheduler.py resets  [--window-anchor ISO] [--week-anchor ISO]

Wire `drain` to cron / launchd at your chosen off-hours (and, if you want, shortly
after a weekly reset). Example crontab — drain 3 tasks nightly at 02:00 local:
  0 2 * * *  cd /path/to/repo && src/portage/scheduler.py drain --max-per-run 3
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAILUP = HERE / "failup.py"
DEFAULT_TIERS = ".claude/tiers.claude.json"


def queue_path(project: str) -> Path:
    p = Path(project) / ".claude" / "state" / "queue.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def enqueue(args) -> None:
    entry = {
        "task": args.task,
        "project": args.project,
        "tiers": args.tiers,
        "max_tier": args.max_tier,
        "added": datetime.now(UTC).isoformat(),
    }
    with queue_path(args.project).open("a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[sched] enqueued: {args.task[:60]}")


def drain(args) -> None:
    qp = queue_path(args.project)
    if not qp.is_file():
        print("[sched] queue empty")
        return
    pending = [json.loads(line) for line in qp.read_text().splitlines() if line.strip()]
    ran, remaining = 0, []

    for item in pending:
        if ran >= args.max_per_run:
            remaining.append(item)          # leave the rest for the next drain
            continue
        # Unattended => cap at Sonnet unless the item/flag says otherwise.
        cap = args.max_tier if args.max_tier is not None else item.get("max_tier", 0)
        cmd = ["uv", "run", str(FAILUP),
               "--task", item["task"],
               "--project", item.get("project", args.project),
               "--tiers", item.get("tiers", args.tiers),
               "--runner", "claude -p"]
        if cap is not None:
            cmd += ["--max-tier", str(cap)]
        print(f"[sched] running: {item['task'][:60]}  (max-tier={cap})")
        rc = subprocess.run(cmd, cwd=item.get("project", args.project)).returncode
        ran += 1
        if rc != 0:
            print("[sched] task did not pass under the cap; left for review",
                  file=sys.stderr)
        if ran < args.max_per_run and args.gap:
            time.sleep(args.gap)             # pace so we don't fire all at once

    qp.write_text("".join(json.dumps(x) + "\n" for x in remaining))
    print(f"[sched] drained {ran}, {len(remaining)} left in queue")


def resets(args) -> None:
    now = datetime.now(UTC)
    wa = datetime.fromisoformat(args.window_anchor) if args.window_anchor else now
    ka = datetime.fromisoformat(args.week_anchor) if args.week_anchor else now
    five = wa + timedelta(hours=5)
    week = ka + timedelta(days=7)
    print("[sched] reset estimates (anchor-based; rolling from your first message):")
    print(f"  5-hour window: anchor {wa.isoformat()} -> resets {five.isoformat()}")
    print(f"  weekly cap:    anchor {ka.isoformat()} -> resets {week.isoformat()}")
    print("\n  Heavy interactive Science/Cowork/Code bursts are best started just")
    print("  after a fresh 5-hour window opens. Unused window capacity does not")
    print("  roll over — but note automated Lane B draws the credit, not this pool.")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("enqueue")
    e.add_argument("--task", required=True)
    e.add_argument("--project", default=os.getcwd())
    e.add_argument("--tiers", default=DEFAULT_TIERS)
    e.add_argument("--max-tier", type=int, default=0)

    d = sub.add_parser("drain")
    d.add_argument("--project", default=os.getcwd())
    d.add_argument("--tiers", default=DEFAULT_TIERS)
    d.add_argument("--max-per-run", type=int, default=3)
    d.add_argument("--gap", type=int, default=0, help="seconds between tasks")
    d.add_argument("--max-tier", type=int, default=None)

    r = sub.add_parser("resets")
    r.add_argument("--window-anchor", default=None, help="ISO time of the first "
                   "message in the current 5h window")
    r.add_argument("--week-anchor", default=None, help="ISO time of the first "
                   "message in the current weekly cycle")

    args = ap.parse_args()
    {"enqueue": enqueue, "drain": drain, "resets": resets}[args.cmd](args)


if __name__ == "__main__":
    main()
