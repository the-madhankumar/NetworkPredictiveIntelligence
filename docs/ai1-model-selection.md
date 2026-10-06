# AI1 Model Selection

## Selected Model

Claude Sonnet 5

## Reason

The Customer Retention Intelligence System requires reasoning over customer behaviour, churn indicators, conflicting evidence, and retention recommendations.

Claude Sonnet 5 provides a strong balance between reasoning capability, latency, context capacity, and cost. It is therefore selected as the default model for the retention assistant.

## Model Comparison

| Model            | Input / MTok | Output / MTok | Context | Suitable Job                                   |
| ---------------- | -----------: | ------------: | ------: | ---------------------------------------------- |
| Claude Haiku 4.5 |           $1 |            $5 |    200K | High-volume/simple retention questions         |
| Claude Sonnet 5  |           $2 |           $10 |      1M | Main retention assistant                       |
| Claude Opus 5    |           $5 |           $25 |      1M | Complex investigations and difficult reasoning |

Pricing and model specifications should be rechecked against the current Anthropic documentation before production deployment.

## Decision

Use Claude Sonnet 5 as the default model.

Use a lower-cost model for simple, high-volume tasks when evaluation shows that quality remains acceptable.

Use a stronger model only when evaluation demonstrates that the additional reasoning capability materially improves difficult retention investigations.
