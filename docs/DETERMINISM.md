# Deterministic ranking

Benchmark candidate selection can contain ties: multiple contingencies may receive the same screening score. Python's stable sort preserves input order for equal keys, so a caller that supplies the same candidates in a different order can otherwise produce a different selected set when a budget truncates a ranking.

`poweragentbench.deterministic_ranking.deterministic_rank` makes the tie policy explicit:

- primary key: numeric benchmark score;
- secondary key: a type-aware representation of the candidate;
- when ranking descending, only the score is reversed; equal-score candidates remain in ascending canonical-key order.

This is intended for benchmark selection, not as a replacement for domain-specific scoring. It is especially useful when a finite validation budget means only the first `N` candidates are evaluated.
