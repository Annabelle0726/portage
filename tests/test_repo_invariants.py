"""Token-free repo invariants. No network, no model calls (HANDOFF Phase 2 rule).

Phase 0 needs `uv run pytest` green from day one. Rather than an empty stub, the
placeholder asserts the one invariant that is cheap to check and expensive to
regress: HANDOFF §6.3 — the sensitive pin is enforced by *config absence*, so
`litellm.sensitive.yaml` must contain only local deployments. Parsed as text on
purpose: the core package is stdlib-only, so this must not need a YAML reader.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

MODEL_RE = re.compile(r"^\s*model:\s*(\S+)", re.M)
API_BASE_RE = re.compile(r"^\s*api_base:\s*(\S+)", re.M)
API_KEY_RE = re.compile(r"^\s*api_key:\s*(\S+)", re.M)

LOCAL_HOSTS = ("http://localhost:", "http://127.0.0.1:")


def test_repo_root_is_sane():
    assert (REPO / "HANDOFF.md").is_file()
    assert (REPO / "litellm.config.yaml").is_file()


def test_sensitive_config_declares_only_local_models():
    text = (REPO / "litellm.sensitive.yaml").read_text(encoding="utf-8")
    models = MODEL_RE.findall(text)
    assert models, "sensitive config declares no models at all"
    offenders = [m for m in models if not m.startswith("ollama/")]
    assert not offenders, f"non-local model in the sensitive config: {offenders}"


def test_sensitive_config_points_only_at_localhost():
    text = (REPO / "litellm.sensitive.yaml").read_text(encoding="utf-8")
    bases = API_BASE_RE.findall(text)
    assert bases, "sensitive config declares no api_base at all"
    offenders = [b for b in bases if not b.startswith(LOCAL_HOSTS)]
    assert not offenders, f"off-machine api_base in the sensitive config: {offenders}"


def test_sensitive_config_carries_no_provider_credentials():
    # A per-deployment api_key here would mean a commercial endpoint slipped in.
    # The proxy's own master_key lives under general_settings and is not one.
    text = (REPO / "litellm.sensitive.yaml").read_text(encoding="utf-8")
    assert not API_KEY_RE.findall(text), "sensitive config carries a provider api_key"
