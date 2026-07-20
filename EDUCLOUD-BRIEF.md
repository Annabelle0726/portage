# EduCloud brief — decentralized AI as public infrastructure

*A positioning and design brief to carry into the EduCloud project. Audience:
EduCloud collaborators and institutional stakeholders, not just engineers.*

---

## 1. The reframe

"Decentralized AI" has been captured by one meaning — token-incentivized,
permissionless GPU marketplaces (Bittensor, io.net, Akash). **That is not what
this is, and for education it is disqualifying:** you cannot know whose hardware
ran the inference, which breaks FERPA and IRB obligations the moment student or
clinical data touches it.

The meaning that matters for EduCloud is the older and more boring one:

> **Decentralized AI = publicly-funded, institutionally-governed compute running
> open-weight models, federated across institutions, with commercial frontier
> models as a policy-gated option rather than a dependency.**

The distinguishing question is not "is it distributed?" but **"who governs the
compute, and can the institution audit it?"** Under that definition, NSF ACCESS
allocations, Jetstream2, and campus HPC clusters are already decentralized AI
infrastructure. They are simply underused for inference.

## 2. Why education specifically needs this

Four arguments, in ascending order of force.

**Continuity.** A course that depends on a commercial model is one vendor
decision away from breaking. This is not hypothetical: a frontier model was
suspended globally under export-control directives in June 2026 and restored
three weeks later. A semester does not pause for that. Institutional compute plus
pinned open weights is the hedge.

**Compliance.** Student records are FERPA-governed; clinical training data is
worse. Routing them through commercial APIs is a governance problem that
procurement offices are increasingly unwilling to sign off on. Local and
institutional tiers keep regulated data inside the institution's own boundary.

**Reproducibility.** Education research cannot be replicated against a model that
is silently updated or deprecated. Open weights, version-pinned, are the only way
a study run in 2026 can be re-run in 2029 and mean anything. For an education
researcher this is not a nice-to-have; it is the difference between publishable
and not.

**Equity — the strongest argument.** If AI tutoring quality is a function of
per-token budget, then well-resourced institutions get capable tutors and
under-resourced ones get degraded service or none. Building on shared public
infrastructure makes capability a function of *infrastructure already paid for by
public funding* rather than of local ability to pay. That is the Open Access
argument with real teeth: the same allocation that serves a flagship serves a
community college partner.

## 3. What we are designing

A **verifier-driven, sovereignty-aware control plane** — the layer that decides
which model runs a task, on whose compute, under what policy, and whether the
result is actually acceptable.

**The tier ladder (routing policy, not a product feature):**

```
local open-weight  →  institutional / sovereign HPC  →  commercial frontier
(free, private)       (free at point of use,            (policy-gated,
                       governed, auditable)              last resort)
```

Escalation is **open-to-open first**. Commercial models are reached only when a
deterministic check says the open tiers failed — never by default, and never at
all in sovereign mode.

**Four mechanisms make it work:**

1. **The verifier decides, never the model.** A runner — tests, lint, citation
   resolution, rubric coverage — determines success. Models do not self-report.
   On failure, the task escalates one tier and retries. This is what makes
   cheaper open tiers *safe* to default to: a misroute self-corrects rather than
   shipping a wrong answer to a student.
2. **Data classification by absence.** Regulated workspaces run against a config
   whose model list contains *only* local deployments. The commercial and shared
   tiers are not blocked at runtime — they are physically absent. A misroute is
   impossible rather than unlikely.
3. **Triage before routing.** A free local model catches underspecified requests
   before they consume expensive capacity — the largest real source of waste.
4. **Measurement with a quality gate.** No efficiency claim counts if verified
   success rate drops. Enforced in code.

**Three operating modes**, same product surface: *full-open* (no commercial
dependency at all), *hybrid* (frontier as verified ceiling), *sovereign* (pinned
to institutional endpoints for governed data).

## 4. What is already proven inside EduCloud

The `peer-tutor-framework` already demonstrates two of the four mechanisms in the
tutoring domain: resource-aware tiers pointed at Jetstream2, and a deterministic
governance grader (solution-leak prevention) that decides acceptability
independently of the model. **This project generalizes that pattern out of
tutoring and into a domain-independent control plane** — which is the honest
framing of the contribution: not a new idea, an existing EduCloud idea made
reusable and measurable.

The pedagogical resonance is worth naming: in education the failure mode is a
student taught something false or handed an answer they should have derived.
"The model does not grade its own homework" is not a slogan here — it is the
governance requirement that makes AI tutoring defensible at all.

## 5. The Parity Bench — the political instrument

The comparison suite is as much an institutional argument as a technical one. If
we can show that open-weight models on institutional compute reach **parity on
educational tasks** with commercial subscriptions, that is the evidence a
department needs to justify not buying per-seat licenses.

The design guards against wishful results: a 2×2 factorial (our harness × native
harness, open model × frontier model) so a gap is attributable to *harness* or
*model* rather than asserted; preregistered tasks and margins; and a
non-inferiority rule — no cost or speed win may be claimed unless verified
success rate stays within margin. **If open-weight loses, the bench says so.**
That credibility is the point; a benchmark that could only produce the answer we
want would persuade nobody.

Cost is reported three ways, which institutions need and vendors never publish:
marginal cost per task, amortized cost per verified success, and quota-share cost
(what fraction of a capped plan a "free" task actually consumed). At institutional
scale these translate directly into per-student cost modeling.

## 6. Context to carry into the project

**Prior art to build on, not duplicate.** STREAM (`hpc-as-api` / `streamrelay`)
and Argonne's FIRST are the closest work on exposing HPC-hosted open models as
OpenAI-compatible endpoints. FIRST is production but DOE-gated; STREAM is a 2026
paper without a confirmed public repo. Borrow the Globus-based control-plane
pattern rather than reinventing firewall traversal.

**Jetstream2 specifics.** The inference service is free, sovereign, and
OpenAI-compatible, but network-gated — running workloads *on* a JS2 instance is
the zero-adapter path; external access needs confirmation before it can be
designed around. Its acceptable use is research and education only.

**The distinction that governs student data.** Institutional HPC is **sovereign
but not private** — shared infrastructure, admin-visible. It is the right tier for
open coursework and research; it is *not* a FERPA-safe destination for
identifiable student records. Those stay local. Do not let the sovereignty story
blur this line.

**Watch item.** DOE↔NSF federation via Globus could open FIRST-class services to
ACCESS users with little warning, which would replace most custom adapter work.
Worth a quarterly check.

**Funding paths.** NSF ACCESS allocations for the compute itself; Anthropic's AI
for Science program (up to $30k in credits per project) for the frontier-side
baseline work, which conveniently keeps benchmark comparisons off personal
budgets.

## 7. Partnership opportunity — OpenMined

OpenMined (openmined.org) is a 501(c)(3) non-profit building **Syft**, a
federated AI network for "secure, governed computation across silos — without
moving data." Note the category: non-profit, not industry. For NSF purposes that
is usually stronger for broader-impacts and sustainability framing, but it does
not fill an "industry partner" requirement where a mechanism demands one.

**The strongest fit: it dissolves the sovereign-but-not-private ceiling (§6).**
Today, FERPA-governed and clinical data can only run on local compute, capping
that tier at whatever a single machine holds. Syft's model — computation
executed where the data lives, from analytics through model inference — converts
the sensitive tier from *local-only and capacity-capped* to *federated and
private*. This is the largest single capability unlock available to EduCloud.

**Four further points of contact:**

1. **NAIRR.** OpenMined is a launch partner for NSF's National AI Research
   Resource pilot. EduCloud's entire compute thesis rests on NSF-funded
   infrastructure; this is a direct bridge, practically and for proposal
   credibility.
2. **The missing subnet.** Syft runs subnets for Publishers, Genomics, Creators,
   and AI Auditors, and explicitly invites new domain subnets. There is no
   education vertical — and education has the same structure as genomics:
   highly sensitive, siloed by institution, enormously valuable in aggregate.
   The ask reframes from "help us" to "anchor the subnet you don't have."
3. **Federated steward training.** `syft-flwr` and their FL Project Co-Design
   program would let multiple EduCloud deployments improve a shared local model
   *without pooling raw logs* — fixing both the thin-data problem and the
   feedback-loop-collapse risk in specs/09 §7, and doing so without moving
   student interactions off-site.
4. **Verification overlap.** Their AI Auditors work — auditors receive verified
   answers rather than model weights or user logs — shares an instinct with this
   project's core rule that the verifier decides and the model never
   self-reports. Their secure-enclave evaluation work is also directly relevant
   to running the Parity Bench against models that cannot be inspected.

**Open questions to put to them,** rather than assume: whether an education
subnet is on the roadmap; whether the NAIRR partnership creates a path for
education-focused ACCESS work; and whether FL Co-Design could take on a
federated tutoring or shared-steward project.

## 8. Honest limits

- **This is a complement, not a replacement.** The frontier remains centralized
  and, for the hardest judgment tasks, still better. The design keeps a
  policy-gated ceiling rather than pretending otherwise. The right amount of
  decentralization is a dial, and the dial moves toward open as the capability
  gap closes — which it has been doing quickly.
- **Institutional compute is not free labor.** Allocations must be applied for,
  endpoints maintained, and models updated. "Free at point of use" hides real
  administrative cost that a department has to own.
- **Novelty is time-sensitive.** Subscription-quota-aware routers exist; sovereign
  HPC inference exists; nobody has combined them. That gap could close without
  warning, which argues for publishing the measurement method early — the method
  outlives the gap.
- **The equity argument is a hypothesis until measured.** It is a good argument.
  It becomes a finding only when the Parity Bench shows an under-resourced
  deployment achieving comparable outcomes. Until then, present it as motivation,
  not as a result.
