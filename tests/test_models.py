"""Tests for the pydantic contract in support_assistant.models."""

import json

import pytest
from pydantic import ValidationError

from support_assistant.models import Metrics, SupportResponse


def _valid_metrics_kwargs() -> dict:
    return {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
        "latency_ms": 123.4,
        "estimated_cost_usd": 0.0001,
    }


def _valid_response_kwargs() -> dict:
    return {
        "answer": "Tu pedido llega mañana.",
        "confidence": 0.8,
        "actions": ["check_order_status"],
        "metrics": _valid_metrics_kwargs(),
    }


def test_valid_support_response_is_accepted():
    response = SupportResponse(**_valid_response_kwargs())

    assert response.answer == "Tu pedido llega mañana."
    assert response.confidence == 0.8
    assert response.actions == ["check_order_status"]
    assert response.metrics.total_tokens == 15


def test_valid_support_response_serializes_expected_keys():
    response = SupportResponse(**_valid_response_kwargs())

    payload = json.loads(response.model_dump_json())

    assert set(["answer", "confidence", "actions", "metrics"]).issubset(payload.keys())
    assert set(
        [
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "latency_ms",
            "estimated_cost_usd",
        ]
    ).issubset(payload["metrics"].keys())


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"confidence": 1.1}, id="confidence-above-one"),
        pytest.param({"confidence": -0.1}, id="confidence-below-zero"),
        pytest.param({"actions": ["not_a_real_action"]}, id="action-not-in-catalog"),
        pytest.param({"answer": ""}, id="empty-answer"),
    ],
)
def test_support_response_rejects_invalid_field(overrides: dict):
    kwargs = _valid_response_kwargs() | overrides

    with pytest.raises(ValidationError):
        SupportResponse(**kwargs)


def test_support_response_requires_metrics():
    kwargs = _valid_response_kwargs()
    del kwargs["metrics"]

    with pytest.raises(ValidationError):
        SupportResponse(**kwargs)


@pytest.mark.parametrize(
    "field",
    ["prompt_tokens", "completion_tokens", "total_tokens"],
)
def test_metrics_rejects_negative_token_count(field: str):
    kwargs = _valid_metrics_kwargs() | {field: -1}

    with pytest.raises(ValidationError):
        Metrics(**kwargs)
