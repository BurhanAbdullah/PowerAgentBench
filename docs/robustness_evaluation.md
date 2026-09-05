# Robustness evaluation for power-system agents

PowerAgentBench evaluates agents on operational tasks where a single successful
run can be misleading: LLM responses, screening choices, and validation order
may vary across runs. Repeated evaluation should therefore report both central
performance and dispersion.

The `poweragentbench.robustness` module provides solver- and provider-agnostic
statistics for a vector of already-computed benchmark outcomes. It does not
access hidden oracle values and does not change the agent/evaluator protocol.

## Recommended reporting

For repeated runs, report:

- `n`: number of finite runs;
- mean and standard deviation;
- minimum and maximum outcome;
- 5th, 50th, and 95th percentiles;
- a deterministic percentile-bootstrap confidence interval for the mean;
- coefficient of variation when the metric mean is materially non-zero.

For a safety or reliability metric, also report the fraction of runs meeting a
pre-declared threshold. The threshold should be specified before evaluating
models and should not be selected after seeing the results.

## Why this matters

The existing benchmark already separates discovery, evidence, mitigation,
action cost, and workflow behavior. A robustness layer adds the missing
question: **does an agent behave consistently across repeated stochastic runs?**

This is especially important for stress evaluation, where small changes in
prompting or model sampling can alter the contingency search trajectory.
A high mean score with a wide tail is scientifically different from a slightly
lower mean with stable behavior.

## Example

```python
from poweragentbench.robustness import bootstrap_mean_interval, summarize

scores = [0.72, 0.81, 0.77, 0.76, 0.83]
summary = summarize(scores)
ci_low, ci_high = bootstrap_mean_interval(scores, seed=2026)

print(summary.mean, summary.std, summary.p05, summary.p95)
print(ci_low, ci_high)
```

The bootstrap uses a local seeded random generator, so repeated report
creation is deterministic and does not modify the process-global RNG state.
