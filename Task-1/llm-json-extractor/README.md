# LLM JSON Extractor

Extract validated JSON from unstructured invoices and resumes using Groq, OpenAI or Gemini.

## Project structure
    llm-json-extractor/
    ├── main.py                # entry point
    ├── src/
    │   ├── __init__.py
    │   ├── __main__.py        # lets you run: python -m src
    │   ├── cli.py             # argument parsing, reads .env
    │   ├── core.py            # extract() with validate-and-repair loop
    │   ├── schemas.py         # Pydantic contracts (Invoice, Resume)
    │   ├── prompts.py         # templates, few-shot examples, repair message
    │   └── providers.py       # Groq / OpenAI / Gemini / Mock adapters
    ├── samples/
    │   ├── invoice_1.txt      # example input documents
    │   └── resume_1.txt
    ├── results/               # created on first run: one JSON per input
    ├── tests/                 # pytest suite (offline)
    │   ├── test_extractor.py
    │   ├── test_providers.py
    │   └── test_schemas.py
    ├── .env.example           # copy to .env (your real .env is git-ignored)
    ├── .gitignore
    ├── pytest.ini
    ├── requirements.txt
    └── requirements-dev.txt

## Setup
    uv pip install -r requirements.txt     # or: pip install -r requirements.txt
    cp .env.example .env                   # set LLM_PROVIDER, LLM_MODEL and your API key

## Run (from the project root)
    python main.py samples/invoice_1.txt --type invoice
    python main.py samples/resume_1.txt  --type resume
    python main.py samples/invoice_1.txt --type invoice --provider mock   # no key needed

Each run prints the JSON and also saves it to `results/<input-name>.json` (e.g. `results/invoice_1.json`); the folder is created automatically. Use `--output path.json` to save somewhere else. `--provider` / `--model` override `.env`. There is no built-in default model, so set `LLM_MODEL`.

## Test
    uv pip install -r requirements-dev.txt
    pytest
