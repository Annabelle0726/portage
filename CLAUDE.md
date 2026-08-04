# CLAUDE.md

> **Roster banner — 2026-08-04.** Provider/model content in
> `REVISION-PLAN.md`, `docs/PLATFORM.md` and `docs/specs/02`, `08`, `10`, `11`
> is superseded by `CW-04-model-roster.md`
> (`portage-local/docs/reports/`). The rewrite has not been performed. Read
> CW-04 and `CW04-HB0-drift.md` before acting on any ladder or model name.

Constitution for this repo. Loaded every turn — kept deliberately lean, because
everything here re-sends on each turn and taxes the shared pool. Situational
guidance lives in skills (`.claude/skills/`), not here.

## Environment
- Python only, managed with `uv`. Run tests with `uv run pytest -q`.
- Never write files outside the repo.

## Model & effort discipline
- Default to Sonnet 5. Use `/model opus` only for judgment: architecture,
  ambiguous debugging, planning a large task, reviewing consequential diffs,
  milestone-gate decisions.
- Default effort. Escalate effort only for those judgment cases — never for
  routine execution.

## Lanes
- This interactive session is Lane A: native Claude Code. claude-code-router
  was deleted in Phase 2 — Claude Code reaches LiteLLM directly.
- Automation (CI, scheduled, batch) is Lane B and runs through the LiteLLM
  gateway, off the interactive session. Don't start Lane B work from an
  interactive session.

## Large tasks
- If a task spans multiple files/stages or needs sequencing, use the
  `/large-task` skill: plan first, get the plan approved, then execute.
- Do not fan out. Sequential by default; parallelize only provably independent
  stages, and only in Lane B.

## Subagents
- Reviewer and planner subagents are read-only. All edits stay on the parent
  agent (subagents can't answer permission prompts).

## Gates (non-negotiable)
- Milestone-gate decisions and large-task plan approvals are human-approved,
  pinned to Opus, and never downshifted for quota.
- Gate on green tests. A red suite blocks the gate.
