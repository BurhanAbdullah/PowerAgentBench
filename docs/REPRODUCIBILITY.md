# Reproducible Benchmark Campaigns

PowerAgentBench campaign results should be reproducible and auditable without exposing credentials, private endpoints, hidden oracle information, or licensed simulator data.

## 1. Create a run manifest

Create a manifest before launching a multi-case campaign:

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

The manifest records the benchmark/track, ordered deterministic seeds, search parameters, case source, repository revision, Python/runtime metadata, and a SHA-256 fingerprint. The fingerprint is calculated over the manifest contents excluding the fingerprint itself, so configuration edits are detectable.

## 2. Parallel deterministic sharding

Workers can partition the manifest seed list with deterministic round-robin sharding:

```python
from poweragentbench.run_manifest import shard_seeds

worker_seeds = shard_seeds(
    manifest["seeds"],
    shard_index=0,
    shard_count=4,
)
```

For a fixed manifest, shard membership is deterministic, shards are disjoint, and their union is exactly the manifest seed set.

## 3. Strict result merging

Merge worker outputs only after validating their case seeds:

```python
from poweragentbench.run_manifest import merge_case_results

merged = merge_case_results(worker_rows, manifest["seeds"])
```

The merger rejects duplicate, missing, or unexpected seeds and restores the canonical manifest order. This prevents partial or duplicated worker output from silently entering aggregate results.

## 4. Integrity rules

A reproducible campaign should retain, at minimum:

- the exact repository revision;
- the versioned run manifest and `manifest_sha256`;
- the ordered case seeds;
- benchmark configuration and search/validation budgets;
- agent/model/provider identifiers and relevant model settings;
- per-case results and aggregate results;
- tool/event logs needed to audit the agent workflow;
- external simulator versions where they affect results.

Never place API keys, private endpoints, hidden oracle labels, secret prompts, or licensed simulator datasets in a public manifest or result artifact.

## 5. Validation

The repository's reproducibility tests cover seed generation, manifest round-tripping, fingerprint tamper detection, deterministic sharding, and strict result merging. Run them with:

```bash
pytest -q tests/test_run_manifest.py
```

The CI workflow also performs a manifest-generation smoke test. A passing manifest test verifies the tooling contract; it does not by itself establish that an external model or simulator is deterministic.
