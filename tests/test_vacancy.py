# pyright: strict
from models.vacancy import VacancyModel


class TestVacancyModel:
    def test_create_minimal(self):
        v = VacancyModel.model_validate({"Название вакансии": "Developer"})
        assert v.name == "Developer"
        assert v.company_name is None

    def test_create_with_all_fields(self):
        v = VacancyModel.model_validate(
            {
                "Название вакансии": "Python Developer",
                "Название компании": "Tech Corp",
                "Зарплата от": 100000,
                "Зарплата до": 150000,
                "Валюта": "RUR",
                "До вычета налогов": True,
                "Описание": "<p>Great job</p>",
            }
        )
        assert v.name == "Python Developer"
        assert v.salary_from == 100000.0
        assert v.salary_to == 150000.0

    def test_serialize_to_dict(self):
        v = VacancyModel.model_validate(
            {"Название вакансии": "Test", "Название компании": "Test Corp"}
        )
        d = v.model_dump()
        assert d["name"] == "Test"
        assert d["company_name"] == "Test Corp"

    def test_serialize_with_aliases(self):
        v = VacancyModel.model_validate({"Название вакансии": "Test"})
        d = v.model_dump(by_alias=True)
        assert d["Название вакансии"] == "Test"

    def test_default_field_values(self):
        v = VacancyModel.model_validate({"Название вакансии": "Test"})
        assert v.it_accredited is None
        assert v.is_trusted_employer is None
        assert v.responses_count is None
        assert v.total_responses is None

    def test_accepts_labor_contract_default_none(self):
        v = VacancyModel.model_validate({"Название вакансии": "Test"})
        assert v.accepts_labor_contract is None

    def test_civil_law_contracts_default_none(self):
        v = VacancyModel.model_validate({"Название вакансии": "Test"})
        assert v.civil_law_contracts is None

    def test_publication_type_can_be_string(self):
        v = VacancyModel.model_validate(
            {
                "Название вакансии": "Test",
                "Тип публикации": "HH_AUTO_RENEWAL",
            }
        )
        assert v.publication_type == "HH_AUTO_RENEWAL"

    def test_publication_type_can_be_list(self):
        v = VacancyModel.model_validate(
            {
                "Название вакансии": "Test",
                "Тип публикации": ["HH_AUTO_RENEWAL"],
            }
        )
        assert isinstance(v.publication_type, list)
