import pytest

from utils.ai_analyzer import AIAnalyzer


@pytest.fixture
def analyzer():
    return AIAnalyzer()


class TestCalculateTrustFactor:
    def test_high_trust(self, analyzer):
        assert analyzer._calculate_trust_factor(5.0, 100) == 1.0

    def test_low_reviews(self, analyzer):
        assert analyzer._calculate_trust_factor(5.0, 1) == pytest.approx(0.01)

    def test_no_reviews(self, analyzer):
        assert analyzer._calculate_trust_factor(5.0, None) == 0.1

    def test_no_rating(self, analyzer):
        assert analyzer._calculate_trust_factor(None, 50) == 0.1

    def test_zero_reviews(self, analyzer):
        assert analyzer._calculate_trust_factor(5.0, 0) == 0.1

    def test_half_rating(self, analyzer):
        assert analyzer._calculate_trust_factor(2.5, 100) == 0.5

    def test_medium_trust(self, analyzer):
        result = analyzer._calculate_trust_factor(4.0, 50)
        assert result == pytest.approx(0.4)


class TestCalculateCompetitionFactor:
    def test_no_competition(self, analyzer):
        assert analyzer._calculate_competition_factor(0) == 1.0

    def test_low_competition(self, analyzer):
        assert analyzer._calculate_competition_factor(50) == 0.75

    def test_high_competition(self, analyzer):
        assert analyzer._calculate_competition_factor(200) == 0.0

    def test_very_high_competition(self, analyzer):
        assert analyzer._calculate_competition_factor(500) == 0.0

    def test_none_responses(self, analyzer):
        assert analyzer._calculate_competition_factor(None) == 1.0


class TestParseLlmResponse:
    def test_valid_json(self, analyzer):
        text = '{"overall_score": 75, "explanation": "Good", "is_shitty": false}'
        result = analyzer._parse_llm_response(text)
        assert result["overall_score"] == 75
        assert result["explanation"] == "Good"

    def test_with_markdown_code_block(self, analyzer):
        text = (
            '```json\n{"overall_score": 80, "explanation": "Nice", '
            '"is_shitty": false}\n```'
        )
        result = analyzer._parse_llm_response(text)
        assert result["overall_score"] == 80

    def test_with_surrounding_text(self, analyzer):
        text = (
            'Some text before {"overall_score": 60, '
            '"explanation": "ok", "is_shitty": false} and after'
        )
        result = analyzer._parse_llm_response(text)
        assert result["overall_score"] == 60

    def test_trailing_comma_fix(self, analyzer):
        text = '{"overall_score": 70, "explanation": "OK", "is_shitty": false,}'
        result = analyzer._parse_llm_response(text)
        assert result["overall_score"] == 70

    def test_single_quotes_fix(self, analyzer):
        text = "{'overall_score': 65, 'explanation': 'Good', 'is_shitty': false}"
        result = analyzer._parse_llm_response(text)
        assert result["overall_score"] == 65

    def test_python_bool_fix(self, analyzer):
        text = '{"overall_score": 50, "explanation": "Bad", "is_shitty": True}'
        result = analyzer._parse_llm_response(text)
        assert result["is_shitty"] is True

    def test_invalid_json_returns_none(self, analyzer):
        result = analyzer._parse_llm_response("not json at all")
        assert result is None

    def test_empty_string_returns_none(self, analyzer):
        result = analyzer._parse_llm_response("")
        assert result is None


class TestDefaultErrorResult:
    def test_returns_zero_score(self, analyzer):
        result = analyzer._default_error_result("connection failed")
        assert result["overall_score"] == 0

    def test_returns_shitty(self, analyzer):
        result = analyzer._default_error_result("error")
        assert result["is_shitty"] is True

    def test_includes_error_message(self, analyzer):
        result = analyzer._default_error_result("timeout")
        assert "timeout" in result["explanation"]
