# PowerAgentBench

PowerAgentBench is a benchmark suite for evaluating AI agents on power-system operation and planning tasks. The current release includes steady-state and dynamic-study tracks, covering contingency analysis, AC power-flow convergence restoration, dynamic model-quality review, dynamic security-risk screening, scripted baselines, and LLM/tool-agent evaluation.

The benchmark is built around a public/hidden split. Agents see public case data, scenarios, action spaces, and tool APIs. Hidden evaluators recompute steady-state or dynamic validity and return discovery, evidence, safety, mitigation, efficiency, workflow, and reliability metrics.

## Repository Structure

```text
PowerAgentBench/
├── cases/                                      # Network case data in multiple formats
│   ├── case39/
│   │   ├── pypsa/case39.nc                     # PyPSA netCDF format
│   │   ├── matpower/case39.m                   # MATPOWER .m format
│   │   └── pandapower/case39.json              # PandaPower JSON format
│   └── solar_wecc/
│       └── psse/                               # WECC solar PV dynamic case (PSS/E)
│           ├── Solar.sav                       # Power-flow case
│           └── Solar.dyr                       # Dynamic model (corrupted REECAU1 gains)
├── benchmarks/                                 # Benchmark definitions and task configs
│   ├── steady/
│   │   ├── level_1/                            # N-1 steady-state audit and mitigation
│   │   ├── level_2/                            # Agentic N-2 search and mitigation
│   │   └── level_3/                            # RestoreBench: AC power-flow convergence restoration
│   └── dynamic/
│       └── level1/                             # Dynamic model-quality review
├── scripts/                                    # Runnable entry points
│   ├── build_case.py
│   ├── convert_case.py
│   ├── evaluate_solution.py
│   ├── make_run_manifest.py                    # Create a reproducible campaign manifest
│   ├── run_steady_n2_baselines.py
│   ├── run_steady_n2_ollama_eval.py
│   └── run_steady_n2_openai_eval.py
├── tests/                                      # Lightweight root-level contract tests
└── poweragentbench/                            # Shared benchmark library
    ├── benchmark_utils.py
    ├── run_manifest.py                         # Reproducibility, sharding, result integrity
    ├── steady_state_agentic.py
    ├── llm_agent_adapter.py
    ├── ollama_client.py
    └── openai_client.py
```

## Installation

```bash
pip install -e .
```

The package intentionally uses lightweight Python dependencies. Provider SDKs are not required for the built-in Ollama and OpenAI runners because both clients use standard-library HTTP calls.

## Quick Start

### Level 1: N-1 steady-state audit and mitigation

```bash
python scripts/build_case.py
python scripts/convert_case.py
python scripts/evaluate_solution.py --solution benchmarks/steady/level_1/solution_template.json
```

### Level 2: Agentic N-2 steady-state evaluation

Run scripted baselines on deterministic variants of the IEEE 39-bus case:

```bash
python scripts/run_steady_n2_baselines.py \
  --case-source case39 \
  --cases 8 \
  --budget 80 \
  --report-k 20
```

The same evaluation protocol can be used with Ollama-hosted or OpenAI-compatible agents; see `benchmarks/steady/level_2/README.md` for provider configuration and output details.

### Reproducible campaign manifests

Every multi-case campaign should have an explicit manifest describing the benchmark track, case source, deterministic seed sequence, search parameters, repository revision, runtime environment, and a SHA-256 fingerprint. Create one before a campaign:

```bash
python scripts/make_run_manifest.py \
  --output results/steady_n2/run_manifest.json \
  --track steady_n2 \
  --case-source case39 \
  --cases 8 \
  --seed-start 1000 \
  --k 2 \
  --budget 80 \
  --report-k 20
```

The manifest records only reproducibility metadata; do not put API keys, private endpoints, hidden oracle labels, prompts containing secrets, or licensed simulator data into it. Its `manifest_sha256` fingerprint makes accidental or post-hoc configuration edits detectable.

The shared library also provides deterministic round-robin case sharding and result merging:

```python
from poweragentbench.run_manifest import merge_case_results, shard_seeds

shard = shard_seeds(manifest["seeds"], shard_index=0, shard_count=4)
merged = merge_case_results(rows_from_all_workers, manifest["seeds"])
```

Shards are disjoint and cover the manifest seed set exactly. Result merging rejects duplicate, missing, or unexpected case seeds and restores the manifest's canonical order. This permits parallel workers to produce partial result files without changing the final case ordering.

### Level 3: RestoreBench — AC power-flow convergence restoration

Level 3 is self-contained and uses `uv` with a pinned lockfile. Install and run it from `benchmarks/steady/level_3/`:

```bash
uv sync
uv run restorebench-verify --dataset-dir dataset/pegase89
uv run restorebench-score attempt.json
```

See `benchmarks/steady/level_3/README.md` for the full specification.

## Case Formats

The IEEE 39-bus stressed scenario is provided in PyPSA, PandaPower, and MATPOWER formats. The existing Level 2 engine converts the repository case into a lightweight DC representation and supports deterministic operating-point variants.

## Evaluation and Reproducibility

PowerAgentBench separates benchmark inputs from hidden evaluation. Public agent inputs and tool contracts can be inspected, while hidden oracle calculations remain evaluator-side. Deterministic campaign manifests extend that separation into reproducible experiment execution by fixing the case seed set and configuration identity.

For published or shared results, retain the run manifest next to per-case and aggregate outputs. A reproducible result should be identifiable by:

1. repository revision,
2. manifest fingerprint,
3. ordered case seeds,
4. benchmark configuration,
5. agent/provider identifier,
6. result files and logs that contain no secrets.

The manifest tooling does not claim that a model run is scientifically reproducible by itself; model/provider versions, external simulator versions, and any stochastic behavior still need to be recorded when they affect the run.

## Metrics

PowerAgentBench returns per-case and aggregate metrics including discovery recall, evidence quality, severity capture/regret, false-safe behavior, post-action violation, mitigation, action cost, invalid tool calls, schema repairs, duplicate validation requests, workflow completion, and validation budget use.

## Development

Before changing benchmark behavior:

- preserve the public/hidden boundary;
- keep random generation deterministic and record seeds;
- add tests for changed scoring, validation, serialization, or aggregation behavior;
- never commit credentials, private endpoints, secrets, or licensed data.

Run the root contract tests locally with:

```bash
python -m pip install -e . pytest
pytest -q
```

The repository CI additionally runs the contract suite on Python 3.11 for pull requests and main/feature pushes.
