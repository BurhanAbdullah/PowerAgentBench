"""Deterministic ranking helpers for benchmark candidate selection."""
from __future__ import annotations

from typing import Callable, Iterable, List, Sequence, Tuple, TypeVar

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
    benchmark candidate selection and reported rankings reproducible when two
    candidates receive identical scores.
    """
    ranked = sorted(
        items,
        key=lambda item: (float(score(item)), _canonical_item_key(item)),
        reverse=reverse,
    )
    if reverse:
        # ``reverse=True`` also reverses the textual tie-break, so reorder each
        # equal-score group into ascending canonical-key order.
        out: List[T] = []
        i = 0
        while i < len(ranked):
            j = i + 1
            score_i = float(score(ranked[i]))
            while j < len(ranked) and float(score(ranked[j])) == score_i:
                j += 1
            out.extend(sorted(ranked[i:j], key=_canonical_item_key))
            i = j
        ranked = out
    return ranked[:limit] if limit is not None else ranked
