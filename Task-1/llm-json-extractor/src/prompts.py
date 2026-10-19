#Parameterized prompt templates with few-shot examples
from __future__ import annotations

import json
from string import Template
from typing import Type

from pydantic import BaseModel

SYSTEM_TEMPLATE = Template(
    """You are a precise information-extraction engine.
Extract data from the user's $doc_type text and return ONLY a single JSON object.
Rules:
- Output must validate against the JSON Schema below. No prose, no markdown fences.
- Use null for missing optional fields; never invent values.
- Dates: ISO format YYYY-MM-DD (resume job dates: YYYY-MM).
- Numbers are plain numbers (no currency symbols or thousands separators).

JSON Schema:
$schema
"""
)

FEW_SHOTS = {
    "invoice": [
        (
            "INVOICE #A-100\nFrom: Bolt Supplies Ltd\nBill to: Rina Das\n"
            "Date: 2026-03-02  Due: 2026-03-16\n"
            "2 x Steel bolt pack @ 12.50 = 25.00\n"
            "Subtotal 25.00  Tax 2.50  Total 27.50 USD",
            {
                "invoice_number": "A-100",
                "vendor_name": "Bolt Supplies Ltd",
                "customer_name": "Rina Das",
                "issue_date": "2026-03-02",
                "due_date": "2026-03-16",
                "currency": "USD",
                "line_items": [
                    {"description": "Steel bolt pack", "quantity": 2,
                     "unit_price": 12.5, "total": 25.0}
                ],
                "subtotal": 25.0,
                "tax": 2.5,
                "total": 27.5,
            },
        )
    ],
    "resume": [
        (
            "Samira Khan | samira@example.com | Dhaka\n"
            "Python developer. Skills: Python, SQL, Docker\n"
            "Acme Corp - Backend Engineer (Jan 2022 - present): built REST APIs\n"
            "BSc Computer Science, BUET, 2021",
            {
                "full_name": "Samira Khan",
                "email": "samira@example.com",
                "phone": None,
                "location": "Dhaka",
                "summary": "Python developer.",
                "skills": ["Python", "SQL", "Docker"],
                "experience": [
                    {"company": "Acme Corp", "title": "Backend Engineer",
                     "start_date": "2022-01", "end_date": None,
                     "highlights": ["Built REST APIs"]}
                ],
                "education": [
                    {"institution": "BUET", "degree": "BSc Computer Science", "year": 2021}
                ],
            },
        )
    ],
}


def build_system_prompt(doc_type: str, model: Type[BaseModel]) -> str:
    return SYSTEM_TEMPLATE.substitute(
        doc_type=doc_type, schema=json.dumps(model.model_json_schema(), indent=2)
    )


def build_messages(doc_type: str, model: Type[BaseModel], text: str) -> list[dict]:
    """Return chat-style messages: system, few-shot pairs, then the real input."""
    messages = [{"role": "system", "content": build_system_prompt(doc_type, model)}]
    for example_in, example_out in FEW_SHOTS[doc_type]:
        messages.append({"role": "user", "content": f"Text:\n{example_in}"})
        messages.append({"role": "assistant", "content": json.dumps(example_out)})
    messages.append({"role": "user", "content": f"Text:\n{text}"})
    return messages


def build_repair_message(error: str) -> dict:
    return {
        "role": "user",
        "content": (
            "Your previous output failed validation:\n"
            f"{error}\n"
            "Return a corrected JSON object only."
        ),
    }
