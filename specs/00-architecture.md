# 00 — Architecture & decision record

The design record for the two-lane, quota-aware Claude Code build. Operational
setup lives in the README; this is the *why*, so decisions don't get relitigated.

## The economic premise everything hangs on

On Claude Max, cheaper models save **quota, not dollars** — every interactive
session draws one shared pool (rolling 5h + two weekly caps, shared across chat /
Code / Cowork). API-layer routers optimize per-token cost, which a flat
subscription already flattened. So the objective is: spend the interactive pool
only on work that needs it, keep automation off it, and never fumble a hard task.

## Decisions

**Two lanes, split by billing bucket.** Interactive work (Lane A) stays on the
Max subscription with native Claude Code — a router there only adds cost.
Automation (Lane B) originally ran through claude-code-router; Phase 1 proved
Claude Code reaches LiteLLM's /v1/messages directly and Phase 2 deleted the
shim (docs/phase-1-findings.md). Lane B now targets the LiteLLM gateway.

**Three execution tiers + a local floor.** T0 background/classifier → a warm
local model (free, private, off every meter). T1 execution → Sonnet 5. T2
judgment → Opus 4.8. Local widens the floor, not the ceiling; T2 always tops out
at Opus. Local is also the privacy tier for anything touching clinical data.

**Escalation is verified, not predicted.** Rather than invest in a sophisticated
difficulty classifier, escalation rests on a deterministic **fail-up guard**:
after a T0/T1 run, check non-empty diff + `ruff` clean + `pytest` green; on
failure, park the attempt, reset clean, retry one tier up to Opus. Cheap routing
is *allowed to be wrong* because the guard catches misroutes. Known-hard classes
(milestone gate, review, plan) are hard-pinned to Opus and never downshifted.

**Large tasks are plan-first, not fan-out.** Decomposition = planning (cheap,
native, where accuracy lives), not parallel subagent swarms (quota-heavy, drift-
prone). The plan is a T2 task done once by Opus and **human-approved**; each
subtask then executes as a normal guarded task; accuracy is verified at the seams
(milestone gates + an integration check), because nothing unit-tests a plan.
See `01-decomposition-driver.md`.

**Herdr orchestrates; it does not multiply.** It bounds and serializes sessions
(`wait agent-status`) and hosts Lane B off-pool on the always-on iMac /
Jetstream2. It is an observability/discipline layer, not throughput.

## Excluded (deliberately)

Runtime prompt engineer (do prompt optimization offline if ever), multi-model
fan-out with an arbiter, a from-scratch router, and the sophisticated classifier.
The fail-up guard is what makes dropping the classifier safe.

## Boundary

Multi-account / round-robin token rotation to multiply Max throughput is against
Anthropic's terms. Everything here stays within one account's fair use and pushes
automation onto the separate credit / API.

## Measurement (the publishable part)

Log quota drawn per unit of work plus `failup-log.jsonl` (tier, result, seconds),
and run baseline-week vs. treatment-week. The contribution is the quota-aware
policy **and** the reproducible evidence that it saves quota without quality
regression — the thing the router ecosystem lacks.
