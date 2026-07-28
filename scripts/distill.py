#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
distill — turn the platform's own verifier logs into training data.

The key property (specs/09 §4): this platform LABELS ITSELF. No hand annotation.

  routing (R2)   the CHEAPEST TIER THAT PASSED is the correct route, by
                 construction. The fail-up guard produces perfect labels as a
                 side effect of doing its job.
  triage  (R1)   tasks that needed a clarification vs. tasks that one-shot at
                 the floor = a natural specified/underspecified split.
  adapt   (R3)   template_id x verified outcome = which template wins per
                 (lane, model class).

Emits JSONL ready for LoRA SFT (messages format) plus a report on whether there
is enough signal to bother training yet.

  distill.py --project . --role routing --out data/routing.jsonl
  distill.py --project . --report

HONEST LIMIT (specs/09 §6): these labels come from your own ladder, so a model
trained on them learns YOUR ladder, not the optimal one. Keep a held-out,
human-judged slice as an anchor, and gate every adapter on the platform's
non-inferiority rule before it ships.
"""
import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

MIN_PER_ROLE = 300          # below this, prompted roles beat a weak adapter


def state(project: str) -> Path:
    return Path(project) / ".claude" / "state"


def read_jsonl(p: Path) -> list[dict]:
    if not p.is_file():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def tasks(project: str) -> list[dict]:
    """Reconstruct per-task outcomes from the guard's attempt log."""
    by_run = defaultdict(list)
    for a in read_jsonl(state(project) / "failup-log.jsonl"):
        by_run[a.get("run_id", a["ts"])].append(a)
    out = []
    for run_id, run in by_run.items():
        run.sort(key=lambda a: a["tier"])
        passed = [a for a in run if a["ok"]]
        win = min((a["tier"] for a in passed), default=None)
        out.append({
            "run_id": run_id,
            "task": run[0].get("task", ""),      # guard logs task text if present
            "start_tier": run[0]["tier"],
            "win_tier": win,
            "win_model": next((a["model"] for a in run if a["tier"] == win), None),
            "attempts": len(run),
            "stalled": win is None,
        })
    return out


# ---------------------------------------------------------------- builders --

def build_routing(project: str) -> list[dict]:
    """Label = the cheapest tier that passed. Ground truth, for free."""
    rows = []
    for t in tasks(project):
        if t["stalled"] or not t["task"] or t["win_model"] is None:
            continue
        rows.append({"messages": [
            {"role": "system", "content":
             "Route this coding task. Reply with only the target model string."},
            {"role": "user", "content": t["task"]},
            {"role": "assistant", "content": t["win_model"]},
        ], "meta": {"run_id": t["run_id"], "win_tier": t["win_tier"]}})
    return rows


def build_triage(project: str) -> list[dict]:
    """Positive = one-shot at the floor. Negative = needed clarification."""
    clarified = {r.get("run_id") for r in
                 read_jsonl(state(project) / "triage-log.jsonl") if r.get("clarify")}
    rows = []
    for t in tasks(project):
        if not t["task"]:
            continue
        under = t["run_id"] in clarified
        rows.append({"messages": [
            {"role": "system", "content":
             "Is this task specified well enough to dispatch? Reply SPECIFIED "
             "or UNDERSPECIFIED."},
            {"role": "user", "content": t["task"]},
            {"role": "assistant", "content":
             "UNDERSPECIFIED" if under else "SPECIFIED"},
        ], "meta": {"run_id": t["run_id"]}})
    return rows


def build_adapt(project: str) -> list[dict]:
    """Preference pairs: for a (lane, class), which template verified better."""
    log = read_jsonl(state(project) / "adapt-log.jsonl")
    agg = defaultdict(lambda: defaultdict(lambda: [0, 0]))   # key -> tpl -> [ok, n]
    for r in log:
        key = (r.get("lane"), r.get("model_class"))
        cell = agg[key][r.get("template_id")]
        cell[1] += 1
        cell[0] += 1 if r.get("verified") else 0
    rows = []
    for key, tpls in agg.items():
        scored = sorted(((ok / n, t, n) for t, (ok, n) in tpls.items() if n >= 5),
                        reverse=True)
        if len(scored) >= 2:
            rows.append({"lane": key[0], "model_class": key[1],
                         "winner": scored[0][1], "winner_rate": round(scored[0][0], 3),
                         "loser": scored[-1][1], "loser_rate": round(scored[-1][0], 3),
                         "n": sum(s[2] for s in scored)})
    return rows


BUILDERS = {"routing": build_routing, "triage": build_triage, "adapt": build_adapt}


# ------------------------------------------------------------------ report --

def report(project: str) -> None:
    ts = tasks(project)
    print(f"tasks with outcomes: {len(ts)}   stalled: {sum(t['stalled'] for t in ts)}")
    missing_text = sum(1 for t in ts if not t["task"])
    if missing_text:
        print(f"  ! {missing_text} tasks have no task text logged — they are "
              "unusable for training. Ensure the guard logs the task string.")
    print(f"\n{'role':<10}{'examples':>10}{'ready?':>10}")
    print("-" * 30)
    for role, fn in BUILDERS.items():
        n = len(fn(project))
        ready = "yes" if n >= MIN_PER_ROLE else f"no (<{MIN_PER_ROLE})"
        print(f"{role:<10}{n:>10}{ready:>10}")

    dist = Counter(t["win_tier"] for t in ts if not t["stalled"])
    if dist:
        print("\nwin-tier distribution (the routing label distribution):")
        for tier, c in sorted(dist.items()):
            print(f"  tier {tier}: {c}")
        if len(dist) == 1:
            print("  ! only one tier ever wins — a router trained on this learns"
                  "\n    a constant. Vary the workload before training.")

    print("\nUntil a role reads 'yes', prompted roles outperform a weak adapter."
          "\nGate any adapter on non-inferiority vs. the prompted baseline.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=os.getcwd())
    ap.add_argument("--role", choices=list(BUILDERS))
    ap.add_argument("--out")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()

    if a.report or not a.role:
        report(a.project)
        return
    rows = BUILDERS[a.role](a.project)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text("".join(json.dumps(r) + "\n" for r in rows))
        print(f"[distill] wrote {len(rows)} examples -> {a.out}")
    else:
        for r in rows:
            print(json.dumps(r))


if __name__ == "__main__":
    main()
