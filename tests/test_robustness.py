import unittest

from poweragentbench.robustness import (
    bootstrap_mean_interval,
    coefficient_of_variation,
    summarize,
)


class TestRobustnessMetrics(unittest.TestCase):
    def test_summary_and_quantiles(self):
        result = summarize([1, 2, 3, 4, 5])
        self.assertEqual(result.n, 5)
        self.assertAlmostEqual(result.mean, 3.0)
        self.assertAlmostEqual(result.p05, 1.2)
        self.assertAlmostEqual(result.p50, 3.0)
        self.assertAlmostEqual(result.p95, 4.8)
        self.assertEqual(result.min, 1.0)
        self.assertEqual(result.max, 5.0)

    def test_nonfinite_values_are_excluded(self):
        result = summarize([1.0, float("nan"), 3.0, float("inf")])
        self.assertEqual(result.n, 2)
        self.assertAlmostEqual(result.mean, 2.0)

    def test_success_rate(self):
        result = summarize([0.1, 0.7, 0.9, 0.2], success_threshold=0.5)
        self.assertAlmostEqual(result.success_rate, 0.5)

    def test_bootstrap_is_deterministic(self):
        values = [0.2, 0.4, 0.6, 0.8]
        self.assertEqual(
            bootstrap_mean_interval(values, resamples=200, seed=17),
            bootstrap_mean_interval(values, resamples=200, seed=17),
        )

    def test_bootstrap_interval_contains_sample_mean(self):
        values = [0.2, 0.4, 0.6, 0.8]
        lower, upper = bootstrap_mean_interval(values, resamples=1000, seed=3)
        self.assertLessEqual(lower, sum(values) / len(values))
        self.assertGreaterEqual(upper, sum(values) / len(values))

    def test_coefficient_of_variation(self):
        self.assertAlmostEqual(
            coefficient_of_variation([1.0, 2.0, 3.0]),
            (2.0 / 3.0) ** 0.5 / 2.0,
        )

    def test_invalid_inputs_raise(self):
        with self.assertRaises(ValueError):
            summarize([])
        with self.assertRaises(ValueError):
            bootstrap_mean_interval([1.0], confidence=1.0)
        with self.assertRaises(ValueError):
            coefficient_of_variation([0.0, 0.0])


if __name__ == "__main__":
    unittest.main()
