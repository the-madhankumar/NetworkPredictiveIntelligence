from dataclasses import dataclass


@dataclass
class Pricing:
    input_per_mtok: float
    output_per_mtok: float
    cache_write_per_mtok: float
    cache_read_per_mtok: float


SONNET_5 = Pricing(
    input_per_mtok=2.00,
    output_per_mtok=10.00,
    cache_write_per_mtok=2.50,
    cache_read_per_mtok=0.20,
)


def token_cost(tokens: int, price_per_mtok: float) -> float:
    return (tokens / 1_000_000) * price_per_mtok


def calculate_request_cost(
    input_tokens: int,
    output_tokens: int,
    cache_write_tokens: int = 0,
    cache_read_tokens: int = 0,
    pricing: Pricing = SONNET_5,
) -> float:

    input_cost = token_cost(
        input_tokens,
        pricing.input_per_mtok,
    )

    output_cost = token_cost(
        output_tokens,
        pricing.output_per_mtok,
    )

    cache_write_cost = token_cost(
        cache_write_tokens,
        pricing.cache_write_per_mtok,
    )

    cache_read_cost = token_cost(
        cache_read_tokens,
        pricing.cache_read_per_mtok,
    )

    return (
        input_cost
        + output_cost
        + cache_write_cost
        + cache_read_cost
    )


def calculate_1000_requests(
    input_tokens: int,
    output_tokens: int,
    cache_write_tokens: int = 0,
    cache_read_tokens: int = 0,
) -> dict[str, float]:

    cost_per_request = calculate_request_cost(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_write_tokens=cache_write_tokens,
        cache_read_tokens=cache_read_tokens,
    )

    cost_per_1000 = cost_per_request * 1000

    return {
        "cost_per_request_usd": round(cost_per_request, 8),
        "cost_per_1000_requests_usd": round(cost_per_1000, 4),
    }