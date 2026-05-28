import json
import os
import sys

from rich.prompt import Confirm

from core.client import HHClient
from core.parser import HHParser
from crawler.scanner import HHScanner
from utils.config import config
from utils.exporter import ExcelExporter
from utils.logger import setup_logger


def main() -> int:
    """Запускает полный цикл: сканирование, экспорт, AI-анализ.

    Returns:
        0 при успехе, 1 если данные не собраны.
    """
    logger = setup_logger()
    logger.info("Запуск приложения...")

    client = HHClient()
    parser = HHParser(client)
    exporter = ExcelExporter()
    scanner = HHScanner(client, parser, exporter)

    # Определяем, есть ли уже данные и нужно ли обновлять
    existing_ids: set[str] | None = None
    refresh = config.get("search_settings.refresh_existing", False)
    if os.path.exists(exporter.excel_path):
        existing_ids = exporter.get_existing_ids()
        if existing_ids:
            if refresh:
                if not Confirm.ask(
                    "[bold yellow]Обновить данные по существующим вакансиям?[/]",
                    default=False,
                ):
                    refresh = False
                # Даже если юзер отказался — existing_ids остаются, скипаем детали
            logger.info(
                f"Найдено {len(existing_ids)} существующих вакансий. "
                f"{'Будет выполнено обновление.' if refresh else 'Новые вакансии будут добавлены без повторного обхода.'}"
            )

    try:
        vacancies = scanner.scan(existing_ids=existing_ids, refresh=refresh)
    except KeyboardInterrupt:
        logger.warning("Сканирование прервано пользователем.")
        vacancies = []
    except Exception as e:
        logger.error(f"Произошла непредвиденная ошибка: {e}")
        vacancies = []

    if vacancies:
        output_folder = config.get_output_folder()
        os.makedirs(output_folder, exist_ok=True)
        json_file = os.path.join(
            output_folder,
            config.get("output_settings.filename", "vacancies_full_data.json"),
        )
        try:
            records = [v.model_dump(by_alias=True) for v in vacancies]
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=4)
            logger.info(f"JSON данные сохранены в {json_file}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении JSON: {e}")

        try:
            exporter.export(vacancies)
        except Exception as e:
            logger.error(f"Ошибка при экспорте в Excel: {e}")

        if config.get("ai_settings.enabled", False):
            try:
                from utils.ai_analyzer import AIAnalyzer

                analyzer = AIAnalyzer()
                analyzer.analyze(exporter.excel_path)
            except Exception as e:
                logger.error(f"Ошибка при AI-анализе: {e}")
    else:
        logger.warning("Данные не были собраны. Файлы не созданы.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
