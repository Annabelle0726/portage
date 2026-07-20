# 01 — Decomposition driver

Turns a large multistage task into an ordered, verified execution **without**
fan-out. Implemented by `scripts/plan.py`.

## Principle

Accuracy on a large task comes from getting the plan right and verifying at the
seams — not from parallelism. So: spend Opus once on the plan, make the plan a
human-approved artifact, execute each stage cheaply under the fail-up guard, and
check integration at the end.

## Two-phase, because the human gate is load-bearing

The driver is split into `plan` and `run` so you *cannot* execute an unapproved
plan — the gate is structural, not a prompt.

### Phase 1 — `plan`

Opus (via the `planner` subagent / `think` route) emits a **structured plan**,
saved to `.claude/state/plans/<stamp>.json`. Schema:

```json
{
  "task": "original request",
  "subtasks": [
    {
      "id": "s1",
      "goal": "one scoped, independently checkable change",
      "depends_on": [],
      "files_touched": ["path/a.py"],
      "parallelizable": false,
      "acceptance_check": "how a human/CI knows this stage is done"
    }
  ],
  "integration_check": "the cross-stage check that must pass at the end",
  "risky_seams": ["where stages could disagree; watch these"]
}
```

The driver prints the plan and stops. Nothing runs yet.

### Human gate

You review and approve the plan (this *is* your milestone-gate work — real, not
ceremony, because nothing unit-tests a plan). Approval = passing the plan file to
`run`. A re-plan requires re-approval.

### Phase 2 — `run`

Execute subtasks in dependency (topological) order. Each subtask is just a normal
task: classified, routed, and wrapped by `failup.py`, so per-stage accuracy is
already covered — a stage harder than the plan assumed self-corrects upward.

- **Sequential by default.** Parallelize only subtasks that are both
  `parallelizable` and file-disjoint, only in Lane B off-pool, and bounded via
  Herdr `wait agent-status`. Parallelism is a throughput option, never the
  correctness mechanism.
- **Integration check at the end.** Run `integration_check` (typically the full
  suite plus any cross-stage assertion). This is the seam verification.
- **On integration failure:** do not blindly re-run everything. Surface which
  subtask's contract the failure implicates; re-run that stage, or re-plan (which
  re-enters the human gate). A bad plan poisons every stage under it, and the
  guard verifies *execution*, not the plan — so plan failures must return to a
  human, not loop autonomously.

## Quota rules

Opus is spent once, on the plan. Execution runs on local/Sonnet under the guard.
No frontier tokens per stage unless a stage escalates into Opus on its own merit.

## Instrumentation

Persist the plan artifact, per-subtask results (via `failup-log.jsonl`), and the
integration outcome. Together with quota drawn, this is the evidence a large-task
run actually cost less and stayed correct.

## Non-goals

Not an autonomous orchestrator. No unprompted decomposition or fan-out. Not a
general workflow engine — it drives *one* approved plan to completion and stops.
