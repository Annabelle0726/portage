#!/usr/bin/env -S uv run --script
# SPDX-License-Identifier: AGPL-3.0-only
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Measurement harness — the part that makes this a *result*, not a config.

Reads the guard's own logs and the manually-recorded /usage snapshots and reports,
per window, the two numbers the router ecosystem never publishes together:

  - EFFICIENCY: how far down the ladder work actually resolved (share of tasks that
    passed at the floor/sovereign tier vs. had to escalate to the proprietary
    ceiling), and quota/credit drawn over the window.
  - QUALITY: the ceiling-stall rate (tasks that never passed even at the top).

The claim to defend is "quota/credit down, with NO rise in ceiling-stalls." A win
on efficiency that raises stalls is not a win.

There is no public /usage API, so quota figures come from snapshots you record by
hand from `/usage` (see `snapshot`). Everything else is derived from the logs.

  measure.py snapshot --label baseline --opus-pct 12 --all-pct 34 --credit-left 82
  measure.py report   --since 2026-07-01 --until 2026-07-08   # one window
  measure.py report   --since 2026-07-01 --until 2026-07-08 \
                      --vs-since 2026-07-08 --vs-until 2026-07-15   # baseline vs treat
"""
import argparse
import json
import os
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path


def state(project: str) -> Path:
    d = Path(project) / ".claude" / "state"
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_jsonl(path: Path):
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def in_window(ts: str, since, until) -> bool:
    t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if since and t < since:
        return False
    if until and t > until:
        return False
    return True


def snapshot(args) -> None:
    entry = {
        "ts": datetime.now(UTC).isoformat(), "label": args.label,
        "opus_pct": args.opus_pct, "all_pct": args.all_pct,
        "credit_left": args.credit_left,
    }
    with (state(args.project) / "usage-log.jsonl").open("a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[measure] snapshot recorded ({args.label}): "
          f"opus={args.opus_pct}% all={args.all_pct}% credit_left={args.credit_left}")


def summarize(project: str, since, until) -> dict:
    attempts = [a for a in read_jsonl(state(project) / "failup-log.jsonl")
                if in_window(a["ts"], since, until)]
    # group escalation attempts into tasks by run_id
    by_run = defaultdict(list)
    for a in attempts:
        by_run[a.get("run_id", a["ts"])].append(a)

    tasks = len(by_run)
    escalated = stalled = floor_pass = 0
    win_tier = defaultdict(int)
    for run in by_run.values():
        run.sort(key=lambda a: a["tier"])
        passed = [a for a in run if a["ok"]]
        if not passed:
            stalled += 1
            continue
        top = min(a["tier"] for a in passed)
        win_tier[top] += 1
        if top == 0:
            floor_pass += 1
        if len(run) > 1 and top > min(a["tier"] for a in run):
            escalated += 1

    usage = [u for u in read_jsonl(state(project) / "usage-log.jsonl")
             if in_window(u["ts"], since, until)]
    usage.sort(key=lambda u: u["ts"])
    quota = {}
    if len(usage) >= 2:
        first, last = usage[0], usage[-1]
        quota = {
            "opus_cap_consumed_pts": _delta(first.get("opus_pct"), last.get("opus_pct")),
            "all_cap_consumed_pts": _delta(first.get("all_pct"), last.get("all_pct")),
            "credit_spent_pts": _delta(last.get("credit_left"), first.get("credit_left")),
        }

    return {
        "tasks": tasks,
        "floor_pass_rate": _pct(floor_pass, tasks),
        "escalation_rate": _pct(escalated, tasks),
        "ceiling_stall_rate": _pct(stalled, tasks),
        "win_tier_distribution": dict(sorted(win_tier.items())),
        "quota": quota,
    }


def _delta(a, b):
    return None if a is None or b is None else round(b - a, 1)


def _pct(n, d):
    return None if not d else round(100 * n / d, 1)


def _fmt(label, s: dict) -> str:
    q = s["quota"]
    lines = [
        f"── {label} ──",
        f"  tasks:              {s['tasks']}",
        f"  floor-pass rate:    {s['floor_pass_rate']}%   (resolved at tier 0)",
        f"  escalation rate:    {s['escalation_rate']}%",
        f"  ceiling-stall rate: {s['ceiling_stall_rate']}%   <- the quality guardrail",
        f"  win tier dist:      {s['win_tier_distribution']}",
    ]
    if q:
        lines += [
            f"  opus cap consumed:  {q['opus_cap_consumed_pts']} pts",
            f"  all cap consumed:   {q['all_cap_consumed_pts']} pts",
            f"  credit spent:       {q['credit_spent_pts']} pts",
        ]
    return "\n".join(lines)


def report(args) -> None:
    def parse(d):
        return datetime.fromisoformat(d).replace(tzinfo=UTC) if d else None

    a = summarize(args.project, parse(args.since), parse(args.until))
    print(_fmt("window", a))
    if args.vs_since or args.vs_until:
        b = summarize(args.project, parse(args.vs_since), parse(args.vs_until))
        print("\n" + _fmt("comparison window", b))
        # honest verdict heuristic
        stall_a, stall_b = a["ceiling_stall_rate"] or 0, b["ceiling_stall_rate"] or 0
        print("\n[verdict] "
              + ("efficiency gains are only real if the second window's stall rate "
                 "did NOT rise. "
                 f"stall {stall_a}% -> {stall_b}%: "
                 + ("QUALITY HELD — compare quota deltas for the efficiency win."
                    if stall_b <= stall_a
                    else "STALLS ROSE — the ladder is too aggressive; "
                         "do not claim a win.")))


# ---------------------------------------------------------------- downscale --

PROVIDER_TO_METER = {
    "anthropic": "claude", "claude": "claude",
    "openai": "codex", "codex": "codex",
    "local": "local", "ollama": "local",
    "sovereign": "sovereign", "jetstream2": "sovereign", "campus-hpc": "sovereign",
    "openrouter": "openrouter", "cheap": "openrouter",
    "perplexity": "perplexity", "sonar": "perplexity",
}

# A meter is only a real downscale candidate if losing it is cheap. These are
# deliberately conservative — a wrong "cut it" costs more than a wrong "keep it".
REDUNDANT_AT = 0.10        # <10% of tasks PROVEN to need it
THIN_DATA = 20             # fewer tasks than this in the window -> don't decide
LOCAL_FLOOR = 0.30         # <30% resolving free/local -> nothing is being absorbed


def meter_of(model: str) -> str:
    prov = (model or "").split(",")[0].strip().lower()
    return PROVIDER_TO_METER.get(prov, prov or "unknown")


def load_ladder(project: str, tiers_file: str | None) -> list[str]:
    """Ordered meters, cheapest first — the escalation ladder actually in use."""
    path = Path(tiers_file) if tiers_file else None
    if path and not path.is_absolute():
        path = Path(project) / path
    if not (path and path.is_file()):
        for guess in (".claude/tiers.claude.json", ".claude/tiers.educloud.json",
                      ".claude/tiers.local.json", ".claude/tiers.json"):
            if (Path(project) / guess).is_file():
                path = Path(project) / guess
                break
    if not (path and path.is_file()):
        return []
    raw = json.loads(path.read_text())
    seq = [meter_of(e if isinstance(e, str) else e.get("model", "")) for e in raw]
    # Several tiers can share one meter (Sonnet and Opus are both "claude").
    # The downscale question is about METERS, so collapse to first appearance.
    out = []
    for m in seq:
        if m not in out:
            out.append(m)
    return out


def tasks_in(project: str, since, until) -> list[dict]:
    """One record per task: which tier won, and what was proven along the way."""
    attempts = [a for a in read_jsonl(state(project) / "failup-log.jsonl")
                if in_window(a["ts"], since, until)]
    by_run = defaultdict(list)
    for a in attempts:
        by_run[a.get("run_id", a["ts"])].append(a)

    out = []
    for run in by_run.values():
        run.sort(key=lambda a: a["tier"])
        passed = [a for a in run if a["ok"]]
        started = run[0]["tier"]
        win = min((a["tier"] for a in passed), default=None)
        out.append({
            "start_tier": started,
            "win_tier": win,
            "win_meter": meter_of(next(a["model"] for a in run if a["tier"] == win))
                         if win is not None else None,
            # proven = something cheaper was actually tried and failed
            "proven": win is not None and started < win,
            "stalled": win is None,
        })
    return out


def interactive_use(project: str, use_log: str | None) -> dict:
    """Lane A / app-lane usage, if the herdr-meters plugin has been logging it."""
    path = Path(use_log) if use_log else state(project) / "use-log.jsonl"
    counts = defaultdict(int)
    for r in read_jsonl(path):
        counts[r.get("meter", "unknown")] += 1
    return dict(counts)


def downscale(args) -> None:
    def parse(d):
        return datetime.fromisoformat(d).replace(tzinfo=UTC) if d else None

    project = args.project
    since, until = parse(args.since), parse(args.until)
    ladder = load_ladder(project, args.tiers)
    tasks = tasks_in(project, since, until)
    inter = interactive_use(project, args.use_log)
    n = len(tasks)

    if not ladder:
        print("[downscale] no tiers file found — cannot reason about the ladder.")
        return

    print(f"ladder (cheapest first): {' -> '.join(ladder)}")
    thin = ""
    if n < THIN_DATA:
        thin = "   (thin data — treat everything below as directional)"
    print(f"automated tasks in window: {n}{thin}\n")

    # --- utilization -------------------------------------------------------
    resolved = [t for t in tasks if t["win_meter"]]
    by_meter = defaultdict(lambda: {"won": 0, "proven": 0})
    for t in resolved:
        by_meter[t["win_meter"]]["won"] += 1
        by_meter[t["win_meter"]]["proven"] += 1 if t["proven"] else 0

    print(f"{'meter':<12}{'won':>5}{'share':>8}{'proven':>8}{'unproven':>10}"
          f"{'interactive':>13}")
    print("-" * 60)
    for m in ladder + [k for k in by_meter if k not in ladder]:
        d = by_meter.get(m, {"won": 0, "proven": 0})
        share = _pct(d["won"], len(resolved)) or 0
        print(f"{m:<12}{d['won']:>5}{share:>7}%{d['proven']:>8}"
              f"{d['won'] - d['proven']:>10}{inter.get(m, 0):>13}")
    if not inter:
        print("\n  ! no interactive/app usage logged — Lane A and the Perplexity")
        print("    lane are INVISIBLE here. Enable herdr-meters use-logging before")
        print("    cutting anything, or you will undercount the lanes you use by hand.")

    # --- absorption floor --------------------------------------------------
    free_share = (sum(by_meter[m]["won"] for m in ("local", "sovereign") if m in by_meter)
                  / len(resolved)) if resolved else 0
    print(f"\nfree/local absorption: {round(100 * free_share)}%"
          f"  ({'above' if free_share >= LOCAL_FLOOR else 'BELOW'} the "
          f"{int(LOCAL_FLOOR * 100)}% floor)")
    if free_share < LOCAL_FLOOR:
        print("  -> routing is not actually absorbing work yet. No downscale is safe.")

    # --- counterfactual per meter -----------------------------------------
    print("\nif a lane disappeared:")
    for m in ladder:
        d = by_meter.get(m, {"won": 0, "proven": 0})
        if m == "local":
            print(f"  {m:<12} free — not a subscription; nothing to cut.")
            continue
        if d["won"] == 0 and inter.get(m, 0) == 0:
            print(f"  {m:<12} IDLE in this window -> strongest cut candidate "
                  "(confirm the window is representative).")
            continue

        # where would its work go? next meter up the ladder.
        i = ladder.index(m)
        receiver = next((x for x in ladder[i + 1:] if x != m), None)
        if receiver is None:
            print(f"  {m:<12} top of ladder — cutting it removes your ceiling. Keep.")
            continue

        # how reliable is the receiver, from actual observation?
        r = by_meter.get(receiver, {"won": 0})
        rate = _pct(r["won"], max(1, r["won"] + sum(
            1 for t in tasks if t["stalled"])))
        seen = r["won"]
        est = (f"~{rate}% observed pass rate at {receiver}" if seen
               else f"{receiver} never exercised — absorption UNKNOWN")
        verdict = ("redundant" if d["proven"] <= REDUNDANT_AT * max(1, len(resolved))
                   else "earning its place")
        print(f"  {m:<12} {d['proven']} tasks PROVEN to need it "
              f"({d['won'] - d['proven']} unproven) -> would fall to {receiver}; {est}")
        print(f"  {'':<12} verdict: {verdict}"
              f"{'  [thin data]' if n < THIN_DATA else ''}")

    print("\nreminder: subscriptions are step functions — you cut a whole lane or")
    print("none of it. 'Unproven' load is the absorbable kind; 'proven' is not.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=os.getcwd())
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("snapshot")
    s.add_argument("--label", default="")
    s.add_argument("--opus-pct", type=float, help="Opus weekly cap used, from /usage")
    s.add_argument("--all-pct", type=float, help="all-models weekly cap used")
    s.add_argument("--credit-left", type=float, help="separate credit remaining")

    r = sub.add_parser("report")
    r.add_argument("--since")
    r.add_argument("--until")
    r.add_argument("--vs-since")
    r.add_argument("--vs-until")

    d = sub.add_parser("downscale", help="which subscription lane could you drop?")
    d.add_argument("--since")
    d.add_argument("--until")
    d.add_argument("--tiers", help="ladder file; auto-detected if omitted")
    d.add_argument("--use-log", help="herdr-meters use-log.jsonl (interactive lanes)")

    args = ap.parse_args()
    {"snapshot": snapshot, "report": report, "downscale": downscale}[args.cmd](args)


if __name__ == "__main__":
    main()
