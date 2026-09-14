"""Tests for support_assistant.cli.main: argument parsing, success path, and error mapping."""

import json
from pathlib import Path

import pytest

from support_assistant import cli
from support_assistant.models import Metrics, SupportResponse
from support_assistant.support import NoAnswerError


def _sample_support_response() -> SupportResponse:
    return SupportResponse(
        answer="Te enviaremos un enlace para restablecer tu contraseña.",
        confidence=0.9,
        actions=["reset_password"],
        metrics=Metrics(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            latency_ms=12.3,
            estimated_cost_usd=0.0001,
        ),
    )


def test_whitespace_only_question_exits_with_error(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["   "])

    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert captured.out == ""

    error_payload = json.loads(captured.err)
    assert error_payload["error"] == "invalid_input"


def test_successful_run_prints_contract_json_and_logs_metrics(
    monkeypatch, tmp_path: Path, capsys
):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.chdir(tmp_path)

    response = _sample_support_response()
    monkeypatch.setattr(cli, "create_client", lambda settings: object())
    monkeypatch.setattr(cli, "ask_support", lambda client, settings, question: response)

    cli.main(["¿Cómo cambio mi contraseña?"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["answer"] == response.answer
    assert payload["confidence"] == response.confidence
    assert payload["actions"] == response.actions
    assert payload["metrics"]["total_tokens"] == 15

    log_path = tmp_path / "logs" / "metrics.jsonl"
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1


def test_no_answer_error_is_mapped_to_no_answer_exit(monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    monkeypatch.setattr(cli, "create_client", lambda settings: object())

    def _raise_no_answer(client, settings, question):
        raise NoAnswerError("boom")

    monkeypatch.setattr(cli, "ask_support", _raise_no_answer)

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["hola"])

    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    error_payload = json.loads(captured.err)
    assert error_payload["error"] == "no_answer"
