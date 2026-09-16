# Reproducible Benchmark Campaigns

PowerAgentBench campaign results should be reproducible and auditable without exposing credentials, private endpoints, hidden oracle information, or licensed simulator data.

## Create a run manifest

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

The manifest records the benchmark/track, ordered deterministic seeds, search parameters, case source, repository revision, Python/runtime metadata, and a SHA-256 fingerprint. The fingerprint covers the manifest contents except the fingerprint field itself, making post-hoc configuration edits detectable.

## Deterministic sharding

Workers partition the manifest seed list with round-robin sharding:

```python
from poweragentbench.run_manifest import shard_seeds
worker_seeds = shard_seeds(manifest["seeds"], shard_index=0, shard_count=4)
```

For a fixed manifest, shards are deterministic, disjoint, and collectively cover the seed set exactly.

## Strict result merging

```python
from poweragentbench.run_manifest import merge_case_results
merged = merge_case_results(worker_rows, manifest["seeds"])
```

The merger rejects duplicate, missing, or unexpected seeds and restores manifest order, preventing partial or duplicated worker output from silently entering aggregate results.

## Integrity requirements

Retain the exact repository revision, manifest and fingerprint, ordered seeds, benchmark configuration, agent/model/provider identifiers, per-case and aggregate results, relevant tool/event logs, and external simulator versions when applicable.

Never put API keys, private endpoints, hidden oracle labels, secret prompts, or licensed simulator datasets into public manifests or result artifacts.

## Validation

Run:

```bash
pytest -q tests/test_run_manifest.py
```

CI validates the manifest tooling across the supported Python versions and runs a manifest-generation smoke test. Passing these tests verifies the reproducibility tooling contract; it does not imply that an external model or simulator is deterministic.
