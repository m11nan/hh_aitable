import json
import random
import time
from typing import Any

import chompjs
from curl_cffi import requests

from utils.config import config
from utils.logger import setup_logger

logger = setup_logger()


class HHClient:
    """Низкоуровневый клиент для запросов к HH.ru."""

    def __init__(self):
        """Загружает настройки из конфига: base_url, заголовки, таймауты, повторы."""
        self.base_url = config.get("search_settings.base_url", "https://spb.hh.ru")
        self.headers = config.get("request_settings.headers")
        self.timeout = config.get("request_settings.timeout", 30)
        self.json_marker = '{"redirectConfig"'
        self.max_retries = config.get("request_settings.retry_settings.max_retries", 3)
        self.backoff_factor = config.get(
            "request_settings.retry_settings.backoff_factor", 2.0
        )

    def _get_random_delay(self, delay_key: str) -> float:
        """Возвращает случайную задержку из конфига по ключу.

        Args:
            delay_key: Ключ в search_settings (например, delay_between_pages).

        Returns:
            Случайное число секунд или значение из конфига.
        """
        delay_cfg = config.get(f"search_settings.{delay_key}")
        if isinstance(delay_cfg, dict):
            return random.uniform(delay_cfg.get("min", 1.0), delay_cfg.get("max", 2.0))
        return delay_cfg if isinstance(delay_cfg, (int, float)) else 1.0

    def fetch_raw_html(self, url: str) -> str | None:
        """Загружает HTML страницы с повторными попытками.

        Args:
            url: Адрес страницы.

        Returns:
            HTML как строка или None при ошибке.
        """
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    impersonate="chrome",
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.text
            except Exception as e:
                if attempt < self.max_retries:
                    sleep_time = self.backoff_factor**attempt
                    logger.warning(
                        f"Ошибка при запросе к {url} (попытка {attempt + 1}/{self.max_retries + 1}). Повтор через {sleep_time:.1f}с. Ошибка: {e}"
                    )
                    time.sleep(sleep_time)
                else:
                    logger.error(
                        f"Не удалось загрузить {url} после {self.max_retries + 1} попыток. Ошибка: {e}"
                    )
        return None

    def fetch_json_from_html(self, html: str) -> dict[str, Any] | None:
        """Извлекает JSON из HTML по маркеру redirectConfig.

        Args:
            html: Содержимое HTML страницы.

        Returns:
            Словарь с данными или None, если JSON не найден.
        """
        if not html:
            return None

        start_idx = html.find(self.json_marker)
        if start_idx == -1:
            return None

        try:
            decoder = json.JSONDecoder()
            parsed_data, _ = decoder.raw_decode(html[start_idx:])
            return parsed_data
        except json.JSONDecodeError:
            try:
                return chompjs.parse_js_object(html[start_idx:])
            except Exception as e:
                logger.error(f"Ошибка парсинга JSON из HTML: {e}")
                return None
