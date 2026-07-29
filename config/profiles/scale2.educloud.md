# Scale 2 — the EduCloud profile

*The config diff Line E's E0 milestone calls for, cut against Line P's Scale 1.
Authored 2026-07-28, after HB-0 made the registry the single source of truth
and gave the diff something to be a diff of.*

---

## 1. What this is, and the one claim it has to survive

Line E's expansion contract says each scale is a config diff against the
previous one, and that **a diff containing code is a defect**. This directory
now holds the Scale-2 half of that diff:

```
scale2.educloud.settings.yaml            shared settings, both lanes
scale2.educloud.student.registry.yaml    sovereign only — the enforcing lane
scale2.educloud.staff.registry.yaml      sovereign default + hybrid tail
scale2.educloud.student.yaml             generated
scale2.educloud.student.model_list.yaml  generated
scale2.educloud.staff.yaml               generated
scale2.educloud.staff.model_list.yaml    generated
```

**The claim: no engine change was required.** Not one line of
`src/portage/render_config.py`, `schema/registry.schema.json`, or any other
engine file was touched to produce this. The Scale-2 step is config, exactly as
the contract requires, and that is now a demonstrated property rather than an
aspiration.

Two things made it hold, and both are worth naming because they are what a
future scale step will lean on:

- **`os.environ/` references are per-deployment namespaces, not global names.**
  `SOVEREIGN_BASE_URL` resolves to the Jetstream2 vLLM endpoint on the Waypoint
  host and is parked in Line P's private deployment. Same name, different value,
  no schema field needed to disambiguate them. The temptation was to add an
  `api_key_env` field to the schema so two sovereign endpoints could coexist;
  that would have been an engine change in service of a problem the environment
  already solves.
- **The renderer takes `--registry` as an argument.** Two lanes are two
  invocations, not a filtering feature. This is what let isolation-by-absence be
  implemented literally instead of as a runtime check.

---

## 2. The diff, in full

Everything below is the complete delta from `scale1.example.*`. There is
nothing else.

### `router_settings`

| Setting | Scale 1 | Scale 2 | Why |
|---|---|---|---|
| `allowed_fails` | 1 | 3 | Jetstream2 is shared HPC. A queued or briefly saturated endpoint is normal operation, not a sick deployment. Ejecting it after one timeout strands the sovereign default — and on the student lane there is no fallback, so the request simply fails. Tolerance here is a privacy property, not only an availability one. |
| `cooldown_time` | 300 | 120 | The same reasoning inverted: when a queue drains, the sovereign deployment should rejoin promptly rather than sit out five minutes. |

Both provisional. TODO(allocation): re-tune against observed JS2 queue behaviour
during the E1 pilot and record the measured values.

### `model_list`

Scale 1's roster is two Macs over Tailscale plus a hosted-open tail. Scale 2
replaces the local tier with institutional vLLM and splits the result in two:

- **Student lane — five deployments, all sovereign.** `classifier`,
  `code_small`, `code_large`, `research_synthesis`, `embedding`, each on the
  `openai` route against `SOVEREIGN_BASE_URL`. No OpenRouter row. No Anthropic
  row. No Perplexity row.
- **Staff lane — nine deployments across seven aliases.** The same five
  sovereign rows at `order: 1`, a hosted open-weight fallback at `order: 2` on
  `code_large` and `research_synthesis` only, and the two proprietary rescue
  rows present-but-`enabled: false`.

### Nothing else

`litellm_settings` and `general_settings` are byte-identical to Scale 1. Per
this directory's README, a Scale-2 diff touching anything outside `model_list`
and `router_settings` would mean the config/registry separation had broken
down. It didn't.

---

## 3. Three decisions that need your sign-off

These are judgment calls I made from existing project policy rather than
inventing. Each is defensible and each is reversible, but none should pass
silently.

### 3.1 The student lane renders five aliases, not seven

HB-0's Gate 2 requires `/v1/models` to list exactly the seven aliases. That
invariant is a property of the **Scale-1 deployment**, where every alias has a
deployment and the disabled proprietary rows must stay visible so HB-2's rescue
path is a flag flip.

At Scale 2 the student lane inverts that requirement. `proprietary_code` and
`proprietary_research` have no sovereign deployment and must not acquire one,
so they are **absent from the student registry entirely** — not disabled,
absent. A student-lane request for one fails at the proxy with an unknown-model
error.

The reasoning: the seven aliases are the platform's *vocabulary*; which of them
a lane can reach is *policy*. A loud unknown-model failure is the correct
behaviour for a student lane reaching for a commercial endpoint. The
alternative — registering them disabled — leaves the row in `model_list`, and
the whole point of absence-based isolation is that there is nothing there to
mis-enable.

**What this means for you:** `portage-local`'s
`test_registry_declares_all_seven_aliases_and_no_others` asserts equality with
the seven and should stay that way — it guards the Scale-1 deployment. The
engine's new `tests/test_scale2_profile.py` guards the Scale-2 lanes with the
inverted assertion. Two deployments, two invariants, both tested. If you'd
rather the student lane register all seven with the unreachable ones disabled,
say so — but I'd argue against it.

### 3.2 Student deployments are `personal_sensitive`, not `regulated`

Line E's E0 text says the profile "carries the attribution labels and the
`regulated` classification." I did not classify these rows `regulated`, and the
reason is that CC-P2's own data-destinations policy forbids it:

> Institutional HPC is sovereign and shared. **Administrators can view
> interactions.** [...] Identifiable student records stay local. They never
> reach a shared or commercial endpoint.

Every deployment in this profile is institutional HPC. Marking it `regulated`
would assert that identifiable student records may route there, which is
exactly what the policy prohibits.

What makes the student lane legitimate is the other half of E0's sentence — the
**attribution labels**. Student coursework reaches this tier already
de-identified, carrying only the platform's opaque `{course, assignment,
student}` identifiers. That is `personal_sensitive` work on shared sovereign
infrastructure, which the policy permits.

**The consequence, stated plainly: identifiable-record processing has no
deployment at E0.** That absence is itself the enforcement, and
`test_student_lane_carries_no_regulated_deployment` will fail if anyone points a
`regulated` workload at shared infrastructure. If Cairn or Belay turns out to
need a genuinely `regulated` inference lane before the pilot, it needs a *local*
deployment on the Waypoint host, and that is a hardware decision (a GPU droplet,
or a small CPU-served model) that does not exist in any current plan. **This is
the item most likely to bite during E1, and it is worth deciding before the
pilot rather than during it.**

### 3.3 Attribution labels are not in the registry, and shouldn't be

E0 asks the profile to "carry the attribution labels." A registry entry
describes a *deployment*; attribution describes a *request*. In LiteLLM the
labels arrive as tags and metadata on virtual keys, which is HB-1's mechanism
(one key per frontend, tagged, budgeted) extended to one key per course section.

Putting `{course, assignment, student}` into `model_info` would have made the
diff look complete while attributing nothing. The labels belong in the key
provisioning step, which is Waypoint deployment work, not registry work.
Recorded here so the gap is understood as deliberate.

---

## 4. What is still TODO(allocation)

None of this is blocked on engineering. All of it is blocked on the ACCESS
Discover allocation being filed and Jetstream2 being live.

- **The five `model_id` values are a deployment contract, not a guess.** vLLM
  serves under whatever `--served-model-name` it is launched with, so these
  names are ours to define — but the JS2 launch must match them exactly:
  `portage-classifier`, `portage-code-small`, `portage-code-large`,
  `portage-research`, `portage-embedding`.
- **`max_context` on all five** — provisional, confirm against the served
  context window.
- **`license` on all five** is the literal `UNVERIFIED`, per the registry's own
  convention, until the allocation picks actual weights.
- **`allowed_fails` / `cooldown_time`** — re-tune against real queue behaviour.
- **The embedding dimension** must match whatever Qdrant collection HB-3/S2
  creates. Changing the embedder after a corpus is indexed invalidates the
  store, which is why `embedding` deliberately has no hosted fallback in either
  lane.

---

## 5. How to render

```
python src/portage/render_config.py \
    --registry config/profiles/scale2.educloud.student.registry.yaml \
    --settings config/profiles/scale2.educloud.settings.yaml \
    --schema schema/registry.schema.json \
    --out-dir config/profiles \
    --config-name scale2.educloud.student.yaml \
    --model-list-name scale2.educloud.student.model_list.yaml
```

Same again with `staff` substituted for `student`. CI re-renders both with
`--check` on every PR, so a hand-edit to a generated file fails the build.
