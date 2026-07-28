"""Tests for src/portage/render_config.py and validate_env.py (HB-0 Gate 1).

Hermetic: no network, no model calls, no live Ollama/Postgres needed — this
tests the renderer's own logic against small in-memory registries. The engine
repo's real Gate-1 evidence (against the checked-in sanitized example) is the
`--check` invocation wired into CI; see .github/workflows/portage-ci.yml.
"""

import json

import pytest
import yaml
from conftest import SCRIPTS, _load

render_config = pytest.fixture(
    lambda: _load("render_config_under_test", SCRIPTS / "render_config.py")
)
validate_env = pytest.fixture(
    lambda: _load("validate_env_under_test", SCRIPTS / "validate_env.py")
)


@pytest.fixture
def schema():
    schema_path = SCRIPTS.parent.parent / "schema" / "registry.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _entry(**overrides):
    base = {
        "alias": "embedding",
        "provider_route": "ollama_chat",
        "model_id": "nomic-embed-text",
        "endpoint": "os.environ/NODE_A",
        "open_weight": True,
        "license": "Apache-2.0",
        "max_context": 8192,
        "supports_tools": False,
        "supports_json": False,
        "data_classification": "public",
        "benchmark_version": None,
        "bfclv3": None,
        "ifeval": None,
        "enabled": True,
    }
    base.update(overrides)
    return base


class TestSchemaValidation:
    def test_valid_registry_passes(self, render_config, schema):
        registry = {"models": [_entry()]}
        assert render_config.validate_schema(registry, schema) == []

    def test_unknown_alias_rejected(self, render_config, schema):
        registry = {"models": [_entry(alias="made_up_alias")]}
        errors = render_config.validate_schema(registry, schema)
        assert any("made_up_alias" in e for e in errors)

    def test_ollama_chat_without_endpoint_rejected(self, render_config, schema):
        entry = _entry()
        del entry["endpoint"]
        registry = {"models": [entry]}
        errors = render_config.validate_schema(registry, schema)
        assert any("endpoint" in e for e in errors)

    def test_missing_required_field_rejected(self, render_config, schema):
        entry = _entry()
        del entry["license"]
        registry = {"models": [entry]}
        errors = render_config.validate_schema(registry, schema)
        assert any("license" in e for e in errors)


class TestCrossEntryValidation:
    def test_duplicate_alias_without_order_rejected(self, render_config):
        models = [
            _entry(alias="code_small"),
            _entry(alias="code_small", model_id="other"),
        ]
        problems = render_config.validate_cross_entry(models)
        assert any("no `order`" in p for p in problems)

    def test_duplicate_alias_with_orders_ok(self, render_config):
        models = [
            _entry(alias="code_small", order=1),
            _entry(alias="code_small", model_id="other", order=2),
        ]
        assert render_config.validate_cross_entry(models) == []

    def test_duplicate_order_values_rejected(self, render_config):
        models = [
            _entry(alias="code_small", order=1),
            _entry(alias="code_small", model_id="other", order=1),
        ]
        problems = render_config.validate_cross_entry(models)
        assert any("duplicate `order`" in p for p in problems)

    def test_disabled_duplicate_does_not_require_order(self, render_config):
        # A disabled sibling shouldn't force the enabled entry to carry `order`.
        models = [
            _entry(alias="code_small"),
            _entry(alias="code_small", model_id="other", enabled=False),
        ]
        assert render_config.validate_cross_entry(models) == []


class TestRenderModelList:
    def test_disabled_entries_still_rendered_but_flagged(self, render_config):
        # Gate 2 requires /v1/models to list exactly the seven aliases, so a
        # disabled alias (e.g. proprietary_code before HB-2) must still show
        # up there — `enabled: false` is carried into model_info instead of
        # excluding the entry from model_list.
        models = [
            _entry(),
            _entry(
                alias="proprietary_code",
                provider_route="anthropic",
                model_id="claude-sonnet-5",
                endpoint=None,
                enabled=False,
            ),
        ]
        doc = render_config.render_model_list(models)
        names = [m["model_name"] for m in doc["model_list"]]
        assert names == ["embedding", "proprietary_code"]
        by_name = {m["model_name"]: m for m in doc["model_list"]}
        assert by_name["proprietary_code"]["model_info"]["enabled"] is False
        assert by_name["embedding"]["model_info"]["enabled"] is True

    def test_ollama_chat_route(self, render_config):
        doc = render_config.render_model_list([_entry()])
        params = doc["model_list"][0]["litellm_params"]
        assert params["model"] == "ollama_chat/nomic-embed-text"
        assert params["api_base"] == "os.environ/NODE_A"

    def test_openrouter_route_uses_env_key(self, render_config):
        entry = _entry(
            alias="code_large",
            provider_route="openrouter",
            model_id="z-ai/glm-5.2",
            endpoint=None,
            order=1,
        )
        doc = render_config.render_model_list([entry])
        params = doc["model_list"][0]["litellm_params"]
        assert params["model"] == "openrouter/z-ai/glm-5.2"
        assert params["api_key"] == "os.environ/OPENROUTER_API_KEY"


class TestValidateEnv:
    def test_missing_vars_reported(self, validate_env, tmp_path, monkeypatch):
        config = tmp_path / "config.yaml"
        model_list = tmp_path / "model_list.generated.yaml"
        model_list.write_text(
            yaml.safe_dump(
                {"model_list": [{"litellm_params": {"api_key": "os.environ/NEEDS_ME"}}]}
            )
        )
        config.write_text(
            yaml.safe_dump(
                {
                    "include": ["model_list.generated.yaml"],
                    "general_settings": {"master_key": "os.environ/ALSO_NEEDED"},
                }
            )
        )
        monkeypatch.delenv("NEEDS_ME", raising=False)
        monkeypatch.delenv("ALSO_NEEDED", raising=False)
        doc = validate_env.load_with_includes(config)
        refs = validate_env.collect_env_refs(doc)
        assert refs == {"NEEDS_ME", "ALSO_NEEDED"}

    def test_all_vars_present(self, validate_env, tmp_path, monkeypatch):
        config = tmp_path / "config.yaml"
        model_list = tmp_path / "model_list.generated.yaml"
        model_list.write_text(yaml.safe_dump({"model_list": []}))
        config.write_text(
            yaml.safe_dump(
                {
                    "include": ["model_list.generated.yaml"],
                    "general_settings": {"master_key": "os.environ/PRESENT_VAR"},
                }
            )
        )
        monkeypatch.setenv("PRESENT_VAR", "x")
        doc = validate_env.load_with_includes(config)
        refs = validate_env.collect_env_refs(doc)
        assert refs == {"PRESENT_VAR"}
        assert all(v in __import__("os").environ for v in refs)
