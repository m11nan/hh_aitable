
from pydantic import BaseModel, ConfigDict, Field


class VacancyModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(alias="Название вакансии")
    company_name: str | None = Field(default=None, alias="Название компании")
    is_trusted_employer: bool | None = Field(
        default=None, alias="Проверенный работодатель"
    )
    company_category: str | None = Field(default=None, alias="Категория компании")
    it_accredited: bool | None = Field(default=None, alias="ИТ-аккредитация")
    company_rating: float | None = Field(default=None, alias="Рейтинг компании")
    reviews_count: int | None = Field(default=None, alias="Количество отзывов")
    salary_from: float | None = Field(default=None, alias="Зарплата от")
    salary_to: float | None = Field(default=None, alias="Зарплата до")
    currency: str | None = Field(default=None, alias="Валюта")
    is_gross: bool | None = Field(default=None, alias="До вычета налогов")
    publication_date: str | None = Field(default=None, alias="Дата публикации")
    update_date: str | None = Field(default=None, alias="Дата обновления")
    creation_date: str | None = Field(default=None, alias="Дата создания")
    vacancy_link: str | None = Field(default=None, alias="Ссылка на вакансию")
    publication_type: str | list[str] | None = Field(
        default=None, alias="Тип публикации"
    )
    accepts_labor_contract: bool | None = Field(
        default=None, alias="Оформление по ТК РФ"
    )
    civil_law_contracts: str | None = Field(default=None, alias="Договоры ГПХ")
    accepts_auto_response: bool | None = Field(
        default=None, alias="Принимает автоответ"
    )
    responses_count: int | None = Field(default=None, alias="Количество откликов")
    total_responses: int | None = Field(default=None, alias="Всего откликов")
    city: str | None = Field(default=None, alias="Город")
    description: str | None = Field(default=None, alias="Описание")
