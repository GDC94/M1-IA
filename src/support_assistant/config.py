"""Application settings loaded from environment variables and validated with Pydantic."""

"""os es un módulo de la librería estándar de Python: viene incluido y no hace falta instalarlo. Su nombre viene de operating system
  (sistema operativo). Te deja hablar con el sistema operativo desde Python."""
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr

DEFAULT_MODEL = "gpt-4o-mini"
# Support answers must be consistent: the same question should get the same answer.
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_OUTPUT_TOKENS = 500


class Settings(BaseModel):
    api_key: SecretStr
    model: str = Field(default=DEFAULT_MODEL, min_length=1)
    temperature: float = Field(default=DEFAULT_TEMPERATURE, ge=0.0, le=2.0)

    # Max length of each reply. Used in support.py: responses.parse(max_output_tokens=...)
    max_output_tokens: int = Field(default=DEFAULT_MAX_OUTPUT_TOKENS, gt=0)

    # Optional settings. To enable one, uncomment it here AND its line in load_settings(),
    # then use it where indicated.

    # Seconds to wait for a response (SDK default: 600). Used in client.py: OpenAI(timeout=...)
    # timeout: float = Field(default=30.0, gt=0)

    # Automatic retries on 429/5xx/connection errors (SDK default: 2). Used in client.py: OpenAI(max_retries=...)
    max_retries: int = Field(default=2, ge=0)


def load_settings() -> Settings:
    """Cargamos las variables de entorno."""
    load_dotenv()
    return Settings(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL") or DEFAULT_MODEL,
        temperature=os.getenv("OPENAI_TEMPERATURE") or DEFAULT_TEMPERATURE,
        max_output_tokens=os.getenv("OPENAI_MAX_OUTPUT_TOKENS") or DEFAULT_MAX_OUTPUT_TOKENS,
        # timeout=os.getenv("OPENAI_TIMEOUT") or 30.0,
        max_retries=os.getenv("OPENAI_MAX_RETRIES") or 2,
    )
