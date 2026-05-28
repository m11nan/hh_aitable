# hh_aitable

Парсер вакансий с [HH.ru](https://hh.ru) с AI-анализом на локальной LLM.

Собирает вакансии по фильтрам, сохраняет в Excel, затем прогоняет через LLM
(llama.cpp) для оценки каждой вакансии.

---

## Требования

- **Python** 3.11+
- **UV** — менеджер пакетов (`pip install uv`)
- **NVIDIA GPU** с драйвером 12.x+ (рекомендуется, но CPU тоже работает)

---

## Установка

```bash
git clone https://github.com/m11nan/hh_aitable.git
cd hh_aitable
uv sync
cp config.example.yaml config.yaml
# Отредактируйте config.yaml под себя
```

---

## Конфигурация (`config.yaml`)

| Параметр | Описание |
|---|---|
| `search_settings.search_url_template` | URL поиска HH.ru (свои фильтры) |
| `search_settings.max_pages` | Количество страниц (`-1` = все) |
| `search_settings.refresh_existing` | `false` — быстрый повторный запуск (без перезапроса описаний). `true` — запросить обновление у пользователя |
| `ai_settings.enabled` | Включить AI-анализ после сбора |
| `ai_settings.model.path` | Путь к GGUF-модели |

Остальные параметры имеют разумные значения по умолчанию.

---

## Использование

```bash
uv run main.py
```

**Повторный запуск** — новые вакансии добавляются, известные пропускаются
(без повторного обхода описаний).

**Принудительное обновление** — в `config.yaml` поставить `refresh_existing: true`.
При запуске будет вопрос: обновить данные по существующим вакансиям?

```bash
# Без AI-анализа (если модель ещё не готова)
# В config.yaml: ai_settings.enabled: false
uv run main.py
```

---

## Структура

```
hh_aitable/
├── core/                 # Сетевой клиент + парсер HTML/JSON
├── crawler/              # Оркестрация сканирования (пагинация, прогресс-бары)
├── models/               # Pydantic-модели данных
├── utils/                # Экспорт, AI-анализ, конфиг, логирование
├── tests/                # Тесты (pytest)
├── .github/workflows/    # CI (ruff → basedpyright → pytest)
├── config.example.yaml   # Шаблон конфига (без личных данных)
├── main.py               # Точка входа
└── pyproject.toml        # Зависимости и инструменты
```

---

## Разработка

```bash
uv run ruff check          # Линтер
uv run basedpyright        # Тип-чекер
uv run pytest              # Тесты
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
