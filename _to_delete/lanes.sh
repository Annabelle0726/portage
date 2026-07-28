#!/usr/bin/env bash
# Herdr surface for the personal hybrid: one pane per METER.
#
# Herdr multiplies SESSIONS, not quota — but here each pane draws a DIFFERENT
# meter, so parallel panes genuinely add capacity instead of racing each other
# for one wallet. That is the whole point of the hybrid.
#
#   pane 1  claude   — scarce wallet, deep repo work
#   pane 2  codex    — separate ChatGPT Plus 5h window
#   pane 3  local    — free, unlimited, private
#
# Perplexity has no pane: the consumer tier is app-only (`ai research` opens it).
set -euo pipefail

REPO="${1:-$HOME/dev/taskcapture}"

herdr workspace create --cwd "$REPO" --label hybrid

herdr pane run 1-1 "claude"                    # Max wallet — spend deliberately
herdr pane run 1-2 "codex"                     # Plus window — the second lane
herdr pane run 1-3 "ollama run qwen2.5-coder:32b"   # free floor

# Serialize only WITHIN a meter, not across them:
#   two claude panes race the same wallet -> don't.
#   claude + codex in parallel -> fine, different meters.
#   herdr wait agent-status 1-1 --status done
#
# Watch the 5h/Week bars Herdr surfaces on the claude pane; when they're low,
# push work to pane 1-2 (codex) or 1-3 (local) instead of waiting.

echo "hybrid up: claude(scarce) | codex(2nd meter) | local(free)."
echo "research -> herdr plugin action invoke meters.hybrid.research  (Perplexity Pro, app-only)"
