# Local Platform — Hybrid Open-First with Proprietary PAYG Ceiling

*Recommended Scale 1 transition architecture: open-weight models receive the workload first; proprietary APIs remain available only as metered, evidence-based escalation.*

> **Revised 2026-07-28 per CW02-decisions.md §3 (dormant-slot synthesis).**
> local_burst is no longer a tier — the MacBook is a second health-checked
> deployment of `local_fast`. The freed T2 slot holds `local_large` (dormant,
> enabled: auto). Groq enters at T3 (`remote_open_fast`); Together is a
> defined-but-dormant T5. Capability aliases are the seven-cell set in CW02 §3.

## Purpose

This is the recommended **production transition mode** while the platform measures whether open-weight models have reached sufficient parity for the user's real workloads.

The architecture preserves the existing Herdr + LiteLLM routing spine, deterministic triage, `adapt.py`, `failup.py`, plan-first decomposition, and `measure.py`.

The major change from the original subscription ladder is:

> **Remove fixed Claude Max/Codex-style subscription rungs.**

Use local open-weight inference first, then hosted open-weight inference, and only then use proprietary APIs when the open ladder has genuinely failed or a specialist capability requires them.

---

## Core principle

> **Open-weight by default; proprietary only when it produces a verified outcome that the open ladder could not.**

The target is to eliminate recurring model subscriptions immediately while preserving a measured frontier safety valve.

---

## Scale 1 footprint

### Existing hardware

- **iMac** — always-on LiteLLM + local inference
- **MacBook Pro** — Herdr surface plus opportunistic local inference worker
- **2 TB NVMe** — active AI workspace
- **8 TB Seagate** — bulk/archive/backup tier

### Future hardware

- **High-memory local AI node** — target roughly 128 GB model-accessible memory
- Added when telemetry shows it will materially replace hosted or proprietary inference

---

## Recommended topology

```text
                         HERDR
                           |
                 classify / adapt
                           |
                        LiteLLM
                           |
        +------------------+------------------+
        |                  |                  |
   local-fast                           local-large
   iMac + MacBook Pro                 future 128GB node
   (two deployments, one rung)        (dormant, enabled: auto)
        |                  |                  |
        +------------------+------------------+
                           |
                    remote-open-fast
                         Groq
                           |
                    remote-open-broad
                       OpenRouter
                           |
                  remote-open-direct
           [DORMANT — Together / DeepInfra]
                           |
                proprietary-specialist
           Anthropic / OpenAI / Perplexity
                           |
                 proprietary-ceiling
                           |
                      CEILING_STALL
```

---

## Inference ladder

### 0. `deterministic`

Runs before any inference.

Responsibilities:

- sensitive-content handling
- explicit overrides
- task-shape rules
- triage
- acceptance-command discovery
- policy checks
- budget checks
- provider/model availability checks

---

### 1. `local_fast`

**Primary host:** iMac.

Use for:

- classifier
- routine coding
- bounded edits
- summarization
- extraction
- R/Python/SQL assistance
- embeddings
- low-cost agent work

Always preferred when likely to succeed.

---

### 2. `local_fast`, second deployment (formerly `local_burst`)

No longer a tier (CW02 §2.1): tiers are capability rungs, machines are
deployments. LiteLLM load-balances the MacBook inside `local_fast` with health
checks; it buys availability, not capability.

**Host:** MacBook Pro when available.

Use for:

- parallel subtasks
- second-agent review
- test generation
- specialist models
- background indexing
- medium local models

A sleeping or absent MacBook is logged as:

```text
unavailable
```

not as a model failure.

---

### 3. `local_large`

**Future host:** roughly 128 GB high-memory AI node.

Use for:

- larger coding models
- larger reasoning models
- long-context local tasks
- large open-weight MoE models
- local research synthesis
- workloads currently requiring hosted open-weight compute

Expose capability aliases rather than permanent model names:

```text
code_large
research_synthesis
```

Parity Bench determines the model assigned to each alias. The alias
vocabulary is the seven-cell set in CW02-decisions §3; the former `local/*`
namespace is retired — where a capability runs is a deployment property, not
part of the alias.

---

### 4. `remote_open`

**Recommended provider:** OpenRouter with a strict open-weight model allowlist.

Herdr chooses the model.

OpenRouter is allowed to choose an infrastructure provider for that model based on approved routing policy.

Recommended controls:

- open-weight allowlist
- provider restrictions
- no model fallback outside allowlist
- optional Zero Data Retention
- price/throughput/latency optimization
- explicit logging of provider used

Do not use an unrestricted auto-router that may select proprietary models.

---

### 5. `remote_open_direct`

**Direct-provider slot — DORMANT** (CW02 §2.1; deferred for the pilot —
OpenRouter already routes to Together endpoints; re-enable on
OpenRouter-unavailability telemetry). When enabled: Together AI.

Reasons:

- serverless per-token inference
- strong large open-model catalog
- no GPU provisioning
- useful for burst workloads
- OpenAI-compatible integration

**Optional second provider:** DeepInfra.

This provides resilience and lets Herdr compare OpenRouter aggregation against a direct inference vendor.

---

## Proprietary escalation boundary

No proprietary API should be invoked simply because it is “better.”

It must satisfy at least one of these conditions:

1. **Verified open failure** — applicable open-weight rungs were tried and failed objective acceptance criteria.
2. **Documented specialist requirement** — the capability is not yet reasonably reproduced by the open stack.
3. **Explicit user override** — the user intentionally requests the proprietary provider.

This is the policy boundary that prevents the hybrid system from quietly becoming a proprietary-first system again.

---

## 6. `proprietary_specialist`

Do not treat all proprietary providers as a single linear ladder.

Route by capability profile.

### Code / agentic implementation

Candidate proprietary ceiling:

- Anthropic API
- OpenAI API

Use only after the applicable open coding ladder fails verification.

The choice between them should be benchmarked by task class rather than hard-coded permanently.

### Research / current-information synthesis

Candidate specialist:

- Perplexity Sonar / Sonar Deep Research

Use only when the self-hosted/open research stack is insufficient for the task or when explicitly requested.

Perplexity should become a metered API capability rather than a fixed app subscription dependency.

### General high-complexity reasoning

Candidate ceiling:

- best validated proprietary reasoning model exposed through the approved API providers

Again, Herdr should own capability aliases rather than permanent model names.

---

## 7. `proprietary_ceiling`

This is the strongest proprietary path the policy allows.

It should be:

- rare
- PAYG
- budget bounded
- logged separately
- followed by deterministic verification
- measured for whether the expense actually changed failure into success

A model call is not justified merely because it produced a plausible response.

`failup.py` remains authoritative.

---

## Recommended proprietary budget model

Before dispatch, Herdr assigns a proprietary budget.

Example:

```yaml
routine_task:
  proprietary_budget: 0

high_value_code_task:
  proprietary_budget: bounded

research_task:
  proprietary_budget: bounded

explicit_override:
  proprietary_budget: user_selected
```

The important metric is not raw API spend.

It is:

```text
proprietary dollars that changed verified failure -> success
-------------------------------------------------------------
total proprietary dollars spent
```

That tells you whether the proprietary ceiling is actually earning its place.

---

## Recommended transition ladder

### Phase A — immediately

```text
local open
  -> hosted open
    -> Anthropic/OpenAI/Perplexity PAYG
```

Cancel fixed high-cost model subscriptions once the PAYG escape hatch is tested and working.

### Phase B — after adding high-memory local compute

```text
local-fast (both machines)
  -> local-large
    -> hosted open (Groq -> OpenRouter)
      -> proprietary PAYG
```

### Phase C — target state

```text
local-fast (both machines)
  -> local-large
    -> hosted open (Groq -> OpenRouter)
      -> proprietary calls approaching zero
```

At this point, the same architecture can be switched to `open_weight_only` without redesigning Herdr.

---

## Provider recommendations

### OpenRouter — primary remote aggregation layer

Recommended role:

```text
Herdr selects model
       |
OpenRouter selects allowed provider endpoint
```

Use provider routing controls for:

- price
- throughput
- latency
- fallback behavior
- ZDR constraints
- provider allow/deny lists

Do not surrender model-policy decisions to an unrestricted router.

---

### Together AI — direct hosted-open backup (dormant slot)

When enabled, serverless inference provides:

- per-token billing
- no provisioning/minimum server requirement
- broad open-model access
- coding/reasoning model availability
- OpenAI-compatible integration

This is especially useful when the workload is bursty and buying the hardware for the largest model would be irrational.

---

### Anthropic — code/reasoning PAYG ceiling

Anthropic's own Claude Code documentation supports using an LLM gateway such as LiteLLM, including centralized authentication, usage tracking, cost controls, and routing.

That fits the platform boundary well:

```text
Claude Code / Herdr
       |
     LiteLLM
       |
  Anthropic API
```

The important policy change is that Anthropic is no longer entitled to a fixed monthly subscription rung.

---

### OpenAI — alternative proprietary PAYG ceiling

Treat OpenAI as another capability provider behind LiteLLM.

Use a Herdr alias such as:

```text
proprietary/reasoning
proprietary/code
```

rather than embedding a current model name throughout the codebase.

The concrete model can then evolve without changing the routing architecture.

---

### Perplexity — specialist research PAYG

Use Sonar/Deep Research only for research tasks that justify it.

The open research stack should still run first where practical:

```text
retrieval
  -> source normalization
    -> open-weight synthesis
      -> citation verification
```

Perplexity becomes escalation for high-value research synthesis rather than an always-paid external surface.

---

## Open research path

Even in Hybrid mode, build the self-hosted research stack.

Recommended shape:

```text
query decomposition
       |
web + scholarly retrieval
       |
source normalization
       |
open-weight synthesis
       |
citation-resolution verifier
       |
verified result
```

Only then should a research task escalate to Perplexity when the open path is insufficient.

That is necessary if the long-term goal is to make proprietary research calls disappear as well.

---

## Model strategy

Use capability aliases:

```text
classifier
code_small
code_large
research_synthesis
embedding
proprietary_code
proprietary_research
```

Avoid permanent provider/model coupling. `code_medium`, `vision`, `reranker`
earn cells when telemetry shows a routing decision that needs them
(scale-mapping §4.3).

The platform should be able to replace a model without changing business logic.

---

## Storage layout

### Fast NVMe

```text
/Volumes/AI/
├── projects/
├── models/active/
├── vectorstores/
├── environments/
├── datasets-working/
├── embeddings/
└── scratch/
```

### Existing 8 TB Seagate

```text
/Volumes/AI-Archive/
├── models/archive/
├── datasets/archive/
├── snapshots/
├── completed-experiments/
└── backups/
```

---

## Recommended policy configuration

```yaml
policy_mode: hybrid

providers:
  local_fast:
    enabled: true          # two deployments: iMac + MacBook (CW02 §2.1)
  local_large:
    enabled: auto          # dormant T2 slot
  groq:
    enabled: true
    open_weight_only_for_open_rungs: true

  openrouter:
    enabled: true
    open_weight_only_for_open_rungs: true

  together:
    enabled: false         # DORMANT — re-enable on OpenRouter-unavailability telemetry
    open_weight_only_for_open_rungs: true

  deepinfra:
    enabled: optional
    open_weight_only_for_open_rungs: true

proprietary:
  enabled: true
  require_verified_open_failure: true
  allow_user_override: true
  subscription_rungs: false

on_total_failure:
  action: ceiling_stall
```

---

## `measure.py` additions

Track:

```text
local success rate
hosted-open success rate
proprietary success rate

proprietary-required tasks
proprietary-avoidable tasks

open failure -> proprietary success
open failure -> proprietary failure

API dollars per verified rescue
```

Add a report:

```text
proprietary_displacement
```

It should answer:

> If the platform were switched to `open_weight_only` today, what percentage of currently successful tasks would become ceiling stalls?

That is the most useful transition metric.

---

## Downscale rule

Evaluate proprietary providers independently.

A provider becomes removable when:

- few tasks require it after genuine open-model failures;
- open-weight models now pass the same task categories;
- another provider provides equivalent verified outcomes more economically.

This supports a progression such as:

```text
Anthropic + OpenAI + Perplexity
              |
         OpenAI + Perplexity
              |
         Perplexity only
              |
        open-weight only
```

The exact order should be determined by Herdr telemetry, not assumed in advance.

---

## Hardware-purchase rule

The future 128 GB node should be purchased when the logs demonstrate that larger locally runnable open-weight models would displace enough:

- hosted-open calls, and/or
- proprietary rescue calls

to make the hardware worthwhile.

The question is not:

> “Can a 128 GB machine run larger models?”

It can.

The useful question is:

> “How many of my verified failures disappear when a larger open-weight model becomes local?”

Parity Bench + Herdr telemetry provide that answer.

---

## Recommended operating mode

This Hybrid architecture is the recommended **transition deployment**.

It allows immediate cancellation of expensive fixed subscriptions while retaining a PAYG frontier escape hatch.

At the same time, every successful open-model substitution is measured, making it possible to move deliberately toward the Open-Weight Only configuration.

The architecture never needs to be rewritten to make that transition.

Only the policy changes:

```yaml
policy_mode: hybrid
```

becomes:

```yaml
policy_mode: open_weight_only
```

---

## End state

Open-weight models receive every task they can reasonably handle.

Local hardware handles the economically sensible share.

Hosted open-weight inference provides access to models too large to justify owning locally.

Proprietary APIs remain metered, rare, profile-specific rescue paths until the data shows they can be removed.

No fixed proprietary LLM subscription is required.

---

## Current provider references

Provider capabilities change, so these should be revalidated periodically.

- OpenRouter provider routing: https://openrouter.ai/docs/guides/routing/provider-selection
- Together AI inference overview: https://docs.together.ai/docs/inference/overview
- Together AI serverless models: https://docs.together.ai/docs/serverless/models
- Anthropic LLM gateway / LiteLLM guidance: https://docs.anthropic.com/en/docs/claude-code/llm-gateway
- OpenAI Models API: https://platform.openai.com/docs/api-reference/models
- Perplexity Sonar Deep Research: https://docs.perplexity.ai/docs/sonar/models/sonar-deep-research
