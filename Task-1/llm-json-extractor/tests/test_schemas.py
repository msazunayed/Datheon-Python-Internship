import pytest
from pydantic import ValidationError

from src.schemas import Invoice


def test_invoice_total_mismatch_rejected():
    with pytest.raises(ValidationError):
        Invoice(
            invoice_number="1", vendor_name="V", issue_date="2026-01-01", currency="usd",
            line_items=[{"description": "a", "quantity": 1, "unit_price": 10, "total": 10}],
            subtotal=10, tax=1, total=99,
        )
