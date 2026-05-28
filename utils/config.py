from pathlib import Path
from typing import Any

import yaml


class Config:
    """Управляет конфигурацией приложения из YAML-файла."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config: dict[str, Any] = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Загружает и парсит YAML-файл конфигурации.

        Returns:
            Словарь с настройками.

        Raises:
            FileNotFoundError: Если файл не найден.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Конфигурационный файл не найден: {self.config_path}"
            )

        with open(self.config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get(self, key_path: str, default: Any = None) -> Any:
        """Получает значение по пути через точку (например, 'search_settings.max_pages').

        Args:
            key_path: Путь к ключу, разделённый точками.
            default: Значение по умолчанию, если ключ не найден.

        Returns:
            Значение из конфига или default.
        """
        keys = key_path.split(".")
        value = self._config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def get_output_folder(self) -> str:
        """Возвращает путь к папке вывода (по умолчанию 'output').

        Returns:
            Путь к папке вывода.
        """
        return self.get("output_settings.output_folder", "output")


config = Config()
