# Local Platform — Open-Weight Only

*Recommended Scale 1 architecture for eliminating proprietary-model dependence while retaining local and hosted open-weight inference.*

> **Revised 2026-07-28 per CW02-decisions.md §3 (dormant-slot synthesis).**
> local_burst is no longer a tier — the MacBook is a second health-checked
> deployment of `local_fast`. The freed T2 slot holds `local_large` (dormant,
> enabled: auto). Groq enters at T3 (`remote_open_fast`); Together is a
> defined-but-dormant T5. Capability aliases are the seven-cell set in CW02 §3.

## Purpose

This mode is the long-term sovereignty target.

The platform keeps the existing Herdr + LiteLLM routing spine, deterministic triage, prompt adaptation, `failup.py` verification, plan-first decomposition, and `measure.py` telemetry. The policy boundary changes: **no proprietary model is ever eligible for inference**.

Hosted inference is still allowed. The requirement is that the model weights are publicly downloadable under an approved license. Remote providers supply compute, not a closed intellectual dependency.

---

## Core principle

> **Open weights first, local whenever practical, hosted when economically rational, proprietary inference never.**

The goal is not “every token must be generated inside the house.”

The goal is:

> **100% of normal model inference is served by approved open-weight models, with local hardware handling the economically sensible share and metered remote GPUs handling workloads that exceed local capacity.**

---

## Scale 1 footprint

### Existing hardware

- **iMac** — always-on routing and local inference host
- **MacBook Pro** — opportunistic second local inference worker
- **2 TB NVMe** — fast active AI workspace, models, vector stores, environments, and working datasets
- **8 TB Seagate** — bulk storage, model archive, dataset archive, and backup tier

### Future hardware

- **High-memory local AI node** — target roughly 128 GB of model-accessible memory
- Added only when Herdr telemetry shows that local model capacity is a recurring constraint

---

## Recommended topology

```text
                         HERDR
                           |
                 classify / adapt
                           |
                        LiteLLM
                           |
        +------------------+-------------------+
        |                  |                   |
   local-fast                            local-large
   iMac + MacBook Pro                  future 128GB node
   (two deployments, one rung)         (dormant, enabled: auto)
        |                  |                   |
        +------------------+-------------------+
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
                       CEILING_STALL
```

There is no Claude, proprietary GPT, Gemini, Sonar, or other closed-model fallback.

---

## Inference ladder

### 0. `deterministic`

No model call yet.

Responsibilities:

- sensitive-content pinning
- explicit overrides
- task-shape rules
- triage for underspecified requests
- lint/test command discovery
- routing-policy enforcement
- model-license allowlist checks

This remains the cheapest and most reliable rung.

---

### 1. `local_fast`

**Primary host:** always-on iMac.

Purpose:

- task classification
- prompt adaptation support
- bounded code edits
- routine R/Python/SQL work
- summarization
- extraction
- lightweight code review
- embeddings
- small specialist models
- inexpensive first-pass agent work

This tier should favor models that remain responsive on the iMac rather than chasing maximum parameter count.

Recommended policy:

```yaml
capability: local_fast
availability: required
cost_class: local
privacy: local
```

---

### 2. `local_fast`, second deployment (formerly `local_burst`)

**Host:** MacBook Pro when online.

No longer a tier (CW02 §2.1): tiers are capability rungs, machines are
deployments. The MacBook runs the same models as the iMac, so escalating to it
buys no capability — LiteLLM load-balances it inside `local_fast` with health
checks. It is not extra RAM for the iMac; it is a second inference worker.

Best uses:

- parallel subtasks
- independent code review
- test generation
- secondary-agent work
- specialist models
- background indexing
- larger local models when the MacBook itself has more unified memory

If the MacBook is asleep or off-network:

```text
result = unavailable
```

not:

```text
result = model_failed
```

This distinction is essential so `measure.py` does not interpret missing hardware as a model-quality failure.

---

### 3. `local_large`

**Future host:** high-memory local AI node.

Recommended target:

- roughly **128 GB** of model-accessible memory
- fast local NVMe
- high-speed Ethernet preferred
- headless operation
- Tailscale/SSH administration
- Ollama, llama.cpp, or another approved local inference runtime behind LiteLLM

This tier should expose **capability aliases**, not hard-coded permanent model names:

```text
code_large
research_synthesis
```

The model behind each alias should be selected by Parity Bench results.
The alias vocabulary is the seven-cell set in CW02-decisions §3; the former
`local/*` namespace is retired — where a capability runs is a deployment
property, not part of the alias.

The purpose of this node is to make substantially larger open-weight models locally available without replacing the iMac as the normal workstation.

---

### 4. `remote_open`

**Recommended provider:** OpenRouter.

Herdr selects the model. OpenRouter selects an allowed infrastructure provider for that model.

That separation is important:

```text
Herdr:
  "Use approved open-weight model X."

OpenRouter:
  "Which approved provider should serve model X?"
```

Do **not** use a general-purpose auto-router that can introduce proprietary models.

Recommended controls:

- hard model allowlist
- model-license metadata stored in Herdr
- provider allow/deny lists
- optional Zero Data Retention enforcement
- explicit quantization policy where relevant
- price/throughput/latency routing only after the model has been selected
- no fallback to a model outside the allowlist

Example policy:

```yaml
remote_open:
  require_open_weight: true
  allow_unclassified_models: false
  proprietary_fallback: false
  provider_fallbacks: true
```

OpenRouter supports provider ordering/restriction, fallback control, ZDR filtering, quantization filtering, and sorting by price, throughput, or latency.

---

### 5. `remote_open_direct`

Maintain at least one direct hosted-open provider as a resilience path.

### Direct-provider slot — DORMANT (Together AI when enabled)

> Deferred for the pilot (CW02 §2.1; scale-mapping §4.1): OpenRouter already
> routes to Together endpoints. Re-enable on OpenRouter-unavailability
> telemetry. When enabled, Together AI is the recommended primary because:

Why:

- serverless per-token inference
- no GPU provisioning required
- strong open-model catalog
- supports large coding/reasoning models
- OpenAI-compatible API
- useful for bursty workloads
- can move to dedicated endpoints later without changing the basic application interface

### Recommended secondary option: DeepInfra

Useful as:

- an additional open-model catalog
- alternate pricing path
- redundancy against OpenRouter/Together availability issues

The platform should benchmark the same model across providers before assuming the cheapest listed endpoint is the best operational choice.

---

## Model strategy

Do not build the architecture around a single “Claude replacement model.”

Use role-specific capability aliases.

```text
classifier
code_small
code_large
research_synthesis
embedding
```

Herdr then maps each capability to the currently best validated model.
Five open aliases here; `proprietary_code` / `proprietary_research` exist only
in hybrid mode (specs/11). `code_medium`, `vision`, `reranker` earn cells when
telemetry shows a routing decision that needs them (scale-mapping §4.3).

Candidate families should be selected from current downloadable open-weight models such as:

- Qwen
- DeepSeek
- Kimi/Moonshot open-weight releases
- GLM/Z.ai open-weight releases
- GPT-OSS
- Llama
- Gemma
- Mistral-family open models

The exact winner is intentionally not permanent.

**Parity Bench decides.**

---

## Recommended coding path

```text
task
 |
deterministic triage
 |
local_fast
 |
verified?
 +-- yes --> complete
 |
 no
 |
local_fast #2 (MacBook) or local_large
 |
verified?
 +-- yes --> complete
 |
 no
 |
remote_open
 |
verified?
 +-- yes --> complete
 |
 no
 |
remote_open_direct
 |
verified?
 +-- yes --> complete
 |
 no
 |
decompose / retry
 |
CEILING_STALL
```

`failup.py` remains authoritative.

The model's statement that it succeeded is never sufficient.

---

## Ceiling behavior

The final open-weight failure must **not** silently cross into proprietary inference.

Instead:

```text
remote_open_direct
        |
      failure
        |
decompose task
        |
retry eligible open tiers
        |
      failure
        |
   CEILING_STALL
```

Log:

- task profile
- model attempts
- local vs. hosted
- context size
- acceptance command
- verifier result
- availability failures
- quality failures
- total open-inference cost
- best prior Parity Bench comparison

This makes the remaining open-model gap measurable.

---

## Research profile without Perplexity

The Science lane must replace Perplexity-style research with an open stack.

Recommended flow:

```text
query decomposition
       |
web / scholarly retrieval
       |
source normalization
       |
open-weight synthesis
       |
citation extraction
       |
citation-resolution verifier
       |
final answer
```

A self-hosted metasearch layer such as **SearXNG** is appropriate for general web discovery, supplemented by direct scholarly APIs/indexes for academic work.

The model must never be trusted to invent citations.

Every cited source must have been retrieved and validated by the citation-resolution verifier.

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

The NVMe is the workbench.

The 8 TB Seagate is the warehouse.

---

## Hardware-purchase rule

Do not buy the 128 GB node merely because larger models exist.

Buy it when Herdr data shows:

1. a material percentage of tasks fail because the best local model is too small;
2. hosted open-weight models solve those same tasks;
3. the expected local inference volume makes hardware economically preferable;
4. the quality gain from the larger open model is demonstrated by the personal Parity Bench.

This turns hardware acquisition into a measured capacity decision rather than a benchmark-driven guess.

---

## Recommended policy configuration

```yaml
policy_mode: open_weight_only

providers:
  local_fast:
    enabled: true          # two deployments: iMac + MacBook (CW02 §2.1)
  local_large:
    enabled: auto          # dormant T2 slot
  groq:
    enabled: true
    open_weight_only: true
  openrouter:
    enabled: true
    open_weight_only: true
  together:
    enabled: true
    open_weight_only: true
  deepinfra:
    enabled: optional
    open_weight_only: true

proprietary:
  enabled: false

on_open_ceiling_failure:
  action: ceiling_stall
```

---

## Success metrics

Track at minimum:

```text
% solved by local_fast
% solved by the MacBook deployment (local_fast #2)
% solved by local_large
% solved by hosted open-weight
% ending in ceiling stall

cost per verified successful task
median latency by rung
tokens / context by rung
unavailable vs. not-good-enough failures
```

The critical metric is:

> **What percentage of real tasks receive a verified successful result without proprietary inference?**

---

## End state

The platform runs open-weight models locally whenever practical, rents remote GPU inference only when larger open models are justified, and treats a model-quality ceiling as measurable evidence rather than permission to invoke a closed model.

No recurring LLM subscription is required.

No proprietary model dependency remains.

---

## Current provider references

Provider capabilities change, so these should be revalidated periodically.

- OpenRouter provider routing: https://openrouter.ai/docs/guides/routing/provider-selection
- Together AI inference overview: https://docs.together.ai/docs/inference/overview
- Together AI serverless models: https://docs.together.ai/docs/serverless/models
- Together AI recommended models: https://docs.together.ai/docs/inference/recommended-models
