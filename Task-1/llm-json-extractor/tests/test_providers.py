import pytest

from src.providers import GroqProvider, get_provider


def test_groq_registered(monkeypatch):
    pytest.importorskip("openai")
    monkeypatch.setenv("GROQ_API_KEY", "test")
    p = get_provider("groq", "openai/gpt-oss-120b")
    assert isinstance(p, GroqProvider)
    assert "groq.com" in str(p.client.base_url)


def test_unknown_provider():
    with pytest.raises(ValueError):
        get_provider("nope")


def test_cli_reads_provider_from_env(monkeypatch, tmp_path, capsys):
    from src.cli import main

    from src import cli

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "RESULTS_DIR", tmp_path / "results")
    (tmp_path / ".env").write_text("LLM_PROVIDER=mock\n")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setattr("sys.argv", ["main.py", str(_sample(tmp_path)), "--type", "invoice"])
    assert main() == 0
    assert "INV-2026-042" in capsys.readouterr().out


def _sample(tmp_path):
    f = tmp_path / "in.txt"
    f.write_text("anything")
    return f


def test_model_required_for_real_providers():
    with pytest.raises(ValueError, match="No model set"):
        get_provider("groq")
    with pytest.raises(ValueError, match="No model set"):
        get_provider("openai", "")


def test_mock_needs_no_model():
    assert get_provider("mock") is not None


def test_result_saved_to_results_folder(monkeypatch, tmp_path):
    from src import cli

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(
        "sys.argv", ["main.py", str(_sample(tmp_path)), "--type", "invoice", "--provider", "mock"]
    )
    assert cli.main() == 0
    saved = tmp_path / "results" / "in.json"
    assert saved.exists() and "INV-2026-042" in saved.read_text()
