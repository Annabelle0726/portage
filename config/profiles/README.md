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

## Scale 2 — the EduCloud profile

Scale 2 arrives as a config *diff* against Scale 1 (MANIFEST §"Actions" item
4) — if the diff touches anything outside `model_list`/`router_settings`, the
config/registry separation has broken down and that's the defect to fix, not
the diff to accept. That diff now exists, and it holds: it touches
`model_list` and two `router_settings` values, and required **no engine
change**.

- `scale2.educloud.settings.yaml` — shared by both lanes.
- `scale2.educloud.student.registry.yaml` — the student lane. **Institutional
  sovereign deployments only.** No commercial route appears in this file at
  all, which is how "student lanes are sovereign by absence" is implemented
  literally rather than as a runtime check.
- `scale2.educloud.staff.registry.yaml` — the instructor lane: the same
  sovereign deployments at `order: 1`, a hosted open-weight fallback at
  `order: 2` on two aliases, and the proprietary rescue rows disabled.
- `scale2.educloud.{student,staff}.yaml` + `.model_list.yaml` — **generated**,
  same rules as Scale 1.

Two lanes are two `--registry` invocations of the same renderer, not a
filtering feature — so isolation cannot be defeated by a filter bug.
`tests/test_scale2_profile.py` asserts the isolation property directly against
the registry (CC-P2 Step 5's check, arriving early because the student lane is
the first configuration that will carry real coursework).

**`scale2.educloud.md` is the reviewable narrative** — the complete diff table,
and three decisions flagged for sign-off, including why the student lane
renders five aliases rather than seven and why its deployments are
`personal_sensitive` rather than `regulated`. Read that before reviewing the
YAML.

The live, personal version — real Tailscale hostnames (as `os.environ/`
references, not literals — see `portage-local/registry.yaml`'s own header),
real model tags, real endpoint URLs — lives in `~/dev/portage-local`
(private), never here. See that repo's own README for the boundary test, and
`config/deploy/compose.example.yaml` (sibling directory) for the sanitized
compose template the deployment repo's real `docker-compose.yaml` is cut
against.
