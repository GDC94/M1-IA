"""Tests for support_assistant.prompts: message structure and few-shot examples."""

from support_assistant.models import SupportAnswer
from support_assistant.prompts import FEW_SHOT_EXAMPLES, SYSTEM_PROMPT, build_messages


def test_first_message_is_system_prompt():
    messages = build_messages("hola")

    assert messages[0].role == "system"
    assert messages[0].content == SYSTEM_PROMPT


def test_last_message_is_the_user_question():
    question = "¿Cuándo llega mi pedido?"

    messages = build_messages(question)

    assert messages[-1].role == "user"
    assert messages[-1].content == question


def test_examples_alternate_user_and_assistant_between_system_and_question():
    messages = build_messages("hola")

    example_messages = messages[1:-1]
    assert len(example_messages) == len(FEW_SHOT_EXAMPLES) * 2

    for index, message in enumerate(example_messages):
        expected_role = "user" if index % 2 == 0 else "assistant"
        assert message.role == expected_role


def test_every_assistant_example_content_parses_back_as_support_answer():
    messages = build_messages("hola")

    assistant_messages = [
        message for message in messages if message.role == "assistant"
    ]
    assert len(assistant_messages) == len(FEW_SHOT_EXAMPLES)

    for message in assistant_messages:
        SupportAnswer.model_validate_json(message.content)


def test_system_prompt_mentions_spanish():
    assert "Spanish" in SYSTEM_PROMPT


def test_examples_cover_a_low_confidence_case():
    assert any(answer.confidence < 0.5 for _, answer in FEW_SHOT_EXAMPLES)


def test_examples_cover_an_escalate_to_human_case():
    assert any("escalate_to_human" in answer.actions for _, answer in FEW_SHOT_EXAMPLES)
