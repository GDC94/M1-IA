"""Support assistant: one question in, one validated SupportResponse (answer + metrics) out."""

import time

from openai import OpenAI
from pydantic import ValidationError

from chatbot.config import Settings
from chatbot.models import Metrics, SupportAnswer, SupportResponse
from chatbot.pricing import estimate_cost
from chatbot.prompts import build_messages


class NoAnswerError(Exception):
    """The model returned no structured answer (e.g. it refused or the output was cut off)."""


def ask_support(client: OpenAI, settings: Settings, question: str) -> SupportResponse:
    messages = build_messages(question)

    start = time.perf_counter()

    try:
        response = client.responses.parse(
            model=settings.model,
            temperature=settings.support_temperature,
            max_output_tokens=settings.max_output_tokens,
            input=[message.model_dump() for message in messages],
            text_format=SupportAnswer,
        )
    except ValidationError as error:
        # Happens when max_output_tokens cuts the JSON in half.
        raise NoAnswerError(
            "The answer was cut off before the JSON was complete."
        ) from error

    # toma start como tiempo inicial y time.perf_counter() como tiempo final,
    # y calculo la diferencia en milisegundos.
    latency_ms = (time.perf_counter() - start) * 1000

    answer = response.output_parsed
    if answer is None:
        raise NoAnswerError(
            f"No structured answer returned (status: {response.status})."
        )

    usage = response.usage

    metrics = Metrics(
        prompt_tokens=usage.input_tokens,
        completion_tokens=usage.output_tokens,
        total_tokens=usage.total_tokens,
        latency_ms=round(latency_ms, 1),
        estimated_cost_usd=estimate_cost(
            settings.model, usage.input_tokens, usage.output_tokens
        ),
    )

    # model_dump() convierte el SupportAnswer en un dict (answer, confidence, actions).
    return SupportResponse(**answer.model_dump(), metrics=metrics)
    # Esto es equivalente a:
    # return SupportResponse(
    #     answer=answer.answer,
    #     confidence=answer.confidence,
    #     actions=answer.actions,
    #     metrics=metrics,
    # )


#  Ejemplo de SupportAnswer:

#  Ejemplo de respuesta:
#  {
#  "answer": "El pedido #1234 está en camino y llega mañana.",
#  "confidence": 0.86,
#  "actions": ["check_order_status", "share_help_article"],
#  "metrics": {
#    "prompt_tokens": 180,
#    "completion_tokens": 42,
#    "total_tokens": 222,
#    "latency_ms": 1240.3,
#    "estimated_cost_usd": 0.0000522
#  }
#  }
