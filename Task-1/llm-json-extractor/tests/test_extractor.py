import pytest

from src import ExtractionError, Invoice, extract
from src.providers import MockProvider


def test_invoice_repairs_then_validates():
    p = MockProvider()
    result = extract("x", "invoice", p)
    assert isinstance(result, Invoice)
    assert result.total == 440.0
    assert p.calls == 2  # first answer invalid, repaired on retry


def test_resume_repairs_then_validates():
    result = extract("x", "resume", MockProvider())
    assert result.full_name == "Nadia Rahman"


def test_fails_without_retries():
    with pytest.raises(ExtractionError):
        extract("x", "invoice", MockProvider(), max_retries=0)
