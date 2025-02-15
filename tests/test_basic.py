# tests/test_basic.py
import pytest
from jobs_applier.config import Config

def test_config_loading():
    config = Config("config.example.yaml")
    assert "linkedin" in config.data
    assert "search" in config.data

def test_llm_generation(monkeypatch):
    """
    Example test for LLM integration, mocking openai response.
    """
    from jobs_applier.llm_integration import generate_cover_letter

    class MockResponse:
        choices = [type("obj", (object,), {"text": "Mock cover letter"})()]

    def mock_completion_create(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr("openai.Completion.create", mock_completion_create)

    result = generate_cover_letter("Software Engineer", "Acme Corp", "Test JD", "My background")
    assert "Mock cover letter" in result

# Additional tests for multi-step forms, pagination, etc., can be placed in separate files.
