from dataclasses import dataclass


@dataclass
class Response:
    text: str
    latency_ms: float
    cost: float
    model_id: str
    provider: str
    input_tokens: int
    output_tokens: int
