# hh_scraper

Парсер вакансий с [HH.ru](https://hh.ru) с AI-анализом на локальной LLM.

Собирает вакансии по заданным фильтрам, сохраняет в Excel, затем
прогоняет через локальную LLM (llama.cpp) для оценки каждой вакансии.

---

## Требования

- **Python** 3.11+
- **NVIDIA GPU** с драйвером 12.x+ (рекомендуется, но не обязательно — будет работать на CPU)
- **UV** — менеджер пакетов (`pip install uv`)

---

## Установка

```bash
# Клонируем репозиторий
git clone https://github.com/m11nan/hh_scraper
cd hh_scraper

# Устанавливаем зависимости
uv sync

# Настраиваем конфиг
cp config.example.yaml config.yaml
# Отредактируйте config.yaml под себя (см. ниже)
```

---

## Конфигурация

Скопируйте `config.example.yaml` в `config.yaml` и настройте:

- **search_settings.search_url_template** — URL поиска HH.ru (свои фильтры)
- **search_settings.max_pages** — количество страниц для сканирования
- **ai_settings.enabled** — `true` / `false`
- **ai_settings.model.path** — путь к GGUF-модели (для AI-анализа)
- Остальные параметры имеют разумные значения по умолчанию

---

## Использование

```bash
uv run python main.py
```

Без AI-анализа (если модель не готова):

```bash
# В config.yaml: ai_settings.enabled: false
uv run python main.py
```

---

## Структура проекта

```
hh_scraper/
├── core/           # Сетевой клиент и парсер HTML/JSON
├── crawler/        # Оркестрация сканирования
├── models/         # Pydantic-модели данных
├── utils/          # Экспорт, AI-анализ, конфиг, логирование
├── tests/          # Тесты (pytest)
├── config.example.yaml  # Шаблон конфига
├── main.py         # Точка входа
└── pyproject.toml  # Зависимости и инструменты
```

---

## Разработка

```bash
# Линтер
uv run ruff check

# Тип-чекер
uv run basedpyright

# Тесты
uv run pytest
```

---

## Технологии

- [curl_cffi](https://github.com/yifeikong/curl_cffi) — обход блокировок HH.ru
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) — локальный AI
- [Pydantic](https://docs.pydantic.dev/) — модели данных
- [Rich](https://rich.readthedocs.io/) — прогресс-бары
- [Loguru](https://loguru.readthedocs.io/) — логирование
- [OpenPyXL](https://openpyxl.readthedocs.io/) / [XlsxWriter](https://xlsxwriter.readthedocs.io/) — Excel

---

## Лицензия

MIT
