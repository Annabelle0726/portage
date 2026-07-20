# 07 — Project overview & landscape research handoff

## Overview

**What it is.** A quota- and sovereignty-aware routing layer for coding agents.
The problem it solves: once you're running multiple AI subscriptions and tools
(Claude Max, ChatGPT Plus/Codex, Perplexity Pro, local open-weight models, and —
at institutional scale — sovereign HPC), the scarce resource stops being
per-token dollars and becomes **subscription quota and allocation**, and the
friction stops being "which model is smartest" and becomes "which meter has
headroom, and did I specify this well enough to not waste a turn."

**The core mechanisms** (each is the minimum custom code needed, everything else
is configuration of existing tools — see `HANDOFF.md` §2 for the full
buy-vs-build resolution):

1. **Tiered routing, free-before-metered, scarce-last.** Local open-weight →
   sovereign/institutional compute → subscription quota → paid API. Sensitive
   data is pinned to local by config absence, not model judgment.
2. **A deterministic fail-up guard.** A task runs at a tier; a *runner* (tests +
   lint + non-empty diff) decides pass/fail, never the model's self-report. On
   failure it escalates one tier up. This is what lets cheap tiers be used
   confidently — a misroute self-corrects instead of shipping a wrong answer.
3. **Plan-first decomposition for large tasks**, with each subtask carrying a
   *runnable* acceptance check (not prose) and a human-approval gate on the plan
   itself, because nothing verifies a plan except a human.
4. **A local, free classifier that triages before it routes** — catching
   underspecified tasks ("fix it") before they waste an expensive turn, then
   picking provider + model + effort. Uncertainty escalates up, never down; the
   classifier asks clarifying questions, it never silently rewrites intent.
5. **A measurement harness** that reports quota saved *and* whether the
   ceiling-stall (failure) rate rose — an efficiency claim that ignores quality
   doesn't count, and the tool refuses to let you claim one that does.
6. **A Herdr plugin (`herdr-meters`)** putting all of this inside the terminal
   multiplexer already in use, rather than a separate app: cross-vendor
   dispatch, a status board, and manual rate-limit marking.

**Why it might be worth publishing, not just using personally:** the research
done earlier in this project found that commercial routers (LiteLLM, Portkey,
OpenRouter) optimize per-token cost, and even the newer subscription-quota-aware
routers (llm-router, 9router, OmniRoute) treat "free" as commercial-free-tier or
local — none of them add institutional/research compute (NSF ACCESS, Jetstream2,
campus HPC) as a sovereign, zero-marginal-cost tier. That fusion, plus the
runnable-acceptance-check governance and the honest measurement layer, is the
candidate novelty. It's a mid-2026 snapshot and time-sensitive — see `PROJECT.md`.

**Where it stands:** fully specified (`specs/00`–`06`), drafted in Python, and
just handed to Claude Code to build for real (`HANDOFF.md`) — with an explicit
instruction to replace hand-rolled pieces with existing tools wherever possible
(LiteLLM instead of a custom broker, for instance, was one correction already
made). This document exists to push that "don't rebuild what exists" instinct
one level further: a fresh outside pass on the current landscape before more
code gets written.

---

## Deep research prompt (for Perplexity)

Copy everything below into Perplexity, in Deep Research mode.

```
I'm building a quota- and sovereignty-aware routing layer for coding agents
(Claude Code, Codex CLI, local open-weight models via Ollama, and institutional/
sovereign HPC inference via NSF ACCESS / Jetstream2). The design already commits
to using LiteLLM as the routing/proxy spine (cooldowns, ordered failover,
Ollama + Anthropic + OpenAI-compatible endpoints, spend logging) rather than a
custom broker. I need a current landscape survey to find anything else I should
adopt instead of building custom, and to sanity-check what's left as genuinely
custom.

For EACH of the following six components, tell me: (a) whether a mature
open-source project already does this well, (b) its license, activity level
(commits/releases in the last 3 months), and adoption signals (stars, notable
users), (c) how it would integrate with a LiteLLM-based proxy layer and Claude
Code / Codex CLI, and (d) whether it's a genuinely better fit than building the
~50-200 line custom version described, or whether the custom version is
justified. Cite specific repos, docs, and dates — I need current (mid-to-late
2026) information, not general background, since this space moves weekly.

1. DETERMINISTIC ACCEPTANCE / VERIFICATION GATES FOR AGENT PIPELINES.
   I have a "fail-up guard": a task runs at a model tier, a deterministic runner
   (tests pass + lint clean + non-empty diff) decides pass/fail — never the
   model's self-report — and on failure it escalates to a stronger tier and
   retries. Is there an existing open-source library that provides this
   "verifier decides, not the model" pattern as a reusable primitive, ideally
   with tier/model escalation built in? I'm aware of DSPy Assertions, CrewAI
   function guardrails, ScopeGate, and AutoPyVerifier as of mid-2026 — has
   anything more complete shipped since, and does any of them support
   automatic model/effort escalation on failure specifically (not just
   retry-same-model)?

2. PLAN-FIRST TASK DECOMPOSITION WITH RUNNABLE PER-SUBTASK ACCEPTANCE CHECKS.
   I have a driver that has an LLM emit a structured plan (ordered subtasks,
   dependencies, a RUNNABLE shell-command acceptance check per subtask, and a
   runnable integration check), requires human approval of the plan before any
   execution, then runs each subtask under the fail-up guard. Do any of the
   current spec-driven-development tools (GitHub Spec Kit, AWS Kiro, cc-sdd,
   OpenSpec, BMAD, or others that have emerged since) support RUNNABLE,
   machine-checked per-subtask acceptance criteria specifically — not just
   prose specs a human reads? Which comes closest, and is it worth adopting
   over the custom ~150-line version?

3. LOCAL, FREE, TASK-DIFFICULTY / INTENT CLASSIFIERS FOR ROUTING CODING TASKS.
   I have a small local model (Ollama, 7B class) that triages a task BEFORE
   routing: it flags underspecified requests with a clarifying question rather
   than dispatching them, then picks a target (provider + model + effort) from
   a small catalog, with deterministic keyword rules for sensitive-data pins
   and explicit overrides that run before the model and can't be overridden by
   it. Is there an existing open-source semantic router or intent-classifier
   project built for this "triage then route, local-first" use case in coding
   agents specifically (not general RAG/chatbot routing)? How mature is it,
   and does it support a fine-grained target catalog with per-target effort
   levels the way I need?

4. HERDR PLUGIN ECOSYSTEM: CROSS-VENDOR METER/QUOTA AWARENESS.
   Herdr (https://herdr.dev) is a terminal multiplexer for coding agents with
   a plugin system (any argv command, JSON manifest, full CLI/socket API
   access, published via a GitHub topic). Its marketplace had 150+ plugins as
   of mid-2026. Has anyone published a Herdr plugin that does cross-vendor
   subscription/quota awareness — tracking rate-limit state across multiple
   agent CLIs (Claude Code, Codex, etc.) in one pane and dispatching tasks to
   whichever has headroom? If nothing exists, say so explicitly and note the
   closest adjacent plugin.

5. MEASUREMENT / EVALUATION OF LLM ROUTING DECISIONS (EFFICIENCY vs QUALITY).
   I have a small harness that logs every routing/escalation attempt, groups
   them by task, and reports (a) how far down a cost ladder tasks resolved,
   (b) escalation rate, and (c) "ceiling-stall rate" — tasks that failed even
   at the top tier — with an explicit rule that an efficiency win doesn't count
   if the stall rate rose. Is there an existing open-source eval/observability
   framework (LangSmith, Langfuse, Helicone, or others) that already computes
   this specific quality-adjusted-efficiency metric for a routing/escalation
   system, rather than just generic cost/latency dashboards? 

6. SOVEREIGN / INSTITUTIONAL HPC INFERENCE EXPOSURE.
   STREAM (arXiv 2606.13968, `hpc-as-api`/`streamrelay`) and Argonne's FIRST
   were, as of mid-2026, the closest tools for exposing HPC-hosted open-weight
   models as OpenAI-compatible endpoints reachable by a router like LiteLLM.
   What's the current status of these projects (releases, adoption, known
   limitations), and has anything more turnkey emerged for wrapping an NSF
   ACCESS / Jetstream2-style inference service as a LiteLLM deployment target,
   including handling of network/firewall gating and auth?

FINALLY: give me a single build-vs-adopt table across all six components with
your recommendation, and flag anything time-sensitive — e.g., if a commercial
or open-source router has closed the "subscription-quota + sovereign-compute"
gap since mid-2026, since that changes whether this project is still novel.
```
