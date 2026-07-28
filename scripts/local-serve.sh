#!/usr/bin/env bash
# Run ON the always-on iMac. Keeps one model resident (no cold-load per call) and
# reachable from the MacBook and Jetstream2 over Tailscale — all three machines
# route to ONE warm model instead of each loading their own.
#
# Keep the weights on the internal SSD, not the external drive: which drive holds
# them affects cold-load time only, but a warm model that gets evicted will
# cold-load from wherever it lives, so an external drive turns eviction into a
# stall. -1 keep-alive avoids eviction entirely.
set -euo pipefail

export OLLAMA_HOST=0.0.0.0:11434     # listen on the tailnet, not just localhost
export OLLAMA_KEEP_ALIVE=-1          # never evict — stay warm

ollama serve &
sleep 2

ollama run qwen2.5-coder:32b ""      # T1 floor (used by the fail-up guard)
ollama run qwen2.5-coder:7b  ""      # T0 background + difficulty classifier

TSNAME="$(tailscale status --json 2>/dev/null | grep -o '"DNSName":"[^"]*' | head -1 | cut -d'"' -f4 || true)"
echo "Local models warm. Point litellm.config.yaml's local deployment api_base at:"
echo "  http://${TSNAME:-<imac-tailscale-name>}:11434"
