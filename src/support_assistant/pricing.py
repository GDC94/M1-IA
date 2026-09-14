"""Token prices and cost estimation. Pure functions: no API calls."""

from pydantic import BaseModel

TOKENS_PER_PRICE_UNIT = 1_000_000
COST_DECIMALS = 8


class ModelPrice(BaseModel):
    input_per_million: float
    output_per_million: float


# Precios del nivel estándar en USD por 1M de tokens.
# Fuente openai.com/api/docs/pricing al 13/09.
PRICES: dict[str, ModelPrice] = {
    "gpt-4o-mini": ModelPrice(input_per_million=0.15, output_per_million=0.60),
    "gpt-4o": ModelPrice(input_per_million=2.50, output_per_million=10.00),
    "gpt-4.1-mini": ModelPrice(input_per_million=0.40, output_per_million=1.60),
    "gpt-4.1-nano": ModelPrice(input_per_million=0.10, output_per_million=0.40),
}

# Con estimate_cost calculo el costo estimado en dólares de una llamada a un modelo, 
# segun cuántos tokens de entrada y de salida se usaron.

def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return the estimated cost in USD. Raises ValueError for models without a known price."""
    price = PRICES.get(model)
    if price is None:
        raise ValueError(f"No price configured for model '{model}'. Add it to PRICES in pricing.py.")

    input_cost = input_tokens * price.input_per_million / TOKENS_PER_PRICE_UNIT
    output_cost = output_tokens * price.output_per_million / TOKENS_PER_PRICE_UNIT

    return round(input_cost + output_cost, COST_DECIMALS)
