import datetime
import html
import os
import re
from typing import Any

import pandas as pd

from models.vacancy import VacancyModel
from utils.config import config
from utils.logger import setup_logger
from utils.progress_helper import make_progress

logger = setup_logger()


class ExcelExporter:
    """Экспортирует данные вакансий в Excel с форматированием и дозаписью."""

    def __init__(self):
        """Загружает настройки путей из конфига, создаёт папку вывода."""
        self.output_folder = config.get_output_folder()
        os.makedirs(self.output_folder, exist_ok=True)

        self.excel_path = os.path.join(
            self.output_folder,
            config.get("output_settings.excel_filename", "report.xlsx"),
        )
        self.json_path = os.path.join(
            self.output_folder,
            config.get("output_settings.filename", "vacancies_full_data.json"),
        )

        self.header_color = config.get("output_settings.header_color_hex", "#C1E1C1")

    def _clean_html(self, html_content: str | None) -> str:
        """Удаляет HTML-теги и декодирует HTML-entities.

        Args:
            html_content: Сырой HTML или None.

        Returns:
            Очищенный текст.
        """
        if not html_content:
            return ""
        html_content = html.unescape(html_content)
        html_content = re.sub(
            r"</p>|</li>|<br\s*/?>", "\n", html_content, flags=re.IGNORECASE
        )
        clean_text = re.sub(r"<[^>]*>", "", html_content)
        clean_text = re.sub(r"[ \t]+", " ", clean_text)
        clean_text = re.sub(r"\n+", "\n", clean_text).strip()
        return clean_text

    def _map_salary_type(self, v: dict[str, Any]) -> str:
        """Определяет тип зарплаты: ОТ, ДО или Диапазон.

        Args:
            v: Словарь с ключами salary_from и salary_to.

        Returns:
            Строка: Диапазон, ОТ, ДО или Не указана.
        """
        salary_from = v.get("salary_from")
        salary_to = v.get("salary_to")

        if salary_from and salary_to:
            return "Диапазон"
        if salary_from:
            return "ОТ"
        if salary_to:
            return "ДО"
        return "Не указана"

    def _get_id(self, vacancy: VacancyModel) -> str:
        """Извлекает ID вакансии из ссылки.

        Args:
            vacancy: Модель вакансии.

        Returns:
            ID как строка или пустая строка.
        """
        if not vacancy.vacancy_link:
            return ""
        return self._get_id_from_url(vacancy.vacancy_link)

    @staticmethod
    def _get_id_from_url(link: str) -> str:
        """Извлекает ID из URL вакансии (последний сегмент).

        Args:
            link: Ссылка на вакансию.

        Returns:
            ID как строка или пустая строка.
        """
        if not link:
            return ""
        return link.rstrip("/").split("/")[-1]

    def get_existing_ids(self) -> set[str]:
        """Читает уже записанные ID из существующего Excel-файла.

        Returns:
            Набор ID или пустое множество.
        """
        if not os.path.exists(self.excel_path):
            return set()
        try:
            df = pd.read_excel(self.excel_path)
            ids = {self._get_id_from_url(link) for link in df["Ссылка"].dropna()}
            return ids
        except Exception as e:
            logger.warning(
                f"Не удалось прочитать существующий Excel-файл: {e}. Дублирование будет отключено."
            )
            return set()

    def get_existing_description(self, vacancy_id: str) -> str | None:
        """Возвращает описание вакансии из Excel по её ID.

        Args:
            vacancy_id: ID вакансии.

        Returns:
            Описание или None, если не найдено.
        """
        if not os.path.exists(self.excel_path):
            return None
        try:
            df = pd.read_excel(self.excel_path)
            for link, desc in zip(df["Ссылка"].dropna(), df["Описание"].dropna()):
                if self._get_id_from_url(link) == vacancy_id:
                    return desc
            return None
        except Exception:
            return None

    def _format_date(self, date_str: str | None) -> str:
        """Форматирует дату в DD.MM.YYYY HH:mm:ss.

        Args:
            date_str: Строка с датой (ISO или timestamp) или None.

        Returns:
            Отформатированная дата или N/A.
        """
        if not date_str:
            return "N/A"
        try:
            dt = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%d.%m.%Y %H:%M:%S")
        except Exception:
            return date_str

    def export(self, vacancies: list[VacancyModel]):
        """Основной метод экспорта с поддержкой дозаписи.

        Args:
            vacancies: Список вакансий для экспорта.
        """
        if not vacancies:
            logger.warning("Нет данных для экспорта.")
            return

        existing_ids = self.get_existing_ids()
        new_vacancies = [
            v for v in vacancies if self._get_id(v) not in existing_ids
        ]

        if not new_vacancies:
            logger.info("Новых вакансий для записи не найдено.")
            return

        logger.info(
            f"Найдено {len(vacancies)} вакансий, из них {len(new_vacancies)} новых и будет записано в файл."
        )

        with make_progress(
            "[bold magenta]Дозапись новых вакансий",
            total=len(new_vacancies),
            text_style="magenta",
            bar_style="magenta",
        ) as prog:
            write_task = prog.add_task(
                "Запись новых вакансий", total=len(new_vacancies)
            )
            rows = []

            for v in new_vacancies:
                employment_type = (
                    "Намешали"
                    if v.accepts_labor_contract and v.civil_law_contracts
                    else "ТКРФ"
                    if v.accepts_labor_contract
                    else "ГПХ"
                    if v.civil_law_contracts
                    else "Неизвестно"
                )
                row = {
                    "Вакансия": v.name,
                    "Компания": v.company_name,
                    "Тип Компании": v.company_category,
                    "Аккредитация": "Да" if v.it_accredited else "Нет",
                    "Верификация": "Да" if v.is_trusted_employer else "Нет",
                    "Рейтинг": v.company_rating if v.company_rating else "N/A",
                    "Отзывы": v.reviews_count if v.reviews_count else "N/A",
                    "Тип ТД": employment_type,
                    "Валюта": v.currency,
                    "Налоги": "До вычета" if v.is_gross else "На руки",
                    "Тип ЗП": self._map_salary_type(v.model_dump()),
                    "ЗП MIN": v.salary_from if v.salary_from else "-",
                    "ЗП MAX": v.salary_to if v.salary_to else "-",
                    "Отклики": v.responses_count if v.responses_count else 0,
                    "Отклики_Всего": v.total_responses or 0,
                    "Локация": v.city,
                    "ДТС (создание)": self._format_date(v.creation_date),
                    "ДТП (публикация)": self._format_date(v.publication_date),
                    "ДТО (обновление)": self._format_date(v.update_date),
                    "ДТ (сканирования)": datetime.datetime.now().strftime(
                        "%d.%m.%Y %H:%M:%S"
                    ),
                    "Описание": self._clean_html(v.description),
                    "Ссылка": v.vacancy_link,
                    "Поднятие": "Да" if v.publication_type and "HH_AUTO_RENEWAL" in v.publication_type else "Нет",
                    "Автоответы": "Включено"
                    if v.accepts_auto_response
                    else "Выключено",
                    "Аргументы": v.publication_type,
                    "AI_Score": None,
                    "AI_Verdict": None,
                    "AI_Status": None,
                    "AI_Error": None,
                }
                rows.append(row)
                prog.update(write_task, advance=1)

        if os.path.exists(self.excel_path):
            old_df = pd.read_excel(self.excel_path, engine="openpyxl")
            new_df = pd.DataFrame(rows)
            df = pd.concat([old_df, new_df], ignore_index=True)
        else:
            df = pd.DataFrame(rows)

        with pd.ExcelWriter(self.excel_path, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Вакансии")

        logger.info(f"Excel отчет успешно сохранен: {self.excel_path}")
