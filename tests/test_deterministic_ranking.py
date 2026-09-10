import unittest

from poweragentbench.deterministic_ranking import deterministic_rank


class TestDeterministicRank(unittest.TestCase):
    def test_equal_scores_do_not_depend_on_input_order(self):
        items = [(2, 3), (0, 4), (1, 5), (0, 2)]
        score = lambda item: 1.0

        self.assertEqual(
            deterministic_rank(items, score),
            deterministic_rank(reversed(items), score),
        )

    def test_primary_score_remains_descending(self):
        items = ["low", "high", "middle"]
        scores = {"low": 0.1, "high": 0.9, "middle": 0.5}

        self.assertEqual(
            deterministic_rank(items, scores.__getitem__),
            ["high", "middle", "low"],
        )

    def test_tie_break_is_ascending_canonical_key(self):
        items = [(10, 11), (2, 20), (1, 9)]
        score = lambda item: 3.0

        result = deterministic_rank(items, score)
        self.assertEqual(result, [(1, 9), (10, 11), (2, 20)])

    def test_limit_is_applied_after_deterministic_ordering(self):
        items = [(3, 4), (1, 2), (5, 6), (0, 1)]
        score = lambda item: 2.0

        self.assertEqual(
            deterministic_rank(items, score, limit=2),
            [(0, 1), (1, 2)],
        )


if __name__ == "__main__":
    unittest.main()
