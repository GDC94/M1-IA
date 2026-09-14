"""Explicit support policy applied after model interpretation."""

import unicodedata

from support_assistant.models import Action, SupportAnswer

ESCALATION_TERMS = (
    "fraude",
    "estafa",
    "denuncia",
    "denuncio",
    "abogado",
    "demanda",
    "legal",
)


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


class SupportDecision:
    """Enforce support safety and fallback rules outside the prompt."""

    def apply(self, question: str, answer: SupportAnswer) -> SupportAnswer:
        actions: list[Action] = list(answer.actions)
        normalized_question = _normalize(question)

        if any(term in normalized_question for term in ESCALATION_TERMS):
            self._add_action(actions, "escalate_to_human")

        if answer.confidence < 0.5:
            self._add_action(actions, "request_more_information")

        return answer.model_copy(update={"actions": actions})

    @staticmethod
    def _add_action(actions: list[Action], action: Action) -> None:
        if action not in actions:
            actions.append(action)
