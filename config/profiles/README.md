# Config profiles

Sanitized, reviewable examples of the LiteLLM configs Portage actually runs
with — no hostnames, no keys, no personal choices. Placeholders read
`LOCAL_NODE_A`, `LOCAL_SMALL_MODEL_ID`, `SOVEREIGN_MODEL_ID`, etc.; every real
value resolves at runtime via `os.environ/...` references or a real hostname
in the private deployment repo, never here.

- `scale1.example.yaml` — the personal-scale profile (`local_fast → [dormant
  local_large] → remote_open_fast (Groq) → remote_open_broad (OpenRouter) →
  [dormant remote_open_direct] → proprietary`, per CW02-decisions.md §3).

Scale 2 arrives as a config *diff* against this file (MANIFEST §"Actions" item
4) — if the diff touches anything outside `model_list`/`router_settings`, the
config/registry separation has broken down and that's the defect to fix, not
the diff to accept.

The live, personal version of this file — real Tailscale hostnames, real
model tags, real endpoint URLs — lives in `~/dev/portage-local` (private),
never here. See that repo's own README for the boundary test.
