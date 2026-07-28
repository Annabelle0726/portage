"""LiteLLM config READINESS, not just liveness.

Phase 1 found that a bad `model_info` key (the reserved `tier` field) makes
LiteLLM silently drop every offending deployment while `/health/liveliness`
still reports the proxy healthy — a proxy that answers healthy and routes
nothing is the worst failure mode this project can have. `commons_tier` fixed
that specific defect; this test guards against the *class* of regression by
asserting the actual deployment count a config loads with, not just that the
YAML parses.

Loads the Router in-process (no server, no port, no HTTP) so this is as fast
and network-free as the rest of the suite. Skips if the optional `proxy` extra
isn't installed — the milestone gate must not depend on a heavy dependency
that most contributors' environments (and CI's default `uv run pytest`) don't
have; run `uv sync --extra proxy` locally to exercise it.
"""

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")
litellm = pytest.importorskip("litellm")

REPO = Path(__file__).resolve().parent.parent


def _load(config_name: str):
    cfg = yaml.safe_load((REPO / config_name).read_text(encoding="utf-8"))
    router = litellm.Router(model_list=cfg["model_list"])
    return router.get_model_list()


def test_work_config_readiness():
    deployments = _load("litellm.config.yaml")
    assert len(deployments) == 12, (
        f"expected 12 deployments (5 rungs + 4 work + 2 judgment + 1 steward), "
        f"got {len(deployments)} — a silently dropped deployment is the exact "
        f"failure Phase 1 found (see KNOWN_GOOD_VERSIONS.md)"
    )
    by_name = {}
    for d in deployments:
        by_name.setdefault(d["model_name"], []).append(d)
    for rung in ("local-small", "local-big", "sovereign-work", "sonnet", "opus"):
        assert rung in by_name, f"rung '{rung}' failed to register"
        assert len(by_name[rung]) == 1, f"rung '{rung}' should be a single deployment"
    assert len(by_name["work"]) == 4
    assert len(by_name["judgment"]) == 2
    assert len(by_name["steward"]) == 1


def test_sensitive_config_readiness():
    deployments = _load("litellm.sensitive.yaml")
    assert len(deployments) == 3, (
        f"expected exactly 3 local-only deployments (work, judgment, steward), "
        f"got {len(deployments)}"
    )
    assert {d["model_name"] for d in deployments} == {"work", "judgment", "steward"}
