# Known-good versions

Pin these. The maintenance research behind this project found that wrapping
fast-moving AI CLIs fails mainly through *silent upstream drift*: renamed
models, changed flags, reshaped configs. Two documented precedents — a Claude
Code point release that broke a gateway path with a 400, and a frontier model
suspended by export controls mid-year — are why model selection is treated as
configuration with a tested rollback, never a hardcoded constant.

Fill these in during HANDOFF Phase 0 from the actually-installed versions.
Anything marked UNVERIFIED has been written against documentation but never
executed here.

| Component | Pinned version | Verified | Notes |
|---|---|---|---|
| Claude Code CLI | `__________` | ☐ | `--model` / effort flag syntax UNVERIFIED |
| Codex CLI | `__________` | ☐ | Plus 5h window shared with other ChatGPT agents |
| claude-code-router | `__________` | ☐ | May be droppable entirely — see Phase 1 |
| LiteLLM | `__________` | ☐ | Config schema has drifted across releases |
| Herdr | `__________` | ☐ | Plugin API v1; `pane list` JSON shape UNVERIFIED |
| Ollama | `__________` | ☐ | |
| Local models | `qwen2.5-coder:7b`, `qwen2.5-coder:32b` | ☐ | steward / work tiers |

## Model IDs

Model names live in exactly two places, on purpose — change them there, not in
code:

- `herdr-meters/models.json` — the routing target catalog
- `litellm.config.yaml` — the deployment ladder

## Drift watch

Renovate with a custom HTTP datasource (HANDOFF Phase 5) should watch the
Claude Code releases feed and this file's model IDs, so a rename opens a PR
instead of a 3am failure. Pair with the nightly canary: one tiny live request
per deployment path, failing loudly.
