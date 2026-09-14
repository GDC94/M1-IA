"""Tests for explicit support policy decisions."""

from support_assistant.decision import SupportDecision
from support_assistant.models import SupportAnswer


def make_answer(*, confidence: float, actions: list[str]) -> SupportAnswer:
    return SupportAnswer(
        answer="Vamos a revisar tu caso.", confidence=confidence, actions=actions
    )


def test_fraud_threat_requires_human_escalation():
    answer = make_answer(confidence=0.8, actions=["check_payment_history"])

    result = SupportDecision().apply(
        "Si no lo resuelven, denuncio estos cobros por fraude", answer
    )

    assert "escalate_to_human" in result.actions


def test_low_confidence_requires_more_information():
    answer = make_answer(confidence=0.3, actions=[])

    result = SupportDecision().apply("no funciona", answer)

    assert result.actions == ["request_more_information"]


def test_safe_answer_keeps_model_actions():
    answer = make_answer(confidence=0.9, actions=["reset_password"])

    result = SupportDecision().apply("¿Cómo cambio mi contraseña?", answer)

    assert result == answer
