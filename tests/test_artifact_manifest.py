import json
import tempfile
import unittest
from pathlib import Path

from poweragentbench.artifact_manifest import (
    DEFAULT_MANIFEST,
    build_manifest,
    verify_manifest,
    write_manifest,
)


class ArtifactManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "baseline_per_case.csv").write_text("agent,score\nA,0.5\n", encoding="utf-8")
        (self.root / "nested").mkdir()
        (self.root / "nested" / "summary.json").write_text('{"score": 0.5}\n', encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_manifest_lists_sorted_relative_files_with_hashes(self):
        manifest = build_manifest(self.root, metadata={"seed": 42})
        paths = [entry["path"] for entry in manifest["files"]]
        self.assertEqual(paths, ["baseline_per_case.csv", "nested/summary.json"])
        self.assertEqual(manifest["metadata"], {"seed": 42})
        self.assertEqual(len(manifest["files"][0]["sha256"]), 64)
        self.assertNotIn(DEFAULT_MANIFEST, paths)

    def test_written_manifest_verifies(self):
        write_manifest(self.root, metadata={"case_source": "case39", "seed": 7})
        self.assertEqual(verify_manifest(self.root), [])

    def test_modified_file_is_detected(self):
        write_manifest(self.root)
        (self.root / "baseline_per_case.csv").write_text("agent,score\nA,0.9\n", encoding="utf-8")
        errors = verify_manifest(self.root)
        self.assertIn("SHA-256 mismatch: baseline_per_case.csv", errors)

    def test_missing_file_is_detected(self):
        write_manifest(self.root)
        (self.root / "nested" / "summary.json").unlink()
        self.assertIn("missing artifact: nested/summary.json", verify_manifest(self.root))

    def test_manifest_path_rejects_traversal(self):
        with self.assertRaises(ValueError):
            build_manifest(self.root, manifest_path="../outside.json")
        self.assertIn("manifest path must be a safe relative path",
                      verify_manifest(self.root, manifest_path="../outside.json"))

    def test_manifest_rejects_non_json_metadata(self):
        with self.assertRaises(ValueError):
            build_manifest(self.root, metadata={"bad": object()})

    def test_invalid_manifest_json_is_reported(self):
        (self.root / DEFAULT_MANIFEST).write_text("{bad", encoding="utf-8")
        self.assertTrue(verify_manifest(self.root)[0].startswith("cannot read manifest:"))

    def test_manifest_root_must_be_object(self):
        (self.root / DEFAULT_MANIFEST).write_text("[]", encoding="utf-8")
        self.assertEqual(verify_manifest(self.root), ["manifest root must be a JSON object"])

    def test_unsafe_artifact_path_is_rejected(self):
        write_manifest(self.root)
        manifest_path = self.root / DEFAULT_MANIFEST
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data["files"][0]["path"] = "../outside.csv"
        manifest_path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("files[0].path must be a safe relative path", verify_manifest(self.root))

    def test_duplicate_artifact_paths_are_rejected(self):
        write_manifest(self.root)
        manifest_path = self.root / DEFAULT_MANIFEST
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data["files"].append(dict(data["files"][0]))
        manifest_path.write_text(json.dumps(data), encoding="utf-8")
        self.assertTrue(any("duplicates" in error for error in verify_manifest(self.root)))

    def test_wrong_schema_version_is_rejected(self):
        write_manifest(self.root)
        manifest_path = self.root / DEFAULT_MANIFEST
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data["schema_version"] = 99
        manifest_path.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(verify_manifest(self.root), ["schema_version must equal 1"])


if __name__ == "__main__":
    unittest.main()
