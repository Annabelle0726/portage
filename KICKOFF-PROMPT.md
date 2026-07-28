# Kickoff prompt for Claude Code

> **RETIRED (CW02 §4, 2026-07-28).** LINE-P-ROADMAP.md (S0–S5) governs
> staging and REVISION-PLAN §9 maps the old phase numbers. Retained for the
> constraint list until the HB-0/HB-1 prompts land in-repo; do not start
> sessions from this file.

> **July 2026 update.** `LINE-P-ROADMAP.md` (S0–S5) governs staging; S0 runs
> on the authored HB-0/HB-1 prompts, which are **not yet in this repo** —
> land them first. Until they land, this file remains the session brief; its
> constraints and acceptance still apply, with the rescue-line and
> calibration changes noted at the top of `REVISION-PLAN.md`.

The repo exists and is under git; **Phases 0 and 1 are done** (`uv run ruff check`
and `uv run pytest` green, versions pinned, LiteLLM spine smoke-tested, and Claude
Code confirmed to talk to LiteLLM directly — see `docs/phase-1-findings.md`). The
current track is the **Scale-1 transition to an open-first ladder with a PAYG
ceiling** — `REVISION-PLAN.md`, Phase 6a.

Open Claude Code in the repo and paste the prompt below. Start in **plan mode** —
produce a plan and a small diff, not a large build.

---

## Current session prompt (copy from here)

```
You are picking up a partly-built project. Read, in this order: README.md,
PLATFORM.md, REVISION-PLAN.md, then docs/BUILD-PLAN.md. PROJECT.md and docs/specs/00-11 are
the reasoning record — consult them when you need to know *why*, don't read them
all up front. docs/specs/10 (open-weight-only) and docs/specs/11 (hybrid open-first + PAYG)
are the normative Scale-1 architecture; docs/specs/03 is HISTORICAL (the Claude-only
pilot), retained only as Parity Bench baseline analysis.

Operating constraints for every session on this repo:

1. BUILD AS LITTLE AS POSSIBLE. docs/BUILD-PLAN.md §2 records which components were
   deliberately replaced by existing tools (LiteLLM, Herdr's plugin system,
   native Claude Code features). The hosted-open tiers (OpenRouter, Together,
   DeepInfra) and the PAYG ceiling are CONFIG, not code — LiteLLM deployments,
   not a custom aggregator. If you think something needs custom code, first say
   what existing tool you checked and why it doesn't fit.

2. TREAT UNVERIFIED EXTERNAL INVOCATIONS AS UNVERIFIED. `claude -p` direct-to-
   LiteLLM is RESOLVED (Phase 1). Still unverified and not to be built on until
   you run them: the `codex` CLI flags, the OpenRouter open-weight-allowlist +
   provider-restriction syntax in a LiteLLM deployment, and the Herdr plugin API.
   When you find a discrepancy, fix the code AND record it in
   KNOWN_GOOD_VERSIONS.md.

3. NEVER REGRESS THE STANDING RULES in docs/BUILD-PLAN.md §6. The load-bearing ones:
   sensitive data is pinned by config absence (policy_mode: sovereign), never by
   a runtime check, model judgment, or a provider's ZDR/retention promise; the
   verifier decides pass/fail, never the model's self-report; the proprietary
   PAYG rung is reached only on verified open failure, a documented specialist
   need, or an explicit override — never because it would perform better; no
   fan-out orchestration; every efficiency claim must survive the quality gate
   in measure.py; `unavailable` (a rung offline) is never scored as a failure.

4. WHEN YOU HIT AN OPEN QUESTION (docs/BUILD-PLAN.md §7), stop and investigate rather
   than assuming. Report what you found.

SCOPE FOR THIS SESSION — Phase 6a (Scale-1 transition), plus its two coupled
prerequisites. Do not start Phase 6 (EduCloud/sovereign) or Phase 7+.

First, confirm where the repo actually is. Phase 6a's acceptance depends on two
pieces from earlier phases — if they aren't done, do them first, in this session:

  a. (Phase 2) failup.py: split `unavailable` from `model_failed`. A
     connection-refused / timeout on a rung logs `unavailable` and skips to the
     next rung; only a verifier failure logs `model_failed` and counts as a real
     escalation. Cover it with a stub-runner test (a fake script that is
     offline / fails / passes on command) — zero tokens, no network.
  b. (Phase 4) measure.py: add the `proprietary_displacement` report (of
     verified successes, the % that would become ceiling-stalls if the PAYG rung
     were removed) and rescue efficiency (proprietary $ that flipped
     failure→success ÷ total proprietary $). Prove both from synthetic fixture
     logs.

Then Phase 6a proper (REVISION-PLAN.md §5):
  1. Extend the LiteLLM config into `litellm.hybrid.yaml`: an OpenRouter
     deployment group with a HARD open-weight allowlist (a non-allowlisted model
     is simply not a deployment) + provider routing by price/throughput/latency
     + optional ZDR; a Together direct group (DeepInfra optional); cooldowns +
     per-group budgets. Keep `litellm.sensitive.yaml` local-only (unchanged).
  2. Wire Anthropic/OpenAI (and Perplexity Sonar for the Science lane) as the
     PAYG ceiling behind LiteLLM budget caps, gated by a per-task-class
     `proprietary_budget` (routine = 0). The allowlist manifest lives in
     plugins/herdr-meters/models.json (license + quantization floor per model).
  3. Do NOT cancel any subscription yet — the Parity Bench baseline (arm A4,
     native Claude Code on Max) needs it live. Cancellation is a later step,
     recorded as a cost-accounting epoch, only after the 12-task bench cut runs.

Acceptance for this session:
  - uv run pytest green (incl. the new unavailable-vs-failed and displacement
    fixtures), no network, no tokens.
  - A curl through LiteLLM reaches an allowlisted model via OpenRouter; a
    non-allowlisted model name fails closed (404), not silently substituted.
  - Killing OpenRouter fails over to Together.
  - The PAYG rung refuses dispatch for a task class with proprietary_budget 0 and
    logs its spend separately when allowed.
  - A short findings note (append to docs/phase-1-findings.md or a new
    docs/phase-6a-findings.md) covering the allowlist-enforcement syntax you
    verified and anything drafted that turned out wrong.

Ask me before: deleting anything outside the superseded list in docs/BUILD-PLAN.md §2,
adding a dependency, cancelling any subscription, or spending real tokens on a
paid meter (the allowlist-enforcement curl can use a single cheap open-weight
call — confirm the budget with me first).
```

## Later sessions

After Phase 6a lands and the 12-task bench baseline (A1 vs A4) is captured,
the remaining track is: subscription cancellation (cost-accounting epoch) →
Phase 5 maintenance rails wired into CI → Phase 6 EduCloud generalization
(sovereign endpoints provisioned by Outfitter; per-lane policy_mode posture) →
Phases 7-10 from PLATFORM.md §9 (lane verifiers + open research stack, Postgres/
Langfuse, bench.py, adaptive router + steward). One phase per session; always
end with a findings note when the phase involved investigation. The flip from
`hybrid` to `open_weight_only` (docs/specs/10) is a config-variant swap, triggered by
the `proprietary_displacement` metric — never by calendar.
