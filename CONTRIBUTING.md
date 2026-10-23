# Contributing to PowerAgentBench

PowerAgentBench is intended to support reproducible evaluation of power-system agents. Contributions should strengthen the benchmark contract, physical validity, agent reproducibility, or evaluation coverage.

## Before changing benchmark behavior

For substantial new features, dependencies, command-line tools, or file formats, discuss the problem and proposed scope in an issue or draft pull request before implementation. Explain the concrete use case and why existing functionality is insufficient. A documented manual workflow is acceptable. Small bug fixes and documentation corrections do not require a separate proposal.

1. Read the benchmark README and the task-specific specification.
2. Keep public task inputs separate from hidden oracle information.
3. Preserve deterministic seeds and record any new source of randomness.
4. Add or update tests for changed scoring, action validation, or serialization behavior. Cover successful inputs, rejected inputs, and relevant boundary cases.
5. Do not commit API keys, private endpoints, model outputs containing secrets, or licensed simulator data.

## Test locally

Run the tests relevant to the change. For shared-library changes that affect both Level 1 and Level 2, run both suites.

From the repository root, install the package and test dependencies:

```bash
python -m pip install -e . pytest
```

Run the shared Level 1/library contract suite and solution-value regression tests:

```bash
python -m pytest -q tests/test_benchmark_utils_contract.py tests/test_solution_value_validation.py
```

This suite runs in CI on Python 3.10, 3.11, and 3.12 for pull requests and for pushes to `main` and branches matching `feat/**` or `fix/**`.

Run the Level 2 anytime-risk regression tests separately:

```bash
python -m unittest discover -s tests -p 'test_anytime_risk.py' -v
```

The Level 2 CI matrix uses Python 3.11 and 3.12. For Level 3 and dynamic benchmarks, follow their task-specific README instructions. The commands above do not run the self-contained Level 3 suite or dynamic simulator evaluations.

When adding a test module, ensure that an appropriate CI job collects it, or explain why it requires manual validation. Update the documented test commands. Passing a unit or contract suite does not establish that full benchmark simulations were run.

## Benchmark changes

When adding a task or metric, document:

- the task objective and agent-visible information,
- the action and observation schema,
- the validation/oracle boundary,
- deterministic seeding and case-generation rules,
- metric definitions, interpretation, and edge-case behavior,
- resource requirements and whether the task can run without licensed software.

Keep the root README as an overview and place detailed task contracts and metric definitions in the task-specific README. Keep terminology, field names, units, and test commands consistent across the affected documentation and implementation.

For intentional changes to benchmark results, regenerate affected reference outputs and explain the expected numerical differences and the impact on comparisons with previous results. If regeneration cannot be performed, state the limitation and reason in the pull request. Do not change expected test results merely to make a failing test pass.

## Pull requests

Use a focused pull request with a descriptive title and complete the [pull request template](.github/pull_request_template.md). Keep unrelated refactoring or infrastructure changes separate from the main contribution.

Report the test commands actually executed, their results, the Python version, and any validation not performed. Link relevant CI runs and identify the tested revision. For documentation-only changes, explain why tests were not run.

Keep the description and validation summary current after review changes. Explain compatibility or reproducibility impacts, including dependency changes, new output fields, and changes to scoring or accepted inputs.