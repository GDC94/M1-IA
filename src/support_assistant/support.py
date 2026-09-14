"""Support assistant: one question in, one validated SupportResponse (answer + metrics) out."""

import time
from pathlib import Path

from support_assistant.config import Settings
from support_assistant.decision import SupportDecision
from support_assistant.llm import (
    GenerationOptions,
    LanguageModel,
    MalformedModelOutput,
)
from support_assistant.models import Metrics, SupportResponse
from support_assistant.metrics_log import log_safety_decision
from support_assistant.pricing import estimate_cost
from support_assistant.prompts import build_messages
from support_assistant.safety import BasicSafetyPolicy, SafetyPolicy


class NoAnswerError(Exception):
    """The model returned no structured answer (e.g. it refused or the output was cut off)."""


def ask_support(
    model: LanguageModel,
    settings: Settings,
    question: str,
    *,
    safety_policy: SafetyPolicy | None = None,
    safety_log_path: Path | None = None,
) -> SupportResponse:
    safety = safety_policy or BasicSafetyPolicy()
    input_safety = safety.check_input(question)
    if not input_safety.allowed:
        if safety_log_path is None:
            log_safety_decision(input_safety)
        else:
            log_safety_decision(input_safety, path=safety_log_path)
        return SupportResponse(
            answer="No puedo ayudar con ese pedido. Puedo ayudarte con una consulta de soporte.",
            confidence=1.0,
            actions=["request_more_information"],
            metrics=Metrics(
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                latency_ms=0,
                estimated_cost_usd=0,
            ),
        )

    messages = build_messages(question)

    start = time.perf_counter()

    try:
        response = model.generate(
            messages,
            GenerationOptions(
                model=settings.model,
                temperature=settings.temperature,
                max_output_tokens=settings.max_output_tokens,
            ),
        )
    except MalformedModelOutput as error:
        raise NoAnswerError(
            "The answer was cut off before the JSON was complete."
        ) from error

    # toma start como tiempo inicial y time.perf_counter() como tiempo final,
    # y calculo la diferencia en milisegundos.
    latency_ms = (time.perf_counter() - start) * 1000

    answer = response.answer
    if answer is None:
        raise NoAnswerError(
            f"No structured answer returned (status: {response.status})."
        )

    output_safety = safety.check_output(answer)
    if not output_safety.allowed:
        if safety_log_path is None:
            log_safety_decision(output_safety)
        else:
            log_safety_decision(output_safety, path=safety_log_path)
        answer = answer.model_copy(
            update={
                "answer": "No puedo confirmar esa información. Vamos a derivar tu caso a soporte humano.",
                "confidence": 1.0,
                "actions": ["escalate_to_human"],
            }
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
    answer = SupportDecision().apply(question, answer)
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
