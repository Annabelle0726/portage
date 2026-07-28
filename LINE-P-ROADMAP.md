# Line P roadmap — personal, current state to full implementation

*July 2026. The fully open personal stack, iMac as the main machine, local
models on a 2TB NVMe SSD. Scales from the authored HB-0 prompt to a
zero-subscription full implementation. Timeline anchors on the 60 to 90 day
calibration window.*

---

## Hardware backbone

**iMac, always on, the main machine.** Runs LiteLLM, Postgres, Herdr, the warm
steward, Qdrant, Open WebUI, SearXNG, and Lane B automation. Wired Ethernet.
Authoritative for config and telemetry.

**MacBook, second worker.** A second health-checked deployment of the local
tier. Registers dynamically, drops out when asleep, logged `unavailable`.

**2TB NVMe SSD on the iMac, `/Volumes/AI/`.** `OLLAMA_MODELS` points here.

```
/Volumes/AI/
├── models/active/        pulled quants, the four pilot models
├── projects/             working repos
├── vectorstores/         Qdrant volume
├── environments/         uv and Docker volumes
├── datasets-working/
├── embeddings/
└── scratch/
```

Mirror the warm steward's quant on the internal drive for fast reload. The 8TB
archive drive, if owned, takes a nightly sync at `/Volumes/AI-Archive/`.

**Local models, the standing four:** Qwen3-Coder 7B Q4 warm on the iMac, a 4B
on the MacBook for offline work, the embedder, an optional small vision model.
Pins live in the registry, re-checked at bench time. Kimi K3 lands July 27;
re-check the hosted pins that week.

---

## Stages

### S0 — Foundation. Weeks 1 to 2, early August 2026.
HB-0 and HB-1 as authored. Gateway on the pinned stable image, registry-rendered
config, two-Ollama health-checked local tier, tool-call smoke tests, then
Aider, Open WebUI with SearXNG, and OpenHands wired with per-frontend keys and
spend tags.
**Exit:** all three frontends round-trip through the proxy with spend
attributed. Tool-calling verified per local model.

### S1 — Verification and budgets. Week 3.
HB-2, authored against the S0 reports. failup.py on the CC-P1 verifier
contract, the five-class failure taxonomy, measure.py with per-class priors,
three-price accounting, per-tier recall and CNA logging from the first
verdict. The Opus rescue key: $10/30d wall, 24h window, no fallbacks, confirm
gate behind a verified open failure.
**Exit:** a seeded hard task escalates and stalls correctly. The 429 fires on
the rescue cap. The priors table populates from real work.

### S2 — Cache affinity and memory. Week 4.
HB-3. `session_id` sticky routing on cache-sensitive flows, the effective-cost
model with the DeepSeek cache-lag tolerance, verified `cached_tokens` > 0.
Qdrant plus the MCP memory server, one embedding model through the proxy, all
three frontends reading one memory.
**Exit:** a fact stored from Aider is retrievable in Open WebUI. A warm Kimi
session shows the cached rate.

### S3 — Calibration. 60 to 90 days, September to November 2026.
Daily work runs through the stack. The dashboards accumulate: routing funnel,
verified success by serving configuration, cost per verified task,
displacement, the hardware case. Temporary subscriptions ride along as
comparison arms: Claude Pro for native Claude Code pairing, Perplexity
Education Pro for the research arm. Spend envelope $60 to $80, hard ceiling
$100.
**Exit:** measure.py answers three questions with evidence. Whether Claude Pro
earns its $20 against the rescue line. Whether the science lane can retire
Perplexity. Whether the hardware-case dashboard shows a workload a local node
would absorb.

### S4 — Downscale and loop hardening. December 2026 to February 2027.
Cut what the evidence says to cut. Expected end state: zero fixed
subscriptions, the $10 rescue cap as the only proprietary line, spend $20 to
$45. Then HB-4 opens if volume justifies it: the LinUCB bandit over the prior
table, distill.py with the collapse guards, exploration fraction, rolling
windows. If per-tier recall on non-cheap tiers approaches zero, stop, rebalance,
and keep the statistical priors.
**Exit:** subscriptions at zero or justified by a number. The router starts
each class at its learned floor without quality-gate violations.

### S5 — Full implementation. From spring 2027.
The definition of done for Line P:

1. Every task routes through Herdr. No surface talks to a provider directly.
2. Zero fixed subscriptions. The rescue line is capped, confirm-gated, and
   rarely fires; the rescue rate is the displacement metric and it is low.
3. The science lane, metasearch plus the citation verifier, carries research.
4. OpenHands carries the Cowork role on Lane B with the artifact-existence
   verifier profile.
5. The learning loop runs with collapse guards green.
6. The hardware decision is made by the dashboard, not by appetite. If the
   trigger fired, a 128GB-class node (Strix Halo personal money, DGX Spark
   grant money) joins as one more LiteLLM deployment and the workhorse moves
   local. If it did not fire, hosted-open continues and the money stays.

**Steady-state spend:** $20 to $45 hosted-open, $0 to $10 rescue, power. Down
from $140.

---

## Standing rules

- Config as git. Registry as single source. Pins deliberate.
- The quality gate is absolute: a cost win that drops verified success reverts.
- Nothing here migrates to EduCloud except through the inclusion test, as
  config against the shared engine, never as code.
