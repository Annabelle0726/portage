# 02 — Local & EduCloud versions

> **Roster banner — 2026-08-04.** The provider ladder and hosted-model
> occupants below are **superseded by `CW-04-model-roster.md`**
> (`portage-local/docs/reports/`). CW-04 §2.2 removes OpenRouter from the
> ladder entirely — it becomes a non-routable failover path, not a rung — and
> §2.3 changes the occupant of every hosted tier. The rewrite that lands this
> is CW-03 group 4, which **has not been performed**; CW-02 §6 pins it to a
> top-model gate review. Do not act on the provider content below without
> reading CW-04 and `CW04-HB0-drift.md` first.

> **Updated 2026-07 (Scale-1 transition).** The ladders below are restated in the
> unified vocabulary of `docs/specs/10`–`11` and `REVISION-PLAN.md`: rungs are
> `local_fast → [local_large] → remote_open_fast (Groq) → remote_open_broad
> (OpenRouter) → [remote_open_direct] → proprietary` — dormant slots
> bracketed; sovereign is an EduCloud-profile insert (CW02-decisions.md §3), and the version you run is a
> **policy_mode** (`open_weight_only` / `hybrid` / `sovereign`) selected by which
> LiteLLM config variant is loaded. The old "copy a config.json" mechanism is
> superseded by config-variant selection; the fail-up guard still reads
> `--tiers`. The core skeleton (two lanes, fail-up guard, plan-first
> decomposition) is unchanged.

The versions differ only in the **escalation ladder** and, for EduCloud, **one
data-classification rule**.

---

## A. Local / personal version (`policy_mode: hybrid`, the current pilot)

Goal: do as much as possible on open-weight models you run yourself, free and
private, use hosted open-weight for what's too big to own, and reach proprietary
models only as a *verified, boundary-gated* backstop.

**Ladder:**
`local_fast (iMac + MacBook, two health-checked deployments) → [local_large:
future 128GB node, dormant] → remote_open_fast (Groq) → remote_open_broad
(OpenRouter, allowlisted) → [remote_open_direct: Together, dormant] →
proprietary (Anthropic/OpenAI PAYG rescue, confirm-gated)`

**Routing:**
- `default → local_fast` (both machines, one rung; execution on your own hardware)
- `background → local_fast` (compaction/summaries/classify, free)
- `think / longContext → escalate through the ladder`; proprietary only on
  verified open failure or explicit override — never a fixed rung.

**How quality is protected:** the fail-up guard. A task runs local; if it fails
the deterministic check (non-empty diff + `ruff` + `pytest`), it escalates one
rung and retries. Local does the volume; hosted-open covers the too-big-to-own
middle; proprietary is the rescue that catches what open-weight can't — you never
bet correctness on the local model guessing right. A rung that is offline (a
sleeping MacBook, a down endpoint) logs `unavailable` and is skipped, **not**
counted as a model failure.

**Honest limits:**
- A 32b coding model wants ~24–32 GB of free unified memory/VRAM to run well;
  size down to 14b/7b if the iMac can't hold it warm. Swap in whatever current
  coding model your hardware runs best — the config is model-agnostic.
- Expect local to escalate more often than a Sonnet-default setup would; that's
  fine and by design. Watch `failup-log.jsonl`: if local's pass rate is low, its
  tokens are wasted motion — raise its floor model or promote `default` a rung.
- Keep weights on the internal SSD and warm (`OLLAMA_KEEP_ALIVE=-1`); serve over
  Tailscale so the MacBook and any VM share one resident model
  (`src/portage/local-serve.sh`).
- The `remote_open` allowlist is enforced by config (a non-allowlisted model
  isn't a deployment); quantization floor + license live in `models.json`.

This version runs fully offline for anything the local tiers can handle; the
hosted-open and PAYG rungs need network + keys but are never on the critical path
for local-solvable work. The end state (`open_weight_only`, `docs/specs/10`) is this
same ladder with the `proprietary_payg` rung removed — a config-variant swap,
triggered by `proprietary_displacement`.

---

## B. EduCloud version (the fusion)

Adds a **sovereign compute tier** — the EduCloud / Jetstream2 inference service
(gpt-oss-120b, Llama 4 Scout class: OpenAI-compatible, US-hosted, no per-token
cost, no external quota draw) — inserted between local and hosted-open as the
default workhorse *and* the overflow valve. This is the generalized form of the
resource-aware tiers already proven in peer-tutor-framework.

**Ladder (`tiers.educloud.json`):**
`local_fast → sovereign (Jetstream2 gpt-oss-120b) → remote_open → proprietary_payg`

**Routing:**
- `default → sovereign` (free, sovereign, no external quota)
- `background → local_fast`
- `think → escalate`; `longContext → sovereign` (big free context on HPC)

**The inversion that makes this different from every commercial router:** the
order is `local → sovereign HPC → hosted open → proprietary PAYG`. Overflow goes
to compute you already control **before** any metered tier — the opposite of
dollar-first routing. On Jetstream2 the sovereign tier absorbs the bulk of
execution for free, and proprietary is reached only when the guard escalates
through everything below it.

**Where it runs (network reality):** the Jetstream2 inference API is
network-gated. Run **Lane B automation *on* a Jetstream2 VM** and the sovereign
tier is native and tokenless — which fits, since Lane B already wants to live on
an always-on host. Off-instance, point the deployment at the Open WebUI proxy and
set `JETSTREAM2_TOKEN`. In EduCloud, **Outfitter provisions and reaps the
inference nodes** (its jetstream2/hpc adapters) under a budget; Portage routes
onto whatever endpoints Outfitter reports healthy (see `REVISION-PLAN.md` §6).

### The data-classification pin (non-negotiable)

The sovereign tier is **sovereign, not private** — it's US-hosted and off the
commercial providers, but it's shared research infrastructure, admins can view
interactions, and its acceptable-use is research/education only. So sensitivity
is a hard gate *above* the cost logic, expressed as a **policy_mode per lane**,
not a per-request check:

- Sensitivity is a property of the **workspace/repo/lane**, set by you — never
  inferred per request (per-token sensitivity detection fails silently; don't
  rely on it).
- Any lane touching clinical/regulated/student-identifying data runs
  **`policy_mode: sovereign`** — a LiteLLM config whose provider list contains
  **only local**. Even the sovereign HPC and hosted-open tiers are *physically
  absent*, so a misroute is impossible. If a local model can't finish, it stops
  and escalates to a human — never to any shared endpoint. (Note: `sovereign`
  mode is stricter than `open_weight_only` — it excludes hosted-open too.)
- Non-sensitive lanes use the full `hybrid` (or `open_weight_only`) ladder.

This is the pin done right: enforced by which providers exist in the config, not
by trusting the router to behave, and not by a provider's ZDR promise (ZDR on
`remote_open` is defense-in-depth for *ordinary* work only).

---

## Per-lane policy modes (EduCloud default posture)

| Lane | Mode | Rationale |
|---|---|---|
| Student-facing (Belay tutoring; feedback on student work) | `sovereign` | student prompts never leave institutional infra — stronger than ZDR; FERPA-aligned; pin by config absence |
| Course automation (grading via Cairn) | `sovereign` or `open_weight_only` | grading content may be sensitive; hosted-open only with ZDR + institutional sign-off |
| Staff / research lanes | `hybrid` | boundary-gated PAYG rescue, budget per PI/course |

---

## Choosing / switching

Select a mode by loading its LiteLLM config variant and pointing the guard at the
matching tiers file:

| Mode | LiteLLM config | `failup.py --tiers` |
|---|---|---|
| Personal `hybrid` | `litellm.hybrid.yaml` | `.claude/tiers.hybrid.json` |
| Personal `open_weight_only` | `litellm.open-only.yaml` | `.claude/tiers.open-only.json` |
| EduCloud (normal) | `litellm.educloud.yaml` | `.claude/tiers.educloud.json` |
| EduCloud / clinical `sovereign` | `litellm.sensitive.yaml` | `.claude/tiers.local.json` |

Lane A (interactive) is unchanged in all — native Claude Code during the pilot,
retiring as the subscription baseline is measured out (`docs/specs/03`). These
versions shape **Lane B** (automation), which is where the tiering and the
free/sovereign compute actually pay off.
