#!/usr/bin/env bash
# Run ON the always-on iMac. Keeps ONE model resident (the warm steward) and
# reachable from the MacBook over Tailscale.
#
# Runtime policy (LINE-P-ROADMAP rev 2): OLLAMA_MAX_LOADED_MODELS=1 on both
# machines; keep-alive pinned (-1) on the iMac steward ONLY — the MacBook swaps
# under LRU and accepts the few-second cold start. For the launchd-managed
# menubar app, set env via `launchctl setenv` and restart the app; the exports
# below cover the foreground `ollama serve` path.
#
# Model pin: still the KNOWN_GOOD_VERSIONS interim entry (qwen2.5-coder — NOT
# INSTALLED; llama3.2 is what Phase 1 actually ran against). HB-0 pulls the
# standing three (Qwen3-Coder 7B, Gemma 4 E4B, embedder), smoke-tests tool
# calling per model, and updates this pin. Do not pre-pin uninstalled models.
set -euo pipefail

export OLLAMA_HOST=0.0.0.0:11434        # listen on the tailnet
export OLLAMA_KEEP_ALIVE=-1             # iMac steward: never evict
export OLLAMA_MAX_LOADED_MODELS=1       # one warm model per machine (policy)

ollama serve &
sleep 2

ollama run qwen2.5-coder:7b ""          # the single warm steward (see pin note)

TSNAME="$(tailscale status --json 2>/dev/null | grep -o '"DNSName":"[^"]*' | head -1 | cut -d'"' -f4 || true)"
echo "Steward warm. Point litellm.config.yaml's local deployment api_base at:"
echo "  http://${TSNAME:-<imac-tailscale-name>}:11434"
