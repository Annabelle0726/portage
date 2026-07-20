---
name: large-task
description: Plan-first execution for large multistage tasks. Use when a task is too big for one pass — it spans multiple files or stages, or needs sequenced steps with verification between them. Plans with Opus, requires human approval of the plan, executes each stage under the fail-up guard, and verifies at integration. Do NOT use for single-file or clearly scoped changes.
---

# Large-task, plan-first

Accuracy on a big task comes from the plan and the seams, not from parallelism.
Follow this; do not fan out.

## Steps

1. **Plan.** Produce a structured plan with Opus (the `planner` subagent, or
   `scripts/plan.py plan --task "<task>"`). The plan lists ordered subtasks with
   dependencies, files touched, an acceptance check each, an integration check,
   and the risky seams. It is saved to `.claude/state/plans/`.

2. **Stop for approval.** Surface the plan to the human. This is a milestone-gate
   decision — real review, because nothing unit-tests a plan. Do not proceed
   without approval. A re-plan needs re-approval.

3. **Execute.** Run the approved plan (`scripts/plan.py run --plan <file>`).
   Each subtask runs in dependency order as a normal guarded task under
   `failup.py`, so a stage harder than planned self-corrects upward. Sequential
   by default; parallelize only stages marked `parallelizable` and file-disjoint,
   only in Lane B, bounded via Herdr.

4. **Verify the seams.** Run the plan's `integration_check` at the end. On
   failure, identify which stage's contract is implicated and re-run that stage
   or re-plan (back to step 2) — never loop autonomously on a bad plan.

## Guardrails
- Opus is spent once, on the plan. Stages run cheap under the guard.
- If the task turns out to be single-file or clearly scoped, abandon this skill
  and just do it directly — planning overhead isn't free.
