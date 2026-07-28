# herdr-meters

Cross-vendor meter awareness for [Herdr](https://herdr.dev). One interface over
Claude Max, ChatGPT Plus/Codex, local models, and Perplexity.

## Why this exists

Herdr already *is* the interface. It gives you real PTYs per agent, semantic
blocked/working/done state, persistence when the laptop closes, remote attach, a
CLI/socket API, and first-class integrations for Claude Code, Codex, OpenCode and
others. It even surfaces Claude's 5h/Week bars on a Claude pane.

What it doesn't do is reason **across vendors**. With a hybrid stack you're
running several *independent meters* — a Max wallet, a Plus window, a free local
model, a Perplexity subscription — and the question stops being "which pane?" and
becomes **"which meter has headroom, and where should this task go?"**

That's the whole scope of this plugin. It adds the layer above Herdr's panes and
nothing else.

## What you get

| | |
|---|---|
| `board` | one table: every meter, its pane, its state, what it's good at |
| `picker` | popup — pick a meter, jump to (or start) its pane |
| `dispatch` | triage → route → send: picks provider, model, **and effort** |
| `classify` | explain the routing decision for a task without dispatching |
| `mark` | flag the focused pane's meter as rate-limited; dispatch routes around it |
| `research` | open the Perplexity Pro lane (app-only — it can't be a pane) |

## The classifier

A free local model (`qwen2.5-coder:7b` by default) picks the target — provider,
model, *and* effort level — from `models.json`. Three jobs, cheapest first:

1. **Triage.** Is the task specified well enough to dispatch? This runs first
   because the tokens a hybrid stack actually wastes are mostly not misrouting —
   they're an expensive agent burning a turn to ask "which file?". Catching that
   locally is free; catching it on Opus is not.
2. **Route.** Cheapest target whose ceiling clearly covers the task.
3. **Shape.** Normalize the prompt to the target's conventions.

Four rules keep a 7B classifier from becoming the problem:

- **Deterministic rules run first and win.** Sensitive-data pins and explicit
  `@provider` overrides never reach the model. A small model must never be what
  decides whether PHI leaves the machine.
- **It asks; it doesn't rewrite.** It flags what's missing and proposes one
  clarifying question. It won't silently reinterpret your task — a small model
  reworking something it half-understands is worse than no rewriting at all.
- **Uncertainty escalates.** Confidence below threshold routes to a *higher*
  ceiling, never lower. Fail-up is cheap; a too-weak model failing a hard task
  costs two attempts.
- **It's advisory.** Every decision is printed before dispatch, scarce targets
  ask for confirmation, and the fail-up guard remains the real correctness
  mechanism.

Override in-line with `@local`, `@codex`, `@claude`, `@perplexity`. Set a
different classifier with `METERS_CLASSIFIER=<ollama model>`.

Keeping `models.json` current is the one maintenance chore — it's the single
place model names and effort levels live, so vendor drift is a one-file fix.

Dispatch policy: **free before metered, scarce last.** Local absorbs bulk work,
Codex takes overflow coding on its own window, Claude is reserved for deep repo
work and judgment. One rule isn't advisory — anything matching
clinical/PHI/student-record keywords is pinned to **local** and never leaves it.

## Install

```sh
herdr plugin install <you>/herdr-meters
herdr plugin action list --plugin meters.hybrid
herdr plugin pane open --plugin meters.hybrid --entrypoint picker
```

Local development:

```sh
herdr plugin link /path/to/herdr-meters
herdr plugin action invoke meters.hybrid.board
```

Bind the board to a key in your Herdr config:

```toml
[[keys.command]]
key = "prefix+m"
type = "plugin_action"
command = "meters.hybrid.board"
description = "meters"
```

## Configure

Copy the default meter list into your plugin config dir and edit:

```sh
herdr plugin config-dir meters.hybrid   # prints the path
```

Write `meters.json` there as `{"meters": [...]}`. Each entry:

```json
{"name": "codex", "kind": "pane", "cmd": "codex", "cost": "subscription",
 "classes": ["code", "quick"], "priority": 2, "scarce": false}
```

`kind: "app"` entries use a `url` template instead of `cmd` — for surfaces with no
CLI.

## Honest limits

- **Availability is observational, not authoritative.** No vendor exposes
  remaining quota through an API, so this reads pane output for rate-limit hints
  and trusts what you `mark`. It's a good-enough signal for "stop typing into the
  spent lane" — not accounting. If a vendor ships a usage endpoint, that's the
  upgrade.
- **Perplexity's consumer tier can't be a pane.** Deep Research (the Opus-powered
  path that costs no Claude quota) is app-only; its Sonar API is a *different,
  metered* product. `research` opens the app rather than pretending otherwise.
- **Pane discovery is best-effort** — it matches the command running in a pane and
  degrades to "no pane yet" rather than guessing.
- Requires `python3`. No other dependencies.

## Publish

Herdr's marketplace is an automatic index of public GitHub repos tagged with the
topic `herdr-plugin`, refreshed every 30 minutes. Add the topic and share
`herdr plugin install owner/repo`.
