from typing import Any

from core.client import HHClient
from models.vacancy import VacancyModel
from utils.logger import setup_logger

logger = setup_logger()


class HHParser:
    """Преобразует сырые данные из HH.ru в модель VacancyModel."""

    def __init__(self, client: HHClient):
        self.client = client

    def parse_vacancy(self, v: dict[str, Any]) -> VacancyModel:
        """Превращает сырой словарь вакансии в VacancyModel.

        Args:
            v: Сырой словарь вакансии из JSON HH.

        Returns:
            Заполненная модель VacancyModel.
        """
        company = v.get("company") or {}
        company_reviews = company.get("employerReviews") or {}
        comp = v.get("compensation") or {}
        pub_time_obj = v.get("publicationTime") or {}
        change_time_obj = v.get("lastChangeTime") or {}
        links_obj = v.get("links") or {}
        props_obj = v.get("vacancyProperties") or {}
        calc_states = props_obj.get("calculatedStates") or {}
        hh_props = calc_states.get("HH") or {}
        contracts_list = v.get("civilLawContracts", [])

        gph_formats = ""
        if contracts_list and isinstance(contracts_list[0], dict):
            formats = contracts_list[0].get("civilLawContractsElement", [])
            gph_formats = ", ".join(formats)

        currency = comp.get("currencyCode") or comp.get("currency")
        if currency == "RUR":
            currency = "RUB"

        resp = v.get("autoResponse") or {}

        publication_type = hh_props.get("filteredPropertyNames")
        if isinstance(publication_type, list):
            publication_type = ", ".join(publication_type)

        data = {
            "Название вакансии": v.get("name"),
            "Название компании": company.get("name"),
            "Проверенный работодатель": company.get("@trusted"),
            "Категория компании": company.get("@category"),
            "ИТ-аккредитация": company.get("accreditedITEmployer"),
            "Рейтинг компании": company_reviews.get("totalRating"),
            "Количество отзывов": company_reviews.get("reviewsCount"),
            "Зарплата от": comp.get("from"),
            "Зарплата до": comp.get("to"),
            "Валюта": currency,
            "До вычета налогов": comp.get("gross"),
            "Дата публикации": pub_time_obj.get("$"),
            "Дата обновления": change_time_obj.get("$"),
            "Дата создания": v.get("creationTime"),
            "Ссылка на вакансию": links_obj.get("desktop"),
            "Тип публикации": publication_type,
            "Оформление по ТК РФ": v.get("acceptLaborContract"),
            "Договоры ГПХ": gph_formats,
            "Принимает автоответ": resp.get("acceptAutoResponse"),
            "Количество откликов": v.get("responsesCount"),
            "Всего откликов": v.get("totalResponsesCount"),
            "Город": (v.get("area") or {}).get("name") or v.get("city"),
        }

        return VacancyModel(**data)

    def get_description(self, detail_html: str) -> str | None:
        """Извлекает описание из HTML страницы вакансии. (заглушка)

        Args:
            detail_html: HTML страницы вакансии.

        Returns:
            None — описание извлекается через fetch_json_from_html.
        """
        return None

    def get_search_count(self, data: dict[str, Any]) -> int:
        """Возвращает общее количество найденных вакансий.

        Args:
            data: Словарь с результатами поиска.

        Returns:
            Число вакансий (0, если ключ не найден).
        """
        return data.get("searchCounts", {}).get("value", 0)

    def get_vacancies(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Возвращает список сырых словарей вакансий из результатов поиска.

        Args:
            data: Словарь с результатами поиска.

        Returns:
            Список сырых вакансий.
        """
        return data.get("vacancySearchResult", {}).get("vacancies", [])
