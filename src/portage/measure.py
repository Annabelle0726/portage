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
import importlib.util
import json
import os
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path


def _load_runlog():
    """The shared run reconstruction (`runlog.py`), loaded by path.

    measure.py is a single-file `uv run --script` utility rather than a package
    member, and tests load it by path too, so a plain `import runlog` would
    resolve only when sys.path happens to contain src/portage. Loading by path
    works in both modes and adds no dependency — runlog.py is stdlib-only, like
    everything else in this repo's core. Same idiom, and same reason, as
    failup.py::code_profile().
    """
    path = Path(__file__).resolve().parent / "runlog.py"
    spec = importlib.util.spec_from_file_location("portage_runlog", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runlog = _load_runlog()


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


# ── WHAT THIS MODULE CANNOT SEE, AND WHAT THAT MEANS FOR A FUTURE METRIC ────
# measure.py reads `failup-log.jsonl` only — the ladder failup.py walks, whose
# rungs are named in `.claude/tiers.json` (local-small, sovereign-work, sonnet,
# opus). It has NO visibility into `registry.yaml`'s alias-based LiteLLM
# deployments (classifier, code_small, code_large, research_synthesis, ...).
# The two are structurally separate systems: failup.py never opens
# registry.yaml, which is why the Kimi K3 Fable-tier row cannot appear in
# anything computed below today.
#
# That changes the moment someone measures registry-alias traffic directly.
# `proprietary_displacement` is named in the platform docs but implemented
# nowhere; if it — or any future metric over registry-alias traffic — is
# built, it MUST exclude from any "open-ladder win":
#
#   * every row with `fable_tier: true` (today: Kimi K3 on code_large and
#     research_synthesis), and
#   * every row whose `license_family` is outside the `open_weight_only`
#     allowlist — published weights do not imply an acceptable license, which
#     is the whole reason license_family exists (CW-04 §2.5).
#
# Both exclusions are needed, and the second is not implied by the first. A
# K3 rescue is reachable in principle through LiteLLM's own retry/fallback
# even while `enabled: false` — the declarative gate narrows exposure but does
# not close it (P6-report §1, "the honest limit of a declarative gate"). Left
# uncounted-for, such a rescue would misreport as an open-weight success and
# flatter exactly the number the displacement claim rests on.
#
# Sources: CW-04 §2.5 and P7-report's ambiguity note, both in
# `portage-local/docs/reports/`. Mirrored in registry.schema.json's
# `license_family` description — keep the two in sync if either changes.
def summarize(project: str, since, until) -> dict:
    """The headline numbers, over ADMISSIBLE runs only.

    Every capability statistic below — floor-pass, escalation, ceiling-stall and
    the win-tier distribution — is computed over runs where every tier below the
    winner actually produced a capability verdict (`runlog.reconstruct`). A run
    whose cheaper tier was rate-limited says nothing about whether that tier
    could have done the task, and counting it inflated `escalation_rate` and
    deflated `floor_pass_rate`.

    The excluded runs are COUNTED, never silently dropped: `inadmissible_runs`
    and `inadmissible_rate` are part of the returned dict and are printed. So is
    `stalled`, the raw count over the whole population, which stays distinct
    from `ceiling_stall_rate` (admissible only) so that a run which stalled
    BECAUSE every tier was unreachable shows up as both facts rather than
    collapsing into one.
    """
    attempts = [a for a in read_jsonl(state(project) / "failup-log.jsonl")
                if in_window(a["ts"], since, until)]
    runs = runlog.reconstruct(attempts)
    admissible, inadmissible = runlog.partition(runs)

    tasks = len(runs)
    n_adm = len(admissible)
    stalled_all = sum(1 for r in runs if r["stalled"])

    escalated = stalled = floor_pass = 0
    win_tier = defaultdict(int)
    for r in admissible:
        if r["stalled"]:
            stalled += 1
            continue
        top = r["win_tier"]
        win_tier[top] += 1
        if top == 0:
            floor_pass += 1
        if len(r["attempts"]) > 1 and top > r["start_tier"]:
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
        "admissible_tasks": n_adm,
        "inadmissible_runs": inadmissible,
        "inadmissible_rate": _pct(inadmissible, tasks),
        "stalled": stalled_all,
        "floor_pass_rate": _pct(floor_pass, n_adm),
        "escalation_rate": _pct(escalated, n_adm),
        "ceiling_stall_rate": _pct(stalled, n_adm),
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
        f"  admissible:         {s['admissible_tasks']}   "
        "(every tier below the winner was actually reached)",
        f"  EXCLUDED:           {s['inadmissible_runs']} "
        f"({s['inadmissible_rate']}%)   <- a cheaper tier was never tried; "
        "these say nothing about capability",
        f"  stalled (all runs): {s['stalled']}",
        "  ── the four below are over ADMISSIBLE runs only ──",
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


def tasks_in(project: str, since, until) -> tuple[list[dict], int]:
    """ADMISSIBLE tasks in the window, and the number excluded.

    Returns `(rows, excluded)` — a pair rather than a list, so that no caller
    can take the admissible population without also holding the count it has to
    report. `downscale()` prints that count next to its thin-data warning.

    `proven` is the reason this filter matters most: it means "something cheaper
    was actually tried and failed", and it feeds the counterfactual that decides
    whether a paid lane can be cancelled. If the cheaper tier was rate-limited
    it was not tried, and `proven` was a false positive that argued for keeping
    a lane the evidence never justified. Runs where that happened are excluded
    here rather than being repaired, because there is no repair: the run does not
    contain the observation.
    """
    attempts = [a for a in read_jsonl(state(project) / "failup-log.jsonl")
                if in_window(a["ts"], since, until)]
    admissible, excluded = runlog.partition(runlog.reconstruct(attempts))

    out = []
    for r in admissible:
        win = r["win_tier"]
        out.append({
            "start_tier": r["start_tier"],
            "win_tier": win,
            "win_meter": meter_of(r["win_model"]) if win is not None else None,
            # proven = something cheaper was actually tried and failed
            "proven": win is not None and r["start_tier"] < win,
            "stalled": r["stalled"],
        })
    return out, excluded


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
    tasks, excluded = tasks_in(project, since, until)
    inter = interactive_use(project, args.use_log)
    n = len(tasks)

    if not ladder:
        print("[downscale] no tiers file found — cannot reason about the ladder.")
        return

    print(f"ladder (cheapest first): {' -> '.join(ladder)}")
    thin = ""
    if n < THIN_DATA:
        thin = "   (thin data — treat everything below as directional)"
    print(f"automated tasks in window: {n}{thin}")
    # The exclusion count sits NEXT TO the thin-data warning on purpose:
    # exclusions make thin data thinner, and the operator has to see both
    # numbers before cancelling a subscription on the strength of the table
    # below. Printed even when zero, so its absence is never mistaken for
    # "nothing was dropped".
    print(f"excluded as inadmissible:  {excluded}"
          "   (a cheaper tier was never reached — the run cannot prove"
          " anything about it)")
    print()

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
    if excluded:
        print(f"  (computed over {len(resolved)} admissible resolved tasks; "
              f"{excluded} run(s) excluded — see above)")

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
