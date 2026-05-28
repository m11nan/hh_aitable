import html as html_mod
import math
import re
import time
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from rich.console import Console

from core.client import HHClient
from core.parser import HHParser
from models.vacancy import VacancyModel
from utils.config import get_config
from utils.exporter import ExcelExporter
from utils.logger import setup_logger
from utils.progress_helper import make_progress

logger = setup_logger()


class HHScanner:
    """Оркестратор: управляет пагинацией, обходом ссылок и прогресс-барами."""

    def __init__(self, client: HHClient, parser: HHParser, exporter: ExcelExporter | None = None):
        self.client = client
        self.parser = parser
        self.exporter = exporter
        self.console = Console()

    def scan(
        self,
        existing_ids: set[str] | None = None,
        refresh: bool = False,
    ) -> list[VacancyModel]:
        """Сканирует вакансии по страницам, собирает данные и описания.

        Args:
            existing_ids: Набор ID уже известных вакансий. Если передан —
                детальный обход (описание) для них пропускается.
            refresh: Если True — всё равно качает описание для существующих
                и сравнивает с сохранённым. Добавляет только если изменилось.

        Returns:
            Список собранных VacancyModel.
        """
        search_url_template = get_config().get("search_settings.search_url_template")
        max_pages = get_config().get("search_settings.max_pages", 1)

        if existing_ids:
            logger.info(f"Загружено {len(existing_ids)} существующих ID вакансий")
        else:
            logger.info("existing_ids не переданы — все вакансии будут загружены")

        all_vacancies: list[VacancyModel] = []

        # Первую страницу фетчим сразу — нужна для метаданных и первой порции вакансий
        logger.info("Инициализация: получение первой страницы...")
        first_page_html = self.client.fetch_raw_html(search_url_template)
        if not first_page_html:
            logger.error("Не удалось получить HTML первой страницы.")
            return []
        first_page_data = self.client.fetch_json_from_html(first_page_html)

        if not first_page_data:
            logger.error("Не удалось получить данные первой страницы.")
            return []

        total_count = self.parser.get_search_count(first_page_data)
        logger.info(f"Всего найдено вакансий в поиске: {total_count}")

        page_count = math.ceil(total_count / 50) if total_count else 1
        effective_pages = min(page_count, max_pages) if max_pages != -1 else page_count

        logger.info(f"Будет обработано страниц: {effective_pages}")

        with make_progress(
            "[bold cyan]Сканирование страниц",
            total=effective_pages,
            text_style="cyan",
            bar_style="cyan",
            console=self.console,
        ) as page_progress:
            page_task = page_progress.add_task("[bold cyan]Страницы", total=effective_pages)

            with make_progress(
                "[bold magenta]Обработка вакансий",
                total=total_count,
                text_style="magenta",
                bar_style="magenta",
                console=self.console,
            ) as vacancy_progress:
                vacancy_task = vacancy_progress.add_task(
                    "[bold magenta]Вакансии", total=total_count
                )

                page = 0
                while True:
                    if max_pages != -1 and page >= max_pages:
                        break

                    # Для page=0 используем уже полученные first_page_data
                    if page == 0:
                        page_data = first_page_data
                    else:
                        parsed = urlparse(search_url_template)
                        query = parse_qs(parsed.query, keep_blank_values=True)
                        query["page"] = [str(page)]
                        new_query = urlencode(query, doseq=True)
                        url: str = urlunparse(parsed._replace(query=new_query))

                        page_html = self.client.fetch_raw_html(url)
                        if not page_html:
                            logger.warning(f"Пропуск страницы {page} из-за ошибки загрузки.")
                            page_progress.advance(page_task)
                            continue
                        page_data = self.client.fetch_json_from_html(page_html)

                        if not page_data:
                            logger.warning(f"Пропуск страницы {page} из-за ошибки.")
                            page_progress.advance(page_task)
                            continue

                    vacancies_raw = self.parser.get_vacancies(page_data)
                    if not vacancies_raw:
                        logger.info(f"Больше вакансий не найдено на странице {page}. Завершаем.")
                        break

                    page_skipped = 0
                    page_fetched = 0
                    for v_raw in vacancies_raw:
                        vacancy = self.parser.parse_vacancy(v_raw)
                        vacancy_id = str(v_raw.get("id", ""))
                        old_desc: str | None = None

                        # Если вакансия уже известна — скипаем детальный обход
                        if existing_ids and vacancy_id in existing_ids:
                            if not refresh:
                                vacancy.description = None
                                all_vacancies.append(vacancy)
                                vacancy_progress.advance(vacancy_task)
                                page_skipped += 1
                                continue

                            # refresh: сравниваем новое описание со старым
                            old_desc = (
                                self.exporter.get_existing_description(vacancy_id)
                                if self.exporter
                                else None
                            )

                        page_fetched += 1

                        detail_url = v_raw.get("links", {}).get("desktop")
                        if detail_url:
                            if not detail_url.startswith("http"):
                                detail_url = self.client.base_url + detail_url
                            detail_html = self.client.fetch_raw_html(detail_url)
                            if not detail_html:
                                detail_data = None
                            else:
                                detail_data = self.client.fetch_json_from_html(detail_html)
                            if detail_data:
                                vacancy.description = detail_data.get("vacancyView", {}).get(
                                    "description"
                                )
                            else:
                                vacancy.description = "Не удалось загрузить описание"
                        else:
                            vacancy.description = "Ссылка не найдена"

                        # refresh: если описание не изменилось — скипаем
                        if (
                            existing_ids
                            and vacancy_id in existing_ids
                            and refresh
                            and old_desc is not None
                        ):
                            old_clean = (
                                html_mod.unescape(re.sub(r"<[^>]*>", "", old_desc))
                                if old_desc
                                else ""
                            )
                            new_clean = (
                                html_mod.unescape(re.sub(r"<[^>]*>", "", vacancy.description or ""))
                                if vacancy.description
                                else ""
                            )
                            if old_clean.strip() == new_clean.strip():
                                vacancy_progress.advance(vacancy_task)
                                continue

                        all_vacancies.append(vacancy)
                        vacancy_progress.advance(vacancy_task)
                        time.sleep(self.client._get_random_delay("delay_between_vacancies"))

                    if page_skipped or page_fetched:
                        logger.info(
                            f"Страница {page}: {page_skipped} вакансий пропущено"
                            f"{f', {page_fetched} загружено' if page_fetched else ''}"
                        )

                    page_progress.advance(page_task)
                    if page > 0:
                        time.sleep(self.client._get_random_delay("delay_between_pages"))
                    page += 1

        return all_vacancies
