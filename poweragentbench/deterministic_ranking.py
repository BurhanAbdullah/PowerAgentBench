"""Deterministic ranking helpers for benchmark candidate selection."""
from __future__ import annotations

from typing import Callable, Iterable, List, TypeVar

T = TypeVar("T")


def _canonical_item_key(item: object) -> str:
    """Return a stable, type-aware textual key for a benchmark candidate."""
    return f"{type(item).__name__}:{item!r}"


def deterministic_rank(
    items: Iterable[T],
    score: Callable[[T], float],
    *,
    reverse: bool = True,
    limit: int | None = None,
) -> List[T]:
    """Rank items by score with an explicit deterministic tie-break.

    The secondary key is independent of the input iteration order. This keeps
    benchmark candidate selection reproducible when multiple candidates have
    identical scores.
    """
    scored = [(float(score(item)), _canonical_item_key(item), item) for item in items]
    scored.sort(key=lambda row: (row[0], row[1]), reverse=reverse)

    if reverse:
        # Only the primary score is descending; canonical keys stay ascending.
        ordered: List[T] = []
        i = 0
        while i < len(scored):
            j = i + 1
            score_i = scored[i][0]
            while j < len(scored) and scored[j][0] == score_i:
                j += 1
            ordered.extend(row[2] for row in sorted(scored[i:j], key=lambda row: row[1]))
            i = j
        return ordered[:limit] if limit is not None else ordered

    ordered = [row[2] for row in scored]
    return ordered[:limit] if limit is not None else ordered
