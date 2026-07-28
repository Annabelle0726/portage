# Line P roadmap — personal, current state to full implementation

*July 2026, revision 2. The fully open personal stack. iMac as the main
machine, local models on a 2TB NVMe SSD, two repos. Supersedes the first
roadmap, which predated the two-repo split, the fully open decision, and the
model roster change.*

---

## What changed in this revision

1. Line P lives in its own private repo. The engine is public and separate.
2. Policy mode is `open_weight_only`. Subscriptions retire during calibration,
   leaving a $10 hard-capped Opus rescue as the only proprietary line.
3. The local roster is three models. Gemma 4 E4B replaces the planned 4B and
   the optional vision model.
4. The stage clock is subordinate to Cairn through August 28.

---

## Repo structure

**Engine: `portage`, public under EduCloud-Ecosystem.** AGPL and Apache split.
Engine code, specs, schemas, sanitized profile examples, the deployment
template Waypoint consumes at Scale 2.

**Deployment: `portage-local`, private.** Registry, policy, compose, launcher
wrappers, version manifest, build reports, telemetry.

The boundary test for any file: if it makes a routing decision it is engine, and
if it names a machine, a key, or a personal choice it is deployment. The private
repo cannot hold engine code, which makes the config-over-code rule structural
instead of a matter of discipline. New capability gets built in the engine with
a config surface, which is the generalization pressure that keeps the two lines
from drifting.

---

## Hardware backbone

**iMac, always on, the main machine.** LiteLLM, Postgres, Herdr, the warm
steward, Qdrant, Open WebUI, SearXNG, Lane B automation. Wired Ethernet.
Authoritative for config and telemetry.

**MacBook, second worker.** A second health-checked deployment of the local
tier. Registers dynamically, drops out when asleep, logged `unavailable`.

**2TB NVMe SSD on the iMac, `/Volumes/AI/`.** `OLLAMA_MODELS` points here.

```
/Volumes/AI/
├── models/active/        pulled quants, the standing three
├── projects/             working repos
├── vectorstores/         Qdrant volume
├── environments/         uv and Docker volumes
├── datasets-working/
├── embeddings/
└── scratch/
```

Mirror the steward's quant on the internal drive for fast reload. The 8TB
archive drive, if owned, takes a nightly sync at `/Volumes/AI-Archive/`.

**Local models, the standing three:** Qwen3-Coder 7B Q4 warm on the iMac,
Gemma 4 E4B on the MacBook as the offline generalist with native vision and
function calling, and the embedder. Pins live in the registry and are
re-checked at bench time. Kimi K3 lands July 27; re-check the hosted pins that
week.

**Ollama runtime policy:** `OLLAMA_MAX_LOADED_MODELS=1` on both machines.
Keep-alive pinned (`-1`) on the iMac steward only. The MacBook swaps under LRU
and accepts the few-second cold start. macOS env vars set through
`launchctl setenv`, then the menubar app restarted.

---

## The scheduling rule

Cairn owns the build effort until August 28, 2026. GitHub Classroom retires
that day, and the adopter letters that gate PESOSE depend on a pilot that
actually runs. Line P work through S2 is session-sized and parallel, and it
never takes a day Cairn needs. The calibration window opens after the Cairn
pilot is deployed, which also gives the measurement a cleaner baseline, since
the machine is not being reconfigured underneath it.

---

## Stages

### S0 — Split and foundation. Sessions across August 2026, parallel to Cairn.

CC-P0 v2 runs first: restructure the engine repo to a src layout, push it, and
extract `portage-local`. The push in step 1 ends the single-disk risk carried
through two status reports.

Then HB-0: LiteLLM on the pinned stable image, registry-rendered config, the
two-Ollama health-checked local tier, per-model tool-call smoke tests, and
measured `load_duration` for every local model on both machines.

Then HB-1: Aider, Open WebUI with SearXNG, OpenHands with per-agent tool
scoping, and a virtual key per frontend with spend tags.

**Exit:** both repos pushed and clean of hostnames and keys, all three
frontends round-tripping through the proxy with spend attributed, tool-calling
verified per local model.

### S1 — Verification, budgets, and the baseline. September 2026.

HB-2, authored against the S0 reports. failup.py on the CC-P1 verifier
contract, the five-class failure taxonomy, a hard two-retry cap per class with
structured failure output returned to the failing stage only, measure.py with
per-class priors, three-price accounting, and per-tier recall and CNA logged
from the first verdict. The Opus rescue key: $10 over 30 days, a 24-hour
window, no fallbacks attached, and a confirm gate behind a verified open
failure.

The baseline runs here and only here. Send the representative task set through
native Claude Code and Codex and through Herdr, paired, while the
subscriptions still exist. This measurement cannot be recovered after
cancellation, and it is what makes the cutover decision in S3 evidence rather
than preference.

**Exit:** a seeded hard task escalates and stalls correctly. The 429 fires on
the rescue cap. The priors table populates from real work. The paired baseline
is recorded.

### S2 — Cache affinity and memory. October 2026.

HB-3. `session_id` sticky routing on cache-sensitive flows, the effective-cost
model with the DeepSeek cache-lag tolerance, and verified `cached_tokens`
greater than zero. Qdrant with the MCP memory server, deterministic store and
recall triggers rather than model discretion, one embedding model through the
proxy, all three frontends reading one memory.

**Exit:** a fact stored from Aider is retrievable in Open WebUI. A warm session
shows the cached rate.

### S3 — Calibration and the open cutover. 60 to 90 days, October 2026 to January 2027.

Daily work runs through the stack. The dashboards accumulate: routing funnel,
verified success by serving configuration, cost per verified task, rescue rate,
and the hardware case.

The cutover is staged inside this window rather than executed on one day.
Cancel ChatGPT Plus and Claude Pro once the paired baseline shows the open
ladder holds on your task distribution. Perplexity retires when the science
lane's citation verifier ships. Each cancellation is a dated decision with the
evidence attached, and each is reversible for one billing cycle if the numbers
disagree.

Spend during the window: $40 in subscriptions falling to $0, plus $20 to $45
hosted-open, plus $0 to $10 rescue.

**Exit:** subscriptions at zero. measure.py answers which classes still reach
the rescue line and how often.

### S4 — Loop hardening. January to March 2027.

HB-4 opens if volume justifies it: the LinUCB bandit over the prior table,
distill.py with the collapse guards, an exploration fraction, and rolling
windows.

The thinking-planner trial runs here, using Gemma 4's own thinking mode as a
gated decomposer for classes whose local pass-rate sits below 0.9, with a
thinking-token cap and think-block stripping before the executor. It promotes
to a standing tier only if it lifts a class to 0.9 inside the latency budget. A
dedicated reasoning model earns a registry entry only if Gemma's thinking
proves too shallow.

If per-tier recall on the non-cheap tiers approaches zero, stop, rebalance the
labels, and keep the statistical priors.

**Exit:** the router starts each class at its learned floor with no
quality-gate violations.

### S5 — Full implementation. From spring 2027.

The definition of done for Line P:

1. Every task routes through Herdr. No surface talks to a provider directly.
2. Zero subscriptions. The rescue line is capped, confirm-gated, and rarely
   fires. The rescue rate is the displacement metric and it stays low.
3. The science lane, metasearch plus the citation verifier, carries research.
4. OpenHands carries the Cowork role on Lane B with the artifact-existence
   verifier profile and per-agent tool scoping.
5. The learning loop runs with collapse guards green.
6. The hardware decision is made by the dashboard rather than by appetite. If
   the trigger fired, a 128GB-class node (Strix Halo on personal money, DGX
   Spark on grant money) joins as one more LiteLLM deployment and the workhorse
   moves local. If it did not fire, hosted-open continues and the money stays.

**Steady-state spend:** $20 to $45 hosted-open, $0 to $10 rescue, power. Down
from $140.

---

## Standing rules

- The registry is the single source. Config is rendered, never hand-edited, and
  it lives in git.
- The private repo holds no engine code. New capability is built in the engine
  with a config surface.
- The quality gate is absolute. A cost win that drops verified success reverts.
- One warm model per machine until a machine crosses 24GB of unified memory.
- Cairn's clock has priority through August 28, 2026.
- Nothing here reaches EduCloud except through the inclusion test, as config
  against the shared engine, never as code.
