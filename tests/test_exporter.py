import pytest

from utils.exporter import ExcelExporter


@pytest.fixture
def exporter():
    return ExcelExporter()


class TestCleanHtml:
    def test_removes_simple_tags(self, exporter):
        assert exporter._clean_html("<p>Hello</p>") == "Hello"

    def test_removes_br_to_newline(self, exporter):
        result = exporter._clean_html("Line1<br/>Line2")
        assert result == "Line1\nLine2"

    def test_removes_entity_escaped_tags(self, exporter):
        result = exporter._clean_html("&lt;strong&gt;Bold&lt;/strong&gt;")
        assert result == "Bold"
        assert "<strong>" not in result

    def test_complex_html(self, exporter):
        html = (
            '<div class="desc"><p>First <strong>para</strong></p>'
            "<ul><li>Item 1</li><li>Item 2</li></ul></div>"
        )
        result = exporter._clean_html(html)
        assert "First" in result
        assert "para" in result
        assert "Item 1" in result
        assert "Item 2" in result
        assert "<" not in result

    def test_empty_input(self, exporter):
        assert exporter._clean_html("") == ""

    def test_none_input(self, exporter):
        assert exporter._clean_html(None) == ""

    def test_unescapes_entities(self, exporter):
        result = exporter._clean_html("AT&amp;T &amp; Co")
        assert result == "AT&T & Co"

    def test_no_html(self, exporter):
        assert exporter._clean_html("Plain text") == "Plain text"


class TestGetIdFromUrl:
    def test_from_link(self, exporter):
        assert exporter._get_id_from_url("https://spb.hh.ru/vacancy/123456") == "123456"

    def test_from_link_with_slash(self, exporter):
        assert exporter._get_id_from_url("https://spb.hh.ru/vacancy/123456/") == "123456"

    def test_from_link_empty(self, exporter):
        assert exporter._get_id_from_url("") == ""

    def test_from_link_none(self, exporter):
        assert exporter._get_id_from_url(None) == ""


class TestMapSalaryType:
    def test_range(self, exporter):
        d = {"salary_from": 100, "salary_to": 200}
        assert exporter._map_salary_type(d) == "Диапазон"

    def test_from_only(self, exporter):
        d = {"salary_from": 100, "salary_to": None}
        assert exporter._map_salary_type(d) == "ОТ"

    def test_to_only(self, exporter):
        d = {"salary_from": None, "salary_to": 200}
        assert exporter._map_salary_type(d) == "ДО"

    def test_not_specified(self, exporter):
        d = {"salary_from": None, "salary_to": None}
        assert exporter._map_salary_type(d) == "Не указана"

    def test_empty_dict(self, exporter):
        assert exporter._map_salary_type({}) == "Не указана"
