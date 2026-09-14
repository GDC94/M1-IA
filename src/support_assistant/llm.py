"""Provider-neutral language-model seam and the OpenAI adapter."""

from dataclasses import dataclass
from typing import Protocol

from openai import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)
from pydantic import ValidationError

from support_assistant.models import Message, SupportAnswer


@dataclass(frozen=True)
class GenerationOptions:
    model: str
    temperature: float
    max_output_tokens: int


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class ModelResult:
    answer: SupportAnswer | None
    usage: TokenUsage
    status: str


class LanguageModel(Protocol):
    def generate(
        self, messages: list[Message], options: GenerationOptions
    ) -> ModelResult: ...


# Para sumar otro proveedor en el futuro:
#
# class AnthropicAdapter:
#     """Traduce el SDK de Anthropic al seam LanguageModel."""
#
#     def generate(
#         self, messages: list[Message], options: GenerationOptions
#     ) -> ModelResult:
#         # 1. Convertir Message y GenerationOptions al formato del proveedor.
#         # 2. Ejecutar la llamada al SDK.
#         # 3. Convertir respuesta, usage y status a ModelResult.
#         # 4. Traducir errores del proveedor a las excepciones de este módulo.
#         ...
#
# Después, cambiar client.py para construir AnthropicAdapter.
# support.py y sus tests de dominio no deberían cambiar.


class MalformedModelOutput(Exception):
    """The provider returned structured output that could not be parsed."""


class ModelAuthenticationError(Exception):
    """The provider rejected authentication."""


class ModelRateLimitError(Exception):
    """The provider rate limit was reached."""


class ModelConnectionError(Exception):
    """The provider could not be reached."""


class ModelProviderError(Exception):
    """The provider returned an unexpected API error."""


class OpenAIAdapter:
    """Translate the OpenAI SDK into the small LanguageModel seam."""

    def __init__(self, client: OpenAI):
        self._client = client

    def generate(
        self, messages: list[Message], options: GenerationOptions
    ) -> ModelResult:
        try:
            response = self._client.responses.parse(
                model=options.model,
                temperature=options.temperature,
                max_output_tokens=options.max_output_tokens,
                input=[message.model_dump() for message in messages],
                text_format=SupportAnswer,
            )
        except AuthenticationError as error:
            raise ModelAuthenticationError from error
        except RateLimitError as error:
            raise ModelRateLimitError from error
        except APIConnectionError as error:
            raise ModelConnectionError from error
        except APIError as error:
            raise ModelProviderError(str(error)) from error
        except ValidationError as error:
            raise MalformedModelOutput from error

        usage = response.usage
        return ModelResult(
            answer=response.output_parsed,
            usage=TokenUsage(
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                total_tokens=usage.total_tokens,
            ),
            status=response.status,
        )
