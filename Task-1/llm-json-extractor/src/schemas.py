#Pydantic schemas that define the strict JSON contract for each document type
from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class LineItem(BaseModel):
    description: str
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)
    total: float = Field(ge=0)


class Invoice(BaseModel):
    invoice_number: str
    vendor_name: str
    customer_name: Optional[str] = None
    issue_date: date
    due_date: Optional[date] = None
    currency: str = Field(min_length=3, max_length=3, description="ISO 4217 code")
    line_items: List[LineItem] = Field(min_length=1)
    subtotal: float = Field(ge=0)
    tax: float = Field(default=0, ge=0)
    total: float = Field(ge=0)

    @field_validator("currency")
    @classmethod
    def upper_currency(cls, v: str) -> str:
        return v.upper()

    @model_validator(mode="after")
    def check_totals(self) -> "Invoice":
        if abs(self.subtotal + self.tax - self.total) > 0.02:
            raise ValueError(
                f"subtotal ({self.subtotal}) + tax ({self.tax}) != total ({self.total})"
            )
        return self


class Experience(BaseModel):
    company: str
    title: str
    start_date: str = Field(description="YYYY-MM")
    end_date: Optional[str] = Field(default=None, description="YYYY-MM or null if current")
    highlights: List[str] = []


class Education(BaseModel):
    institution: str
    degree: str
    year: Optional[int] = Field(default=None, ge=1950, le=2100)


class Resume(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = Field(min_length=1)
    experience: List[Experience] = []
    education: List[Education] = []

    @field_validator("email")
    @classmethod
    def basic_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and ("@" not in v or "." not in v.split("@")[-1]):
            raise ValueError("invalid email")
        return v


SCHEMAS = {"invoice": Invoice, "resume": Resume}
