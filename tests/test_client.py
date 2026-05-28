import pytest

from core.client import HHClient


@pytest.fixture
def client():
    return HHClient()


class TestFetchJsonFromHtml:
    def test_empty_html_returns_none(self, client):
        assert client.fetch_json_from_html("") is None

    def test_none_html_returns_none(self, client):
        assert client.fetch_json_from_html(None) is None

    def test_no_marker_returns_none(self, client):
        assert client.fetch_json_from_html("<html></html>") is None

    def test_extracts_json_by_marker(self, client):
        html = '<script>window.__INITIAL_STATE__={"redirectConfig":{"key":"val"}}</script>'
        result = client.fetch_json_from_html(html)
        assert result is not None
        assert result["redirectConfig"]["key"] == "val"

    def test_with_surrounding_content(self, client):
        html = (
            '<html><body><script>var data = {"redirectConfig":{"page":1}};</script></body></html>'
        )
        result = client.fetch_json_from_html(html)
        assert result is not None
        assert result["redirectConfig"]["page"] == 1
