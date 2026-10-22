"""Create and verify checksummed manifests for benchmark result artifacts.

The manifest deliberately records files and explicitly supplied metadata only.
It does not capture environment variables, credentials, or machine-specific paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

SCHEMA_VERSION = 1
DEFAULT_MANIFEST = "run_manifest.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative_path(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value:
        return None
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or any(part in ("", ".", "..") for part in candidate.parts):
        return None
    return candidate.as_posix()


def build_manifest(
    root: str | Path,
    metadata: Mapping[str, Any] | None = None,
    manifest_path: str = DEFAULT_MANIFEST,
) -> dict[str, Any]:
    """Build a manifest for regular files beneath *root*, excluding the manifest."""
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise NotADirectoryError(f"artifact root is not a directory: {root}")
    safe_manifest = _safe_relative_path(manifest_path)
    if safe_manifest is None:
        raise ValueError("manifest_path must be a safe relative path")
    try:
        json.dumps(metadata if metadata is not None else {})
    except (TypeError, ValueError) as exc:
        raise ValueError("metadata must be JSON-serializable") from exc

    files: list[dict[str, Any]] = []
    for path in sorted(root_path.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        resolved = path.resolve()
        if not resolved.is_relative_to(root_path):
            continue
        relative = path.relative_to(root_path).as_posix()
        if relative == safe_manifest:
            continue
        files.append({
            "path": relative,
            "size_bytes": path.stat().st_size,
            "sha256": _sha256(path),
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "metadata": dict(metadata or {}),
        "files": files,
    }


def write_manifest(
    root: str | Path,
    metadata: Mapping[str, Any] | None = None,
    manifest_path: str = DEFAULT_MANIFEST,
) -> Path:
    """Create a JSON manifest under *root* and return its path."""
    root_path = Path(root).resolve()
    manifest = build_manifest(root_path, metadata=metadata, manifest_path=manifest_path)
    target = root_path / manifest_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def verify_manifest(root: str | Path, manifest_path: str = DEFAULT_MANIFEST) -> list[str]:
    """Return integrity errors for a manifest; an empty list means it verified."""
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        return [f"artifact root is not a directory: {root}"]
    safe_manifest = _safe_relative_path(manifest_path)
    if safe_manifest is None:
        return ["manifest path must be a safe relative path"]
    manifest_file = root_path / safe_manifest
    if manifest_file.is_symlink() or not manifest_file.is_file():
        return [f"manifest not found: {safe_manifest}"]
    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"cannot read manifest: {exc}"]
    if not isinstance(data, dict):
        return ["manifest root must be a JSON object"]
    if data.get("schema_version") != SCHEMA_VERSION:
        return [f"schema_version must equal {SCHEMA_VERSION}"]
    entries = data.get("files")
    if not isinstance(entries, list):
        return ["files must be a list"]

    errors: list[str] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        prefix = f"files[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        relative = _safe_relative_path(entry.get("path"))
        if relative is None:
            errors.append(f"{prefix}.path must be a safe relative path")
            continue
        if relative == safe_manifest:
            errors.append(f"{prefix}.path must not reference the manifest itself")
            continue
        if relative in seen:
            errors.append(f"{prefix}.path duplicates {relative!r}")
            continue
        seen.add(relative)
        target = root_path / relative
        if target.is_symlink() or not target.is_file():
            errors.append(f"missing artifact: {relative}")
            continue
        try:
            if not target.resolve().is_relative_to(root_path):
                errors.append(f"artifact escapes root: {relative}")
                continue
        except OSError:
            errors.append(f"cannot resolve artifact: {relative}")
            continue
        expected_size = entry.get("size_bytes")
        if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size < 0:
            errors.append(f"{prefix}.size_bytes must be a non-negative integer")
        elif target.stat().st_size != expected_size:
            errors.append(f"size mismatch: {relative}")
        expected_hash = entry.get("sha256")
        if not isinstance(expected_hash, str) or len(expected_hash) != 64 or any(
            char not in "0123456789abcdef" for char in expected_hash
        ):
            errors.append(f"{prefix}.sha256 must be a lowercase SHA-256 hex digest")
        elif _sha256(target) != expected_hash:
            errors.append(f"SHA-256 mismatch: {relative}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    create_parser = subparsers.add_parser("create", help="create a checksummed artifact manifest")
    create_parser.add_argument("root", type=Path, help="directory containing benchmark artifacts")
    create_parser.add_argument("--output", default=DEFAULT_MANIFEST, help="relative manifest path")
    create_parser.add_argument(
        "--metadata-json", default="{}", help="explicit JSON metadata, e.g. '{\"seed\": 42}'"
    )
    verify_parser = subparsers.add_parser("verify", help="verify artifacts against a manifest")
    verify_parser.add_argument("root", type=Path, help="directory containing benchmark artifacts")
    verify_parser.add_argument("--manifest", default=DEFAULT_MANIFEST, help="relative manifest path")
    args = parser.parse_args(argv)

    if args.action == "create":
        try:
            metadata = json.loads(args.metadata_json)
            if not isinstance(metadata, dict):
                raise ValueError("metadata JSON must be an object")
            path = write_manifest(args.root, metadata=metadata, manifest_path=args.output)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(f"Manifest written: {path}")
        return 0

    errors = verify_manifest(args.root, manifest_path=args.manifest)
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"Manifest verified: {args.root / args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
