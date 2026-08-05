# Licensing

Status: in force as of 2026-08-06. The personal-time-work IP release
originally anticipated here is not the path forward; the University of
Arizona will instead administer grants for this work, which resolves the
condition this file was written under. The licenses below are now a grant,
not a plan.

## The split, and why

Portage uses two licenses on purpose.

The portability contract is Apache-2.0. Anyone should be able to write a
provider registry, an alternative renderer, or a different orchestrator
against the same config schema without taking on copyleft. Making the
contract permissive maximizes reuse, which is the point of a contract.

The Portage engine — the fail-up guard, the plan-first decomposer, the
measurement harness, the Herdr meters plugin — is AGPL-3.0. The running
router and its policy logic are copyleft so that improvements to a deployed
instance flow back to the commons, including over a network.

This is the same principle Cairn and Belay use: the interoperability
primitives are Apache, the platform that implements them is AGPL.

## The boundary

Apache-2.0, the contract only:

- `config/**` — the sanitized example profiles and their schema. Anyone
  writing a Portage-compatible config, or a tool that renders one, needs this
  surface and only this surface.
- Any future `schema/` (JSON Schema / OpenAPI for the endpoint manifest,
  plan.json, etc.) — same reasoning.

AGPL-3.0, everything that implements the contract:

- `src/portage/` — failup.py (the deterministic fail-up guard), plan.py (the
  decomposer), measure.py (the measurement harness), distill.py (parked).
- `plugins/herdr-meters/` — the Herdr plugin: classify, adapt, meters.

`docs/**` carries no header — prose, not code.

The boundary test for any new file: if it makes a routing decision, it is
AGPL engine code. If it only describes a config shape another tool could
implement against, it is Apache contract. If it's prose, it's neither.

## Placement (at publish time)

- AGPL-3.0 full text at the repository root as `LICENSE`. Drop in the
  verbatim text from the FSF (gnu.org); do not modify it.
- Apache-2.0 full text alongside the contract, `config/LICENSE`, or in
  `LICENSES/Apache-2.0.txt`. Drop in the verbatim text from apache.org; do
  not modify it.
- Per-file SPDX headers (`SPDX-License-Identifier: AGPL-3.0-only` or
  `Apache-2.0`) so the boundary is legible file by file, not just by
  directory. These headers are already in place on every source file; they
  are declarations of intent that become a grant only when the two license
  texts are dropped in and the Status above flips to in force.

## Contributions: DCO, not a CLA

Contributions are accepted under the Developer Certificate of Origin, with a
`Signed-off-by` line on each commit. There is no copyright assignment and no
contributor license agreement — with no single entity holding assigned
copyright, no single entity can relicense the project out from under its
contributors.

## `portage-local`

The private deployment repo (`~/dev/portage-local`) carries no license file
and states in its README that it is private and unpublished. Nothing in it is
released, so the question does not arise there.
