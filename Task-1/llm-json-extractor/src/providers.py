#LLM provider adapters. Each exposes complete(messages) -> str (raw JSON text)
from __future__ import annotations

import json
import os
from typing import Protocol


class Provider(Protocol):
    def complete(self, messages: list[dict]) -> str: ...


class OpenAIProvider:
    def __init__(self, model: str):
        from openai import OpenAI

        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = model

    def complete(self, messages: list[dict]) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content or ""


class GroqProvider(OpenAIProvider):
    #Groq exposes an OpenAI-compatible API, so we reuse the openai SDK.

    def __init__(self, model: str):
        from openai import OpenAI

        self.client = OpenAI(
            api_key=os.environ["GROQ_API_KEY"],
            base_url="https://api.groq.com/openai/v1",
        )
        self.model = model


class GeminiProvider:
    def __init__(self, model: str):
        import google.generativeai as genai

        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        self.genai = genai
        self.model_name = model
        self._system = None

    def complete(self, messages: list[dict]) -> str:
        system = next(m["content"] for m in messages if m["role"] == "system")
        model = self.genai.GenerativeModel(
            self.model_name,
            system_instruction=system,
            generation_config={
                "temperature": 0,
                "response_mime_type": "application/json",
            },
        )
        history = [
            {"role": "model" if m["role"] == "assistant" else "user",
             "parts": [m["content"]]}
            for m in messages
            if m["role"] != "system"
        ]
        resp = model.generate_content(history)
        return resp.text


class MockProvider:
    #Offline provider so the pipeline can be demoed/tested without an API key.Returns a deliberately invalid answer first (to exercise the repair loop),then a correct one derived from the input text.

    def __init__(self):
        self.calls = 0

    def complete(self, messages: list[dict]) -> str:
        self.calls += 1
        text = messages[-1]["content"] if messages[-1]["role"] == "user" else ""
        original = next(
            m["content"] for m in reversed(messages)
            if m["role"] == "user" and m["content"].startswith("Text:")
        )
        is_invoice = "invoice_number" in messages[0]["content"]
        if is_invoice:
            good = {
                "invoice_number": "INV-2026-042",
                "vendor_name": "Nimbus Cloud Services",
                "customer_name": "Tanvir Ahmed",
                "issue_date": "2026-09-15",
                "due_date": "2026-10-15",
                "currency": "USD",
                "line_items": [
                    {"description": "Cloud hosting (monthly)", "quantity": 1,
                     "unit_price": 200.0, "total": 200.0},
                    {"description": "Support hours", "quantity": 5,
                     "unit_price": 40.0, "total": 200.0},
                ],
                "subtotal": 400.0,
                "tax": 40.0,
                "total": 440.0,
            }
        else:
            good = {
                "full_name": "Nadia Rahman",
                "email": "nadia.rahman@example.com",
                "phone": "+880 1711 000000",
                "location": "Dhaka, Bangladesh",
                "summary": "Data engineer with 5 years of experience.",
                "skills": ["Python", "SQL", "Airflow", "AWS"],
                "experience": [
                    {"company": "DataWorks", "title": "Senior Data Engineer",
                     "start_date": "2023-02", "end_date": None,
                     "highlights": ["Cut pipeline runtime by 40%"]},
                    {"company": "FinTrack", "title": "Data Engineer",
                     "start_date": "2021-06", "end_date": "2023-01",
                     "highlights": ["Built ETL pipelines"]},
                ],
                "education": [
                    {"institution": "University of Dhaka",
                     "degree": "BSc Computer Science", "year": 2021}
                ],
            }
        if self.calls == 1:
            bad = dict(good)
            bad["total"] = 999.0 if is_invoice else None
            if not is_invoice:
                bad["email"] = "not-an-email"
            return json.dumps(bad)
        return json.dumps(good)


def get_provider(name: str, model: str | None = None) -> Provider:
    """Build a provider. A model name is required for every real provider."""
    if name == "mock":
        return MockProvider()
    classes = {"openai": OpenAIProvider, "gemini": GeminiProvider, "groq": GroqProvider}
    if name not in classes:
        raise ValueError(f"Unknown provider: {name}")
    if not model:
        raise ValueError(
            f"No model set for provider '{name}'. "
            "Set LLM_MODEL in .env or pass --model."
        )
    return classes[name](model)
