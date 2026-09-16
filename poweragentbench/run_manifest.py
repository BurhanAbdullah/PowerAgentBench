"""Reproducibility helpers for PowerAgentBench campaigns.

The manifest is deliberately independent of model providers and simulators. It
captures the benchmark configuration, deterministic case seeds, repository
revision, and execution metadata needed to identify a run without storing
private prompts, credentials, endpoints, or hidden oracle data.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

MANIFEST_VERSION = "1"


@dataclass(frozen=True)
class RunManifest:
    benchmark: str
    track: str
    cases: int
    seed_start: int
    seeds: tuple[int, ...]
    k: int
    validation_budget: int
    report_k: int
    case_source: str
    config: Mapping[str, Any] = field(default_factory=dict)
    repository_revision: str = "unknown"
    python_version: str = ""
    platform: str = ""
    created_at_utc: str = ""
    manifest_version: str = MANIFEST_VERSION
    manifest_sha256: str = ""


def git_revision(repo_root: str | Path = ".") -> str:
    """Return the current git revision, or ``unknown`` outside a checkout."""
    try:
        value = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
        return value or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def canonical_json(payload: Mapping[str, Any]) -> str:
    """Serialize a manifest payload deterministically for hashing/storage."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def manifest_fingerprint(payload: Mapping[str, Any]) -> str:
    """Compute a stable SHA-256 fingerprint for manifest identity."""
    unsigned = dict(payload)
    unsigned.pop("manifest_sha256", None)
    return hashlib.sha256(canonical_json(unsigned).encode("utf-8")).hexdigest()


def build_manifest(
    *,
    benchmark: str,
    track: str,
    cases: int,
    seed_start: int,
    k: int,
    validation_budget: int,
    report_k: int,
    case_source: str,
    config: Mapping[str, Any] | None = None,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    """Build a JSON-safe, reproducible description of a benchmark campaign."""
    if cases < 0:
        raise ValueError("cases must be non-negative")
    if k < 1:
        raise ValueError("k must be at least 1")
    if validation_budget < 0:
        raise ValueError("validation_budget must be non-negative")
    if report_k < 1:
        raise ValueError("report_k must be at least 1")

    seeds = [seed_start + i for i in range(cases)]
    payload: dict[str, Any] = {
        "benchmark": benchmark,
        "track": track,
        "cases": cases,
        "seed_start": seed_start,
        "seeds": seeds,
        "k": k,
        "validation_budget": validation_budget,
        "report_k": report_k,
        "case_source": case_source,
        "config": dict(config or {}),
        "repository_revision": git_revision(repo_root),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_version": MANIFEST_VERSION,
    }
    payload["manifest_sha256"] = manifest_fingerprint(payload)
    return payload


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    """Validate structural and determinism invariants of a stored manifest."""
    required = {
        "benchmark", "track", "cases", "seed_start", "seeds", "k",
        "validation_budget", "report_k", "case_source", "config",
        "repository_revision", "python_version", "platform", "created_at_utc",
        "manifest_version", "manifest_sha256",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise ValueError(f"Manifest missing required fields: {', '.join(missing)}")

    cases = manifest["cases"]
    if not isinstance(cases, int) or cases < 0:
        raise ValueError("Manifest 'cases' must be a non-negative integer")
    seeds = manifest["seeds"]
    if seeds != [manifest["seed_start"] + i for i in range(cases)]:
        raise ValueError("Manifest seeds are not a deterministic seed_start sequence")
    if manifest["manifest_version"] != MANIFEST_VERSION:
        raise ValueError(f"Unsupported manifest version: {manifest['manifest_version']}")

    expected = manifest_fingerprint(manifest)
    if manifest["manifest_sha256"] != expected:
        raise ValueError("Manifest SHA-256 fingerprint does not match its contents")


def write_manifest(path: str | Path, manifest: Mapping[str, Any]) -> Path:
    """Validate and write a manifest as stable pretty-printed JSON."""
    validate_manifest(manifest)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(dict(manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination


def read_manifest(path: str | Path) -> dict[str, Any]:
    """Load and validate a manifest from disk."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Manifest root must be a JSON object")
    validate_manifest(payload)
    return payload


def shard_seeds(seeds: Sequence[int], shard_index: int, shard_count: int) -> list[int]:
    """Partition seeds deterministically using round-robin sharding."""
    if shard_count < 1:
        raise ValueError("shard_count must be at least 1")
    if not 0 <= shard_index < shard_count:
        raise ValueError("shard_index must satisfy 0 <= shard_index < shard_count")
    return [seed for offset, seed in enumerate(seeds) if offset % shard_count == shard_index]


def merge_case_results(rows: Sequence[Mapping[str, Any]], expected_seeds: Sequence[int]) -> list[dict[str, Any]]:
    """Validate and deterministically sort per-case results for aggregation."""
    expected = list(expected_seeds)
    seen: dict[int, dict[str, Any]] = {}
    for row in rows:
        if "case_seed" not in row:
            raise ValueError("Every result row must contain case_seed")
        seed = int(row["case_seed"])
        if seed in seen:
            raise ValueError(f"Duplicate case_seed in results: {seed}")
        seen[seed] = dict(row)

    missing = [seed for seed in expected if seed not in seen]
    unexpected = [seed for seed in seen if seed not in expected]
    if missing or unexpected:
        raise ValueError(f"Result seed mismatch; missing={missing}, unexpected={unexpected}")
    return [seen[seed] for seed in expected]
