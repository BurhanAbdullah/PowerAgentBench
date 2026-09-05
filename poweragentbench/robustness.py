"""Reusable robustness metrics for repeated PowerAgentBench evaluations."""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import mean
from typing import Iterable, Sequence


@dataclass(frozen=True)
class RobustnessSummary:
    """Distribution-free summary of repeated agent outcomes."""

    n: int
    mean: float
    std: float
    min: float
    max: float
    p05: float
    p50: float
    p95: float
    success_rate: float | None = None


def _finite(values: Iterable[float]) -> list[float]:
    result: list[float] = []
    for raw in values:
        value = float(raw)
        if value != value or value in (float("inf"), float("-inf")):
            continue
        result.append(value)
    return result


def _quantile(values: Sequence[float], q: float) -> float:
    if not values:
        raise ValueError("at least one finite value is required")
    if not 0.0 <= q <= 1.0:
        raise ValueError("q must lie between 0 and 1")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = q * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] + weight * (ordered[upper] - ordered[lower])


def summarize(values: Iterable[float], success_threshold: float | None = None) -> RobustnessSummary:
    """Summarize repeated benchmark outcomes.

    ``success_threshold`` is optional and is interpreted as a lower-is-better
    agnostic threshold: the success rate is the fraction of observations at or
    above it. Callers evaluating a lower-is-better metric can transform values
    before calling this function.
    """
    data = _finite(values)
    if not data:
        raise ValueError("at least one finite outcome is required")

    avg = mean(data)
    variance = sum((value - avg) ** 2 for value in data) / len(data)
    success_rate = None
    if success_threshold is not None:
        success_rate = sum(value >= success_threshold for value in data) / len(data)

    return RobustnessSummary(
        n=len(data),
        mean=avg,
        std=sqrt(variance),
        min=min(data),
        max=max(data),
        p05=_quantile(data, 0.05),
        p50=_quantile(data, 0.50),
        p95=_quantile(data, 0.95),
        success_rate=success_rate,
    )


def bootstrap_mean_interval(
    values: Iterable[float],
    confidence: float = 0.95,
    resamples: int = 2000,
    seed: int = 0,
) -> tuple[float, float]:
    """Return a deterministic percentile-bootstrap interval for the mean."""
    data = _finite(values)
    if not data:
        raise ValueError("at least one finite outcome is required")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must lie strictly between 0 and 1")
    if resamples < 1:
        raise ValueError("resamples must be positive")

    import random

    rng = random.Random(seed)
    boot_means = [mean(rng.choices(data, k=len(data))) for _ in range(resamples)]
    alpha = (1.0 - confidence) / 2.0
    return _quantile(boot_means, alpha), _quantile(boot_means, 1.0 - alpha)


def coefficient_of_variation(values: Iterable[float], floor: float = 1e-12) -> float:
    """Return standard deviation divided by absolute mean."""
    summary = summarize(values)
    if abs(summary.mean) <= floor:
        raise ValueError("coefficient of variation is undefined near zero mean")
    return summary.std / abs(summary.mean)
