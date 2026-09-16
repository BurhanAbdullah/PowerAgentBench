# PowerAgentBench

PowerAgentBench is a benchmark suite for evaluating AI agents on power-system operation and planning tasks. The current release includes steady-state and dynamic-study tracks, covering contingency analysis, AC power-flow convergence restoration, dynamic model-quality review, dynamic security-risk screening, scripted baselines, and LLM/tool-agent evaluation.

The benchmark is built around a public/hidden split. Agents see public case data, scenarios, action spaces, and tool APIs. Hidden evaluators recompute steady-state or dynamic validity and return discovery, evidence, safety, mitigation, efficiency, workflow, and reliability metrics.

## Repository Structure

```text
PowerAgentBench/
├── cases/
│   ├── case39/
│   │   ├── pypsa/case39.nc
│   │   ├── matpower/case39.m
│   │   └── pandapower/case39.json
│   └── solar_wecc/
│       └── psse/
│           ├── Solar.sav
│           └── Solar.dyr
├── benchmarks/
│   ├── steady/
│   │   ├── level_1/
│   │   │   ├── README.md
│   │   │   ├── actionspace.json
│   │   │   ├── actioncost.json
│   │   │   ├── baseline_summary.json
│   │   │   └── solution_template.json
│   │   ├── level_2/
│   │   │   ├── README.md
│   │   │   ├── .env.example
│   │   │   ├── .gitignore
│   │   │   └── prompts/
│   │   │       └── steady_n2_llm_prompt.json
│   │   └── level_3/
│   │       ├── README.md
│   │       ├── pyproject.toml
│   │       ├── restorebench/
│   │       ├── dataset/
│   │       └── tests/
│   └── dynamic/
│       └── level1/
│           ├── README.md
│           ├── actionspace.json
│           ├── actioncost.json
│           ├── baseline_summary.json
│           ├── solution_template.json
│           └── harness/
├── scripts/
│   ├── build_case.py
│   ├── convert_case.py
│   ├── evaluate_solution.py
│   ├── make_run_manifest.py
│   ├── run_steady_n2_baselines.py
│   ├── run_steady_n2_ollama_eval.py
│   └── run_steady_n2_openai_eval.py
├── tests/
└── poweragentbench/
    ├── benchmark_utils.py
    ├── run_manifest.py
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
python scripts/evaluate_solution.py \
  --solution benchmarks/steady/level_1/solution_template.json
```

### Level 2: Agentic N-2 search and mitigation

Run scripted baselines on deterministic variants of the existing IEEE 39-bus case:

```bash
python scripts/run_steady_n2_baselines.py \
  --case-source case39 \
  --cases 8 \
  --budget 80 \
  --report-k 20
```

Run deployed Ollama LLM agents:

```bash
python scripts/run_steady_n2_ollama_eval.py \
  --case-source case39 \
  --cases 8 \
  --budget 80 \
  --report-k 20 \
  --max-turns 12 \
  --prompt-template benchmarks/steady/level_2/prompts/steady_n2_llm_prompt.json
```

Run an OpenAI/ChatGPT-style agent:

```bash
python scripts/run_steady_n2_openai_eval.py \
  --case-source case39 \
  --cases 8 \
  --budget 80 \
  --report-k 20 \
  --max-turns 12 \
  --prompt-template benchmarks/steady/level_2/prompts/steady_n2_llm_prompt.json
```

Outputs are written under `results/steady_n2/` and `results/steady_n2_openai/`. Each run produces per-case CSVs, aggregate CSVs, tool logs, sanitized API debug files, and LaTeX table rows.

### Reproducible campaign manifests

Multi-case campaigns should use an explicit manifest describing the benchmark track, case source, deterministic seed sequence, search parameters, repository revision, runtime environment, and a SHA-256 fingerprint. Create one before a campaign:

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

The manifest records reproducibility metadata only. Do not put API keys, private endpoints, hidden oracle labels, prompts containing secrets, or licensed simulator data into it. The `manifest_sha256` fingerprint makes accidental or post-hoc configuration edits detectable.

The shared library provides deterministic round-robin case sharding and strict result merging:

```python
from poweragentbench.run_manifest import merge_case_results, shard_seeds

shard = shard_seeds(manifest["seeds"], shard_index=0, shard_count=4)
merged = merge_case_results(rows_from_all_workers, manifest["seeds"])
```

Shards are disjoint and cover the manifest seed set exactly. Result merging rejects duplicate, missing, or unexpected case seeds and restores the manifest's canonical order. This permits parallel workers to produce partial result files without changing final case ordering.

## Level 3: RestoreBench — AC power-flow convergence restoration

Level 3 is self-contained and uses `uv` with a pinned lockfile. Install and run it from its own directory:

```bash
cd benchmarks/steady/level_3
uv sync
uv run restorebench-verify --dataset-dir dataset/pegase89
uv run restorebench-score attempt.json
uv run restorebench-sweep --campaign ieee118-anthropic --dry-run
```

See `benchmarks/steady/level_3/README.md` for the full specification, datasets, agent architectures, and reproduction instructions.

## Case Formats

The IEEE 39-bus stressed scenario is provided in three formats:

- **PyPSA** (`cases/case39/pypsa/case39.nc`): primary format used by the Level 1 evaluator and Level 2 case39 converter.
- **PandaPower** (`cases/case39/pandapower/case39.json`): for PandaPower-based tools.
- **MATPOWER** (`cases/case39/matpower/case39.m`): for MATPOWER or compatible solvers.

## Benchmarks

### Steady Level 1

`benchmarks/steady/level_1/` evaluates N-1 steady-state audit and mitigation on a stressed IEEE 39-bus case. The agent receives a case, a published contingency list, and a bounded action space. The evaluator checks base-case and contingency violations after submitted actions.

### Steady Level 2

`benchmarks/steady/level_2/` evaluates agentic N-2 contingency search and optional mitigation. The agent must spend a limited validation budget, submit evidence-backed ranked contingencies, and optionally improve the hidden post-action violation score.

The default case source is the existing IEEE 39-bus case distributed in this repository. The runner converts it to a lightweight DC representation and creates deterministic operating-point variants from fixed seeds. A synthetic fallback is also available for development.

### Steady Level 3

`benchmarks/steady/level_3/` is **RestoreBench** — diagnosis and recovery of non-convergent AC power-flow cases using LLM-based agents. Every scenario is a grid snapshot for which AC power flow does not converge; the agent proposes reactive-control maneuvers with solver-grounded feedback and succeeds if convergence is restored within a ten-maneuver budget. It ships frozen IEEE 118-bus and PEGASE 89-bus corpora, a standalone scorer, and reference agent architectures on a deterministic pandapower environment.

### Dynamic Level 1

`benchmarks/dynamic/level1/` evaluates dynamic model-quality review on a modified WECC solar PV model. The agent runs the DMView model-quality test suite, diagnoses failures, and repairs the model by adjusting four allowed REECAU1 controller gains within a five-iteration budget.

> **Note:** Unlike the steady-state benchmarks, this dynamic benchmark requires licensed/external tooling: **PSS/E 36.2** and the **DMView 3.4** dynamic-model review tool, running on Python 3.11. Set `DMVIEW_ROOT` and `PY311` in `benchmarks/dynamic/level1/harness/config.py` for your installation.

## Model and API Configuration

Private model endpoints and API keys should not be committed. Configure them through a local `.env` file:

```bash
cp benchmarks/steady/level_2/.env.example benchmarks/steady/level_2/.env
```

The local `.env` file is ignored by Git. Settings may also be supplied through command-line flags or environment variables.

### Ollama configuration

```bash
POWERAGENTBENCH_OLLAMA_URL=http://localhost:11434/api/generate
POWERAGENTBENCH_OLLAMA_MODELS=qwen3.5:latest mistral-nemo:12b command-r:35b
POWERAGENTBENCH_OLLAMA_TEMPERATURE=0.0
POWERAGENTBENCH_OLLAMA_NUM_CTX=16384
POWERAGENTBENCH_OLLAMA_API_MODE=generate
POWERAGENTBENCH_OLLAMA_THINK=false
POWERAGENTBENCH_OLLAMA_SCHEMA_FORMAT=true
```

For internal deployments, replace the URL locally. Do not commit internal URLs. Raw thinking traces, when exposed by a model, are not parsed, scored, or required for benchmark results.

### OpenAI/ChatGPT configuration

```bash
POWERAGENTBENCH_OPENAI_API_KEY=sk-your-private-token
POWERAGENTBENCH_OPENAI_MODELS=gpt-5.5
POWERAGENTBENCH_OPENAI_URL=https://api.openai.com/v1/responses
POWERAGENTBENCH_OPENAI_TEMPERATURE=none
POWERAGENTBENCH_OPENAI_MAX_OUTPUT_TOKENS=4096
POWERAGENTBENCH_OPENAI_STRUCTURED_OUTPUTS=true
POWERAGENTBENCH_OPENAI_REASONING_EFFORT=medium
POWERAGENTBENCH_OPENAI_REASONING_SUMMARY=none
POWERAGENTBENCH_OPENAI_TIMEOUT=300
POWERAGENTBENCH_OPENAI_MAX_RETRIES=3
POWERAGENTBENCH_OPENAI_RETRY_BACKOFF=2.0
```

Reasoning models may reject a `temperature` parameter; use `POWERAGENTBENCH_OPENAI_TEMPERATURE=none` to omit it. The OpenAI runner uses sanitized API debug logs and does not store the API key, raw output text, or reasoning content.

## Metrics

PowerAgentBench returns per-case and aggregate metrics, including:

- submitted, evidence-backed, and found top-20 recall,
- evidence rate and unvalidated-claim rate,
- best severity capture and severity regret,
- false-safe rates and severity-weighted false negatives,
- post-action violation and violation reduction,
- action cost,
- invalid tool calls,
- schema repairs and type coercions,
- duplicate validation requests,
- explicit submission and auto-finalization indicators,
- validation budget use,
- completed and requested case counts.

These metrics distinguish answer quality, tool evidence, search quality, mitigation quality, safety behavior, and workflow compliance.

## Result Files

Typical Level 2 outputs include per-case CSVs, aggregate summaries, tool logs, sanitized API debug JSONL files, and LaTeX table rows under `results/steady_n2/` or `results/steady_n2_openai/`.

If an OpenAI run stops early after a retry failure, partial outputs are preserved with `_partial` in the filename and errors are written to an errors JSONL file.

## Development and Reproducibility

Before changing benchmark behavior:

- preserve the public/hidden boundary;
- keep random generation deterministic and record seeds;
- add tests for changed scoring, validation, serialization, or aggregation behavior;
- never commit credentials, private endpoints, secrets, or licensed data;
- regenerate affected results after modifying prompts, adapters, scoring rules, or case-generation settings.

Run the root contract and reproducibility tests locally with:

```bash
python -m pip install -e . pytest
pytest -q
```

The repository CI runs automated contract tests and reproducibility smoke tests on pull requests and pushes to `main` and feature branches.

For published or shared results, retain the run manifest next to per-case and aggregate outputs. A reproducible result should identify the repository revision, manifest fingerprint, ordered case seeds, benchmark configuration, agent/provider identifier, and result files/logs without secrets. The manifest tooling does not by itself guarantee scientific reproducibility; model/provider versions, external simulator versions, and stochastic behavior must also be recorded when they affect the run.
