# Benchmark artifact manifests

PowerAgentBench can emit per-case CSVs, aggregate summaries, tool logs, and other experiment artifacts. A checksum manifest makes it easier to confirm that those files have not changed between evaluation, review, and publication.

The manifest utility uses only the Python standard library and does not alter benchmark results.

## Create a manifest

Run from the repository root after a benchmark has finished:

```bash
python -m poweragentbench.artifact_manifest create results/steady_n2 \
  --metadata-json '{"case_source":"case39","seed_start":1000,"cases":8,"budget":80}'
```

This writes `run_manifest.json` inside the selected results directory. It records each regular file's relative path, byte size, and SHA-256 digest, plus a UTC creation timestamp and the metadata supplied explicitly on the command line.

Metadata is optional. Supply only non-sensitive details that help reproduce the run, such as scenario source, seed range, budget, model identifier, or code revision. The utility does not collect environment variables or credentials.

## Verify a manifest

Run verification before sharing or analyzing the artifacts:

```bash
python -m poweragentbench.artifact_manifest verify results/steady_n2
```

A successful verification exits with status 0. A missing or modified file, malformed manifest, unsafe path, or invalid checksum exits non-zero and reports the problem. The verifier checks the files listed in the manifest; it does not assert that the experiment itself is scientifically valid or that every unlisted file is absent.

Use a separate manifest per result directory or campaign to keep artifact inventories scoped and understandable.
