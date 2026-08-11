import unittest

from poweragentbench.steady_state_agentic import (
    AgentOutput,
    compute_anytime_risk_metrics,
)


class TestAnytimeRiskMetrics(unittest.TestCase):
    def setUp(self):
        self.A, self.B, self.C, self.D = (0, 1), (0, 2), (0, 3), (0, 4)
        self.oracle = {
            self.A: 4.0,
            self.B: 3.0,
            self.C: 2.0,
            self.D: 1.0,
        }
        self.dangerous = set(self.oracle)

    def output(self, order, budget=4):
        return AgentOutput(
            name="toy",
            validated={c: self.oracle[c] for c in order},
            reported=[],
            validation_budget=float(budget),
        )

    def metrics(self, order, budget=4, oracle=None, dangerous=None):
        return compute_anytime_risk_metrics(
            self.output(order, budget),
            self.oracle if oracle is None else oracle,
            self.dangerous if dangerous is None else dangerous,
        )

    def test_known_early_trajectory(self):
        result = self.metrics([self.A, self.B, self.C, self.D])

        self.assertAlmostEqual(result["anytime_risk_auc"], 0.625)
        self.assertAlmostEqual(result["anytime_risk_at_25"], 0.40)
        self.assertAlmostEqual(result["anytime_risk_at_50"], 0.70)
        self.assertAlmostEqual(result["anytime_risk_at_75"], 0.90)
        self.assertAlmostEqual(result["anytime_risk_at_100"], 1.00)

    def test_early_discovery_beats_late_discovery(self):
        early = self.metrics([self.A, self.B, self.C, self.D])
        late = self.metrics([self.D, self.C, self.B, self.A])

        self.assertAlmostEqual(early["anytime_risk_auc"], 0.625)
        self.assertAlmostEqual(late["anytime_risk_auc"], 0.375)
        self.assertEqual(early["anytime_risk_at_100"], 1.0)
        self.assertEqual(late["anytime_risk_at_100"], 1.0)
        self.assertGreater(
            early["anytime_risk_auc"],
            late["anytime_risk_auc"],
        )

    def test_validation_budget_limits_trajectory(self):
        result = self.metrics(
            [self.A, self.B, self.C, self.D],
            budget=2,
        )

        self.assertAlmostEqual(result["anytime_risk_at_100"], 0.70)

    def test_empty_or_zero_risk_cases_return_zero(self):
        no_validation = self.metrics([], budget=0)
        no_danger = self.metrics([self.A], dangerous=set())

        zero_oracle = {self.A: 0.0, self.B: 0.0}
        zero_risk = self.metrics(
            [self.A, self.B],
            budget=2,
            oracle=zero_oracle,
            dangerous={self.A, self.B},
        )

        for result in (no_validation, no_danger, zero_risk):
            self.assertTrue(all(value == 0.0 for value in result.values()))

    def test_metrics_are_bounded(self):
        result = self.metrics([self.B, self.A, self.D, self.C])

        for name, value in result.items():
            with self.subTest(metric=name):
                self.assertGreaterEqual(value, 0.0)
                self.assertLessEqual(value, 1.0)


if __name__ == "__main__":
    unittest.main()


class TestScoreAgentAnytimeRiskIntegration(unittest.TestCase):

    def test_score_agent_exposes_anytime_risk_metrics(self):
        from unittest.mock import patch

        from poweragentbench.steady_state_agentic import PFResult, score_agent

        A = (0, 1)
        B = (0, 2)
        C = (0, 3)
        D = (0, 4)

        oracle_values = {
            A: 4.0,
            B: 3.0,
            C: 2.0,
            D: 1.0,
        }

        output = AgentOutput(
            name="integration",
            validated={
                A: 4.0,
                B: 3.0,
                C: 2.0,
                D: 1.0,
            },
            reported=[A, B, C, D],
            validation_budget=4.0,
        )

        fake_pf = PFResult(
            feasible=True,
            flows={},
            loading={},
            severity=1.0,
            island_penalty=0.0,
            outage=(),
        )

        with patch(
            "poweragentbench.steady_state_agentic.dc_power_flow",
            return_value=fake_pf,
        ):
            result = score_agent(
                original_case=None,
                output=output,
                oracle_values=oracle_values,
                top_m=4,
                danger_threshold=1.0,
            )

        for key in (
            "anytime_risk_auc",
            "anytime_risk_at_25",
            "anytime_risk_at_50",
            "anytime_risk_at_75",
            "anytime_risk_at_100",
        ):
            self.assertIn(key, result)
            self.assertGreaterEqual(result[key], 0.0)
            self.assertLessEqual(result[key], 1.0)

        self.assertAlmostEqual(result["anytime_risk_auc"], 0.625)
        self.assertAlmostEqual(result["anytime_risk_at_100"], 1.0)
