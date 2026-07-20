# 05 — Federated sovereign compute

> **STATUS: reasoning current, implementation superseded.** The custom broker described here was deleted; LiteLLM provides cooldowns, ordered failover and health checks natively. See `litellm.config.yaml` and HANDOFF.md §2. The free-before-allocation policy and the sovereign-but-not-private data rule still stand exactly as written.

The EduCloud sovereign tier is a **federation** of institutional/open-weight
endpoints, not a single Jetstream2 URL. This is the direction the Fable 5
suspension argued for: a single frontier dependency got pulled by export controls
overnight; institutional compute you can pool and fail over across is the hedge.

## What "federated" adds here

The `sovereign` CCR provider points at a local broker
(`scripts/sovereign_broker.py`) that fronts a **pool** of endpoints
(`.claude/sovereign-registry.json`) as one OpenAI-compatible tier:

```
CCR 'sovereign' ─▶ broker :8787 ─┬─▶ jetstream2   (free, priority 1)
                                 ├─▶ campus-hpc   (allocation, priority 2)
                                 └─▶ ...add ACCESS resources
      all endpoints down ─▶ 503 ─▶ fail-up guard escalates to Opus
```

Per request the broker picks, among endpoints serving the model and not in
cooldown, **free before metered, then lowest priority number**. On failure it
circuit-breaks that endpoint (cooldown) and tries the next. Only when the whole
federation is unavailable does it return 503 — which the fail-up guard reads as a
failed tier and escalates to the proprietary ceiling. So one HPC endpoint being
gated, in maintenance, or queue-saturated degrades to a peer institution, not
straight to paid Opus.

## Allocation-awareness

Jetstream2 inference is currently free (no SU cost); other ACCESS resources burn
allocation. The registry tags each endpoint `cost: free | allocation`, and the
broker prefers free ones — a metered endpoint is used only when the free tier is
unhealthy, protecting SU budgets. This is the institutional analog of the Opus-cap
reservation on the Claude side.

## Reuse, don't reinvent

The broker is deliberately thin: it assumes each endpoint is already
OpenAI-compatible. Expose HPC jobs via STREAM's `hpc-as-api` / `streamrelay`
(which already solve firewall traversal and OpenAI-compatible exposure); the
broker adds only the federation, health/failover, and reliability logging that the
existing tools don't. Argonne's FIRST is the reference for federated inference
supply if the pool grows beyond ACCESS.

## Data-classification interaction (unchanged, and it matters more here)

The federation is shared research infrastructure — sovereign, **not private**, and
research/education-use-only. So sensitive workspaces still use
`config.educloud-sensitive.json`, which has **no `sovereign` provider at all** —
the broker is physically unreachable from a clinical-data repo. Federating more
institutions widens the sovereign tier for open work; it never widens what
sensitive data can touch.

## Measurement

The broker logs every request's endpoint, latency, and outcome to
`.claude/state/sovereign-log.jsonl`. That feeds two things the contribution needs:
per-endpoint **reliability** (how often each institution was healthy) and how often
the federation absorbed work that would otherwise have escalated to paid compute —
i.e., the concrete value of federating.

## Honest limits

- Non-streaming forwarding (fine for Lane B automation; streaming is a TODO).
- Health is lazy circuit-breaking + an on-demand `check`; there's no active
  queue-depth or allocation-balance awareness yet — an HPC endpoint that accepts
  the request but queues it for minutes looks "healthy." Real HPC-queue awareness
  is a Stage-3 refinement.
- Off-instance Jetstream2 access was "coming soon" as of the research; the pool is
  solid on-instance, so run Lane B on a Jetstream2 VM where the sovereign tier is
  native, and treat off-instance endpoints as best-effort until confirmed.
