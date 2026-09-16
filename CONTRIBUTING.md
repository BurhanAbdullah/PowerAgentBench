# Contributing to PowerAgentBench

PowerAgentBench is intended to support reproducible evaluation of power-system agents. Contributions should strengthen the benchmark contract, physical validity, agent reproducibility, or evaluation coverage.

## Before changing benchmark behavior

1. Read the benchmark README and the task-specific specification.
2. Keep public task inputs separate from hidden oracle information.
3. Preserve deterministic seeds and record any new source of randomness.
4. Add or update tests for changed scoring, action validation, or serialization behavior.
5. Do not commit API keys, private endpoints, model outputs containing secrets, or licensed simulator data.

## Test locally

From the repository root:

```bash
python -m pip install -e . pytest
pytest -q tests/test_benchmark_utils_contract.py
```

The repository CI runs the same contract suite on Python 3.11 for every pull request and for pushes to `main` and feature branches.

## Benchmark changes

When adding a task or metric, document:

- the task objective and agent-visible information,
- the action and observation schema,
- the validation/oracle boundary,
- deterministic seeding and case-generation rules,
- metric definitions and edge-case behavior,
- resource requirements and whether the task can run without licensed software.

For changes to existing benchmark results, regenerate affected outputs and explain the reproducibility impact in the pull request.

## Pull requests

Use a focused pull request with a descriptive title. Include the problem being solved, the benchmark behavior that changes, tests run, and any compatibility or reproducibility considerations.
