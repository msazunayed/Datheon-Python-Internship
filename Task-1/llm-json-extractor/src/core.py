#Structured LLM prompt pipeline & JSON extractor.

from __future__ import annotations

import json
import re
import sys

from pydantic import BaseModel, ValidationError

from .prompts import build_messages, build_repair_message
from .providers import get_provider
from .schemas import SCHEMAS


class ExtractionError(RuntimeError):
    pass


def _parse_json(raw: str) -> dict:
    """Parse JSON, tolerating markdown fences or stray text around the object."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def extract(text: str, doc_type: str, provider, max_retries: int = 2) -> BaseModel:
    #Run the prompt, validate with Pydantic, and self-repair on failure.
    model_cls = SCHEMAS[doc_type]
    messages = build_messages(doc_type, model_cls, text)
    last_error = ""
    for attempt in range(max_retries + 1):
        raw = provider.complete(messages)
        try:
            return model_cls.model_validate(_parse_json(raw))
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = str(exc)
            print(f"[attempt {attempt + 1}] validation failed, retrying...",
                  file=sys.stderr)
            messages.append({"role": "assistant", "content": raw})
            messages.append(build_repair_message(last_error))
    raise ExtractionError(f"Failed after {max_retries + 1} attempts:\n{last_error}")
