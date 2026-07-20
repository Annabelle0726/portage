# 02 — Local & EduCloud versions

Same skeleton (two lanes, fail-up guard, plan-first decomposition). The versions
differ only in the **escalation ladder** (`.claude/tiers.*.json`, read by
`failup.py --tiers`) and, for EduCloud, **one data-classification rule**. Pick a
version by copying its config to `~/.claude-code-router/config.json` and pointing
the guard at its tiers file.

---

## A. Local version (pragmatic, not novel — just works)

Goal: do as much as possible on open-weight models you run yourself, free and
private, and use proprietary models only as a *verified* quality backstop.

**Ladder (`tiers.local.json`):**
`local 7b → local 32b → Sonnet 5 → Opus 4.8`

**Routing (`config.local.json`):**
- `default → local 32b` (execution runs on your own hardware)
- `background → local 7b` (compaction/summaries/classify, free)
- `think / longContext → Opus` (judgment and big context go straight to frontier)

**How quality is protected:** the fail-up guard. A task runs on local 32b; if it
fails the deterministic check (non-empty diff + `ruff` + `pytest`), it escalates
to Sonnet, then Opus. So local does the volume and proprietary is the backstop
that catches what open-weight can't — you never bet correctness on the local
model guessing right.

**Honest limits:**
- A 32b coding model wants ~24–32 GB of free unified memory/VRAM to run well;
  size down to 14b/7b if the iMac can't hold it warm. Swap in whatever current
  coding model your hardware runs best — the config is model-agnostic.
- Expect local to escalate more often than a Sonnet-default setup would; that's
  fine and by design. Watch `failup-log.jsonl`: if local's pass rate is low, its
  tokens are wasted motion — raise its floor model or demote `default` to Sonnet.
- Keep weights on the internal SSD and warm (`OLLAMA_KEEP_ALIVE=-1`); serve over
  Tailscale so the MacBook and any VM share one resident model
  (`scripts/local-serve.sh`).

This version has **no external dependency** beyond your Anthropic key — it runs
fully even offline for anything the local tier can handle.

---

## B. EduCloud version (the fusion)

Adds a **sovereign compute tier** — the EduCloud / Jetstream2 inference service
(gpt-oss-120b, Llama 4 Scout: OpenAI-compatible, US-hosted, no per-token cost, no
Max quota draw) — as the default workhorse *and* the quota-overflow valve. This
is the generalized form of the resource-aware tiers already proven in
peer-tutor-framework.

**Ladder (`tiers.educloud.json`):**
`local 7b → Jetstream2 gpt-oss-120b → Sonnet 5 → Opus 4.8`

**Routing (`config.educloud.json`):**
- `default → jetstream2 gpt-oss-120b` (free, sovereign, no quota)
- `background → local 7b`
- `think → Opus`; `longContext → jetstream2` (big free context on HPC)

**The inversion that makes this different from every commercial router:** the
order is `local → sovereign HPC → Max quota → paid API`. Overflow goes to compute
you already control **before** touching the scarce Max quota — the opposite of
dollar-first routing. On Jetstream2 the sovereign tier absorbs the bulk of
execution for free, and Max/Opus is reached only when the guard escalates.

**Where it runs (network reality):** the Jetstream2 inference API is
network-gated. Run **Lane B automation *on* a Jetstream2 VM** and the sovereign
tier is native and tokenless — which fits, since Lane B already wants to live on
an always-on host. Off-instance, point the provider at the Open WebUI proxy and
set `JETSTREAM2_TOKEN`. So the sovereign tier is strongest exactly where the
automated lane already lives.

### The data-classification pin (non-negotiable)

The sovereign tier is **sovereign, not private** — it's US-hosted and off the
commercial providers, but it's shared research infrastructure and admins can view
interactions, and its acceptable-use is research/education only. So sensitivity is
a hard gate *above* the cost logic:

- Sensitivity is a property of the **workspace/repo**, set by you — never inferred
  per request (per-token sensitivity detection fails silently; don't rely on it).
- Any repo touching clinical/regulated data uses
  **`config.educloud-sensitive.json`**, whose provider list contains **only
  local**. The HPC and cloud tiers are *physically absent*, so a misroute to them
  is impossible. If a local model can't finish, it stops and escalates to a human
  — never to a shared endpoint.
- Non-sensitive repos use the full `config.educloud.json` ladder.

This is the pin done right: enforced by which providers exist in the config, not
by trusting the router to behave.

---

## Choosing / switching

| | copy to `~/.claude-code-router/config.json` | `failup.py --tiers` |
|---|---|---|
| Local | `config.local.json` | `.claude/tiers.local.json` |
| EduCloud (normal) | `config.educloud.json` | `.claude/tiers.educloud.json` |
| EduCloud (sensitive) | `config.educloud-sensitive.json` | `.claude/tiers.local.json` |

Lane A (interactive Max) is unchanged in both — native Claude Code, Sonnet
default, Opus for judgment. These versions only shape **Lane B** (automation),
which is where the tiering and the free/sovereign compute actually pay off.
