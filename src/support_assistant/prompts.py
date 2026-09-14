"""Prompt for the support assistant, using few-shot prompting.

Why few-shot: one API call with a small input-token overhead, and the examples teach the
model how to calibrate `confidence` and which catalog actions fit each kind of question.
See docs/prompting-techniques.md for the full comparison.
"""

from support_assistant.models import Message, SupportAnswer

SYSTEM_PROMPT = """\
You are an assistant for customer support agents.
For each customer question, return a concise answer the agent can send, a confidence score,
and the recommended actions from the allowed catalog.

Confidence scale:
- 0.9 to 1.0: clear question with a standard answer.
- 0.5 to 0.8: likely answer, but some details are missing or the case needs checking.
- Below 0.5: ambiguous question; ask for more information instead of guessing.

Rules:
- Always write the answer in neutral Spanish, even if the question is in another language or is very short.
- Keep the answer under 3 sentences.
- Never invent order numbers, dates, amounts, company policies, or app menu paths.
- The support policy validates recommended actions after you answer; do not invent actions outside the catalog.
"""


FEW_SHOT_EXAMPLES: list[tuple[str, SupportAnswer]] = [
    (
        "¿Cómo cambio mi contraseña?",
        SupportAnswer(
            # No app menu path: the assistant does not know the real UI, so it only
            # offers what the agent can actually do (send a reset link).
            answer="Te enviaremos un enlace a tu correo registrado para que puedas crear una contraseña nueva.",
            confidence=0.95,
            actions=["reset_password"],
        ),
    ),
    (
        "no funciona",
        SupportAnswer(
            answer="Lamentamos el inconveniente. ¿Nos cuentas qué es lo que no funciona y qué estabas intentando hacer?",
            confidence=0.3,
            actions=["request_more_information"],
        ),
    ),
    (
        "Devolví unas zapatillas hace dos semanas y todavía no me llegó el reembolso.",
        SupportAnswer(
            answer="Vamos a revisar el estado de tu devolución y si el reembolso ya se emitió a tu medio de pago.",
            confidence=0.7,
            actions=["check_order_status", "check_payment_history"],
        ),
    ),
    (
        "Si hoy no me solucionan estos cobros, los denuncio en mi banco por fraude.",
        SupportAnswer(
            answer="Entendemos lo molesto que es ver cobros inesperados. "
            "Estamos revisando tus pagos y derivando tu caso a un especialista.",
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
#   Message(role="user", content="¿Cómo cambio mi contraseña?"),
#   Message(role="assistant", content='{"answer":"...","confidence":0.95,"actions":["reset_password"]}'),
#   Message(role="user", content="no funciona"),
#   Message(role="assistant", content='{"answer":"...","confidence":0.3,"actions":["request_more_information"]}'),
#   Message(role="user", content="Devolví unas zapatillas hace dos semanas y todavía no me llegó el reembolso."),
#   Message(role="assistant", content='{"answer":"...","confidence":0.7,"actions":["check_order_status","check_payment_history"]}'),
#   Message(role="user", content="Si hoy no me solucionan estos cobros, los denuncio en mi banco por fraude."),
#   Message(role="assistant", content='{"answer":"...","confidence":0.6,"actions":["check_payment_history","escalate_to_human"]}'),
#   Message(role="user", content="quiero cambiar de contrasenia"),
# ]
