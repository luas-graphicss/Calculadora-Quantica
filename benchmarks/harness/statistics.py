import math
from collections.abc import Sequence
from typing import TypedDict


class Summary(TypedDict):
    count: int
    minimum: float
    p50: float
    p95: float
    maximum: float
    mean: float


def percentile(values: Sequence[float], percent: float) -> float:
    ordered = sorted(values)
    rank = max(1, math.ceil(percent / 100 * len(ordered)))
    return ordered[rank - 1]


def summarize(values: Sequence[float]) -> Summary:
    return Summary(
        count=len(values),
        minimum=min(values),
        p50=percentile(values, 50),
        p95=percentile(values, 95),
        maximum=max(values),
        mean=math.fsum(values) / len(values),
    )
