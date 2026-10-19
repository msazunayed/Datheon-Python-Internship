#Command-line interface: python main.py <file> --type invoice|resume

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from .core import ExtractionError, extract
from .providers import get_provider
from .schemas import SCHEMAS

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"  # <project root>/results


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract validated JSON from unstructured text with an LLM.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path, help="Path to unstructured text file")
    ap.add_argument("--type", choices=list(SCHEMAS), required=True)
    ap.add_argument("--provider", choices=["gemini", "openai", "groq", "mock"],
                    help="LLM provider (default: LLM_PROVIDER from .env, else gemini)")
    ap.add_argument("--model", help="Model name (default: LLM_MODEL from .env; required for real providers)")
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--output", type=Path, help="Save JSON to this path instead of results/<input-name>.json")
    args = ap.parse_args()
    load_dotenv(find_dotenv(usecwd=True))  # .env from the directory you run in
    provider_name = args.provider or os.environ.get("LLM_PROVIDER", "gemini").lower()
    model_name = args.model or os.environ.get("LLM_MODEL") or None

    text = args.input.read_text(encoding="utf-8")
    try:
        provider = get_provider(provider_name, model_name)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    try:
        result = extract(text, args.type, provider, args.retries)
    except ExtractionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    out = result.model_dump_json(indent=2)
    out_path = args.output or RESULTS_DIR / f"{args.input.stem}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding="utf-8")
    print(out)
    print(f"Saved validated JSON to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
