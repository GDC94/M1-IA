"""Prompt for the support assistant, using few-shot prompting.

Why few-shot: one API call with a small input-token overhead, and the examples teach the
model how to calibrate `confidence` and which catalog actions fit each kind of question.
See docs/prompting-techniques.md for the full comparison.
"""

from chatbot.models import Message, SupportAnswer

SYSTEM_PROMPT = """\
You are an assistant for customer support agents.
For each customer question, return a concise answer the agent can send, a confidence score,
and the recommended actions from the allowed catalog.

Confidence scale:
- 0.9 to 1.0: clear question with a standard answer.
- 0.5 to 0.8: likely answer, but some details are missing or the case needs checking.
- Below 0.5: ambiguous question; ask for more information instead of guessing.

Rules:
- Keep the answer under 3 sentences.
- Never invent order numbers, dates, amounts, or company policies.
- Recommend escalate_to_human only for angry customers, legal or fraud threats, or cases an agent cannot solve alone.
"""


FEW_SHOT_EXAMPLES: list[tuple[str, SupportAnswer]] = [
    (
        "How do I change my password?",
        SupportAnswer(
            answer="Go to Settings > Security > Change password and follow the steps. "
            "If you can't log in, use 'Forgot password' on the login page.",
            confidence=0.95,
            actions=["reset_password", "share_help_article"],
        ),
    ),
    (
        "It's not working",
        SupportAnswer(
            answer="Sorry about that. Could you tell me what is not working and what you were trying to do?",
            confidence=0.3,
            actions=["request_more_information"],
        ),
    ),
    (
        "I returned my shoes two weeks ago and still haven't received the refund.",
        SupportAnswer(
            answer="Refunds are issued once the return is received and processed. "
            "Let me check the return status and the refund on your payment method.",
            confidence=0.7,
            actions=["check_order_status", "check_payment_history"],
        ),
    ),
    (
        "If you don't fix these charges today I'm reporting you to my bank for fraud.",
        SupportAnswer(
            answer="I understand how frustrating unexpected charges are. "
            "I'm reviewing your payments now and passing your case to a specialist.",
            confidence=0.6,
            actions=["check_payment_history", "escalate_to_human"],
        ),
    ),
]


def build_messages(question: str) -> list[Message]:
    """System prompt, then each example as a user/assistant turn, then the real question."""
    messages = [Message(role="system", content=SYSTEM_PROMPT)]
    for example_question, example_answer in FEW_SHOT_EXAMPLES:
        messages.append(Message(role="user", content=example_question))
        messages.append(Message(role="assistant", content=example_answer.model_dump_json()))
    messages.append(Message(role="user", content=question))
    return messages


# Ejemplo: build_messages("quiero cambiar de contrasenia")
# [
#   Message(role="system", content=SYSTEM_PROMPT),
#   Message(role="user", content="How do I change my password?"),
#   Message(role="assistant", content='{"answer":"...","confidence":0.95,"actions":["reset_password","share_help_article"]}'),
#   Message(role="user", content="It's not working"),
#   Message(role="assistant", content='{"answer":"...","confidence":0.3,"actions":["request_more_information"]}'),
#   Message(role="user", content="I returned my shoes two weeks ago and still haven't received the refund."),
#   Message(role="assistant", content='{"answer":"...","confidence":0.7,"actions":["check_order_status","check_payment_history"]}'),
#   Message(role="user", content="If you don't fix these charges today I'm reporting you to my bank for fraud."),
#   Message(role="assistant", content='{"answer":"...","confidence":0.6,"actions":["check_payment_history","escalate_to_human"]}'),
#   Message(role="user", content="quiero cambiar de contrasenia"),
# ]
