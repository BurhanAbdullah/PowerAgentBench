from __future__ import annotations

import json
from pathlib import Path

import pytest

from poweragentbench.run_manifest import (
    build_manifest,
    manifest_fingerprint,
    merge_case_results,
    read_manifest,
    shard_seeds,
    validate_manifest,
    write_manifest,
)


def test_manifest_has_deterministic_seed_sequence() -> None:
    manifest = build_manifest(
        benchmark="PowerAgentBench",
        track="steady_n2",
        cases=5,
        seed_start=1000,
        k=2,
        validation_budget=80,
        report_k=20,
        case_source="synthetic",
    )
    assert manifest["seeds"] == [1000, 1001, 1002, 1003, 1004]
    assert manifest["manifest_sha256"] == manifest_fingerprint(manifest)


def test_manifest_round_trips(tmp_path: Path) -> None:
    manifest = build_manifest(
        benchmark="PowerAgentBench",
        track="steady_n2",
        cases=2,
        seed_start=10,
        k=2,
        validation_budget=4,
        report_k=2,
        case_source="synthetic",
    )
    path = write_manifest(tmp_path / "manifest.json", manifest)
    assert read_manifest(path) == manifest


def test_manifest_detects_tampering(tmp_path: Path) -> None:
    manifest = build_manifest(
        benchmark="PowerAgentBench",
        track="steady_n2",
        cases=1,
        seed_start=7,
        k=2,
        validation_budget=4,
        report_k=2,
        case_source="synthetic",
    )
    payload = dict(manifest)
    payload["validation_budget"] = 999
    with pytest.raises(ValueError, match="fingerprint"):
        validate_manifest(payload)


def test_manifest_rejects_non_deterministic_seeds() -> None:
    manifest = build_manifest(
        benchmark="PowerAgentBench",
        track="steady_n2",
        cases=3,
        seed_start=20,
        k=2,
        validation_budget=4,
        report_k=2,
        case_source="synthetic",
    )
    payload = dict(manifest)
    payload["seeds"] = [20, 22, 23]
    payload["manifest_sha256"] = manifest_fingerprint(payload)
    with pytest.raises(ValueError, match="deterministic seed_start sequence"):
        validate_manifest(payload)


def test_sharding_is_complete_and_disjoint() -> None:
    seeds = list(range(10, 18))
    shards = [shard_seeds(seeds, i, 3) for i in range(3)]
    assert sorted(x for shard in shards for x in shard) == seeds
    assert len(set(x for shard in shards for x in shard)) == len(seeds)


def test_invalid_shard_is_rejected() -> None:
    with pytest.raises(ValueError):
        shard_seeds([1, 2], 2, 2)


def test_merge_orders_rows_by_manifest_seed_order() -> None:
    expected = [101, 100, 102]
    rows = [
        {"case_seed": 102, "score": 3},
        {"case_seed": 100, "score": 1},
        {"case_seed": 101, "score": 2},
    ]
    merged = merge_case_results(rows, expected)
    assert [row["case_seed"] for row in merged] == expected


def test_merge_rejects_missing_or_extra_seed() -> None:
    with pytest.raises(ValueError, match="seed mismatch"):
        merge_case_results([{"case_seed": 1}], [1, 2])


def test_merge_rejects_duplicate_seed() -> None:
    rows = [{"case_seed": 1}, {"case_seed": 1}]
    with pytest.raises(ValueError, match="Duplicate case_seed"):
        merge_case_results(rows, [1])
