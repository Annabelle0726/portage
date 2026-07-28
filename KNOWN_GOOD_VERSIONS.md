# Known-good versions

Pin these. The maintenance research behind this project found that wrapping
fast-moving AI CLIs fails mainly through *silent upstream drift*: renamed
models, changed flags, reshaped configs. Two documented precedents — a Claude
Code point release that broke a gateway path with a 400, and a frontier model
suspended by export controls mid-year — are why model selection is treated as
configuration with a tested rollback, never a hardcoded constant.

Filled in 2026-07-20 (HANDOFF Phase 0) from the actually-installed versions on
the primary dev machine (macOS 25.5.0, arm64). "Verified" means the version was
read from the installed binary AND the repo's use of it was executed, not just
documented. Anything absent is marked so rather than guessed.

| Component | Pinned version | Verified | Notes |
|---|---|---|---|
| Claude Code CLI | `2.1.207` | ☑ | `--model` / `--effort` syntax executed — see below and `docs/phase-1-findings.md` |
| Codex CLI | **ABSENT** | ☐ | Not installed on this machine. Every Codex flag, model ID and effort value in this repo remains UNVERIFIED. |
| claude-code-router | **DELETED (Phase 2)** | — | `.claude-code-router/` is gone. Phase 1 found it unnecessary — Claude Code reaches LiteLLM directly — and Phase 2 acted on it: CI, `plan.py`, and `local-serve.sh` all updated. See `docs/phase-1-findings.md`. |
| LiteLLM | `1.93.0` | ☑ | Proxy started against both configs; round-trip, ordered failover and the sensitive pin all executed. Config schema had drifted — two fixes applied, below. |
| Herdr | `0.7.1` | ☐ | Installed, but the plugin API / `pane list` JSON shape is still UNVERIFIED (HANDOFF Phase 3). |
| Ollama | `0.30.10` | ☑ | Server reachable at `http://localhost:11434`; served the Phase 1 round-trip. |
| Local models | `qwen2.5-coder:7b`, `qwen2.5-coder:32b` | ☐ | **NEITHER IS INSTALLED.** Only `llama3.2:latest` is present, which is what the Phase 1 smoke test actually ran against. Pull both before any real use. |
| uv | `0.11.16` | ☑ | |
| Python (venv) | `3.11.15` | ☑ | `requires-python = ">=3.11"` |

## Verified CLI facts (Claude Code 2.1.207)

Executed against a local LiteLLM proxy, so these cost no metered quota.

- `--model <name>` accepts an alias (`sonnet`, `opus`, `fable`), a full model
  name (`claude-sonnet-5`), or **any string the configured gateway resolves** —
  a LiteLLM model-group name like `work` works.
- The `provider,model` comma form (`anthropic,claude-sonnet-5`) is **rejected**.
  That syntax belongs to claude-code-router's `Router` block, not to
  `claude --model`. It had leaked into `.claude/tiers.claude.json`; fixed.
- `--effort <level>` accepts exactly `low|medium|high|xhigh|max`.
  **`default` is not valid.** An unknown value does not fail — the CLI prints a
  warning and silently proceeds at default effort. For the fail-up ladder this
  is the dangerous case: a bad value quietly flattens escalation instead of
  erroring. Tiers wanting default effort must use `null`, which omits the flag.
- Gateway env vars honored: `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN` /
  `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`. Claude Code calls
  `POST /v1/messages?beta=true` and streams.
- `MAX_THINKING_TOKENS=0` is required to drive a model that does not support
  extended thinking; without it Claude Code sends a `thinking` parameter that
  such backends reject. `drop_params: true` in LiteLLM does **not** strip it.

## Verified LiteLLM config facts (1.93.0)

Both were drift, and both were fixed in `litellm.config.yaml`:

1. `health_check_interval` and `background_health_checks` belong under
   `general_settings`, **not** `router_settings`. With them in
   `router_settings` the proxy hard-fails at startup.
2. `model_info.tier` is a **reserved** LiteLLM key constrained to `free|paid`.
   Our semantic values (`local`, `sovereign`, `open_api`, `frontier`) failed
   schema validation — and LiteLLM *silently dropped every offending
   deployment* while still reporting the proxy healthy. All 7 deployments
   vanished and `/v1/models` returned an empty list. The key is renamed to
   `commons_tier` in both configs. **Treat a healthy-but-empty `/model/info`
   as the signature of this class of bug.**

Also note: `success_callback: ["langfuse"]` is commented out until Phase 8
provisions Langfuse, and `database_url` likewise, so the proxy runs today.

## Rungs vs groups (Phase 2 design)

`litellm.config.yaml` registers some deployments TWICE, under two kinds of
`model_name`, because two different callers need two different guarantees:

- **Rungs** — `local-small`, `local-big`, `sovereign-work`, `sonnet`, `opus` —
  are individually addressable, one name per deployment, no `order`. The
  fail-up ladder (`.claude/tiers.*.json`) names a rung directly: it chose a
  specific point on the capability ladder and must reach exactly that
  deployment, not whichever one happens to be up. This is what makes the guard
  a *capability* escalation.
- **Groups** — `work`, `judgment` — are ordered-failover pools over the same
  deployments (`order: 1,2,3,...`). A caller that just wants "the best thing
  that's actually reachable" targets the group. This is *availability*
  failover, and it's what the Phase 1 smoke test exercised.

Verified: loading `litellm.config.yaml` registers 12 deployments (5 rungs + 4
in `work` + 2 in `judgment` + 1 `steward`), all creating cleanly — see
`tests/test_repo_invariants.py::test_litellm_config_readiness`.

`sonnet`/`opus` are spelled identically whether reached as a LiteLLM rung
(gatewayed, `ANTHROPIC_API_KEY` billing) or as a native Claude Code alias
(Max-wallet quota, no gateway) — same string, two different meters depending
on which env vars are set when the runner is invoked. `.claude/tiers.claude.json`
(native, Max wallet) and `.claude/tiers.local.json` / `tiers.educloud.json`
(LiteLLM-gatewayed, API billing) both use these names for that reason; do not
assume "same tier name" means "same meter" — check which env is active.

## Model IDs

Model names live in exactly two places, on purpose — change them there, not in
code:

- `herdr-meters/models.json` — the routing target catalog
- `litellm.config.yaml` — the deployment ladder

`.claude/tiers.*.json` and `herdr-meters/models.json`'s `local.*`/`claude.*`
targets both reference the rung names above rather than raw model strings, so
all three files share one vocabulary (see "Rungs vs groups"). Codex targets in
`models.json` still carry raw model IDs (`gpt-5.6-*`) — Codex has no rungs yet
because the CLI is unverified (Phase 3).

## Drift watch

Renovate with a custom HTTP datasource (HANDOFF Phase 5) should watch the
Claude Code releases feed and this file's model IDs, so a rename opens a PR
instead of a 3am failure. Pair with the nightly canary: one tiny live request
per deployment path, failing loudly. The canary must assert a **non-empty**
`/model/info`, given finding 2 above.
