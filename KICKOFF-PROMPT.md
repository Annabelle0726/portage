# Kickoff prompt for Claude Code

Untar the bundle, `cd` into it, `git init && git add -A && git commit -m "import design bundle"`,
then open Claude Code and paste the prompt below. Start in **plan mode** — the
first session should produce findings and a small diff, not a large build.

---

## Session 1 prompt (copy from here)

```
You are picking up a fully specified but never-executed project. Read, in this
order: README.md, PLATFORM.md, then HANDOFF.md. PROJECT.md and specs/00-09 are
the reasoning record — consult them when you need to know *why*, don't read them
all up front.

Operating constraints for every session on this repo:

1. BUILD AS LITTLE AS POSSIBLE. HANDOFF.md §2 records which components were
   deliberately replaced by existing tools (LiteLLM, Herdr's plugin system,
   native Claude Code features). Do not rebuild any of them. If you think
   something needs custom code, first say what existing tool you checked and why
   it doesn't fit.

2. TREAT ALL EXTERNAL CLI INVOCATIONS AS UNVERIFIED. Every `claude -p`, `codex`,
   `ccr`, and `--effort`/`--model` flag in this repo was written against
   documentation and has never been run. Do not build on top of them until you
   have executed them and confirmed the actual syntax. When you find a
   discrepancy, fix it in the code AND record it in KNOWN_GOOD_VERSIONS.md.

3. NEVER REGRESS THE STANDING RULES in HANDOFF.md §6. The load-bearing ones:
   sensitive data is pinned by config absence and never by a runtime check or
   model judgment; the verifier decides pass/fail, never the model's
   self-report; no fan-out orchestration; every efficiency claim must survive
   the quality gate in measure.py.

4. WHEN YOU HIT AN OPEN QUESTION (HANDOFF.md §7), stop and investigate rather
   than assuming. Report what you found.

SCOPE FOR THIS SESSION — Phase 0 and the Phase 1 investigation only. Do not
start Phase 2+.

Phase 0 (finish it):
- Fill in KNOWN_GOOD_VERSIONS.md from the actually-installed versions on this
  machine. Mark anything not installed as absent rather than guessing.
- `uv sync`, then `uv run ruff check .` — fix what it finds.
- Create a `tests/` directory with a placeholder that passes, so
  `uv run pytest` is green from day one.
- Acceptance: ruff clean, pytest green, no references to files that don't exist.

Phase 1 (investigate, then smoke-test):
- The highest-value question in the whole plan: can Claude Code (and `claude -p`)
  and Codex CLI point at the LiteLLM proxy DIRECTLY, using LiteLLM's
  Anthropic-compatible endpoint? If yes, claude-code-router and everything in
  .claude-code-router/ can be deleted entirely. Fewest hops wins. Investigate
  and write up the finding before changing anything.
- Start LiteLLM against litellm.config.yaml and confirm: (a) one curl
  round-trips through Ollama; (b) stopping Ollama causes failover to the next
  deployment in the `work` group; (c) litellm.sensitive.yaml exposes no
  non-local model.
- Do not wire anything else to LiteLLM yet.

DELIVERABLE for this session: a short written findings note (create
docs/phase-1-findings.md) covering the direct-connection question, the actual
CLI flag syntax you observed, and anything in the drafted code that turned out
to be wrong. Plus the Phase 0 acceptance criteria met. Keep the diff small.

Ask me before: deleting anything outside the superseded list in HANDOFF.md §2,
adding a dependency, or spending real tokens on a paid meter.
```

## Session 2 and beyond

Once Phase 1 findings are in, the next session is HANDOFF.md Phase 2 — hardening
`failup.py` and `plan.py` with **stub-runner tests** (a fake script that succeeds
or fails on command), so the guard's ladder logic, budget ceiling, and
stash/reset recovery are all provable with zero tokens and no network. That test
suite is the thing that makes every later phase safe to build.

Suggested prompt shape for later sessions: same operating constraints (1-4
above), one phase per session, always ending with a findings note when the phase
involved investigation.
