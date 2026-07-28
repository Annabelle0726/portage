# Config profiles

Sanitized, reviewable examples of the LiteLLM configs Portage actually runs
with — no hostnames, no keys, no personal choices. Since HB-0, this directory
holds both the *source* (a registry + settings, hand-authored) and the
*rendered output* (generated, never hand-edited):

- `scale1.example.registry.yaml` — a sanitized example registry, fully
  open-weight, placeholder endpoints (`EXAMPLE_NODE_A_HOST`,
  `EXAMPLE_NODE_B_HOST`, etc.). Same shape as `portage-local`'s real (private)
  `registry.yaml`, the single source of truth for the live deployment.
- `scale1.example.settings.yaml` — the router/litellm/general settings block,
  also hand-authored and versioned.
- `scale1.example.yaml` / `scale1.example.model_list.yaml` — **generated** by
  `src/portage/render_config.py` from the two files above. Carries a
  "GENERATED — do not hand-edit" header. CI re-renders and diffs these on
  every PR (`render_config.py --check`) — a diff here that isn't just the
  registry/settings changing is the renderer breaking its own contract, not a
  file to hand-patch.

Regenerate locally after editing either source file:

```
python src/portage/render_config.py \
    --registry config/profiles/scale1.example.registry.yaml \
    --settings config/profiles/scale1.example.settings.yaml \
    --schema schema/registry.schema.json \
    --out-dir config/profiles \
    --config-name scale1.example.yaml \
    --model-list-name scale1.example.model_list.yaml
```

Scale 2 arrives as a config *diff* against this file (MANIFEST §"Actions" item
4) — if the diff touches anything outside `model_list`/`router_settings`, the
config/registry separation has broken down and that's the defect to fix, not
the diff to accept.

The live, personal version — real Tailscale hostnames (as `os.environ/`
references, not literals — see `portage-local/registry.yaml`'s own header),
real model tags, real endpoint URLs — lives in `~/dev/portage-local`
(private), never here. See that repo's own README for the boundary test, and
`config/deploy/compose.example.yaml` (sibling directory) for the sanitized
compose template the deployment repo's real `docker-compose.yaml` is cut
against.
