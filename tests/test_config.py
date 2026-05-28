import pytest
import yaml

from utils.config import Config


@pytest.fixture
def config(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_data = {
        "search_settings": {"max_pages": 2, "base_url": "https://hh.ru"},
        "output_settings": {"output_folder": "output", "excel_filename": "report.xlsx"},
        "ai_settings": {
            "enabled": True,
            "model": {"path": "models/model.gguf"},
            "inference": {"max_tokens": 1500},
        },
    }
    with open(cfg_file, "w", encoding="utf-8") as f:
        yaml.dump(cfg_data, f)
    return Config(str(cfg_file))


class TestConfig:
    def test_get_existing_key(self, config):
        assert config.get("search_settings.max_pages") == 2

    def test_get_nested_key(self, config):
        assert config.get("search_settings.base_url") == "https://hh.ru"

    def test_get_missing_key_returns_default(self, config):
        assert config.get("nonexistent.key", "default") == "default"

    def test_get_missing_key_no_default(self, config):
        assert config.get("nonexistent.key") is None

    def test_get_partial_path_returns_dict(self, config):
        result = config.get("search_settings")
        assert isinstance(result, dict)
        assert result["max_pages"] == 2

    def test_get_output_folder(self, config):
        assert config.get_output_folder() == "output"

    def test_ai_enabled(self, config):
        assert config.get("ai_settings.enabled") is True

    def test_ai_model_path(self, config):
        assert config.get("ai_settings.model.path") == "models/model.gguf"

    def test_ai_max_tokens(self, config):
        assert config.get("ai_settings.inference.max_tokens") == 1500
