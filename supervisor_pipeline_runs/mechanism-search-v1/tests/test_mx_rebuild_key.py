"""Offline key reconstruction checks; every write goes to a temporary archive."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ARCHIVE = Path(__file__).resolve().parents[1]


class RebuildKeyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mx-key-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.script = self.root / "scripts/mx_rebuild_key.py"
        self.script.parent.mkdir()
        shutil.copyfile(ARCHIVE / "scripts/mx_rebuild_key.py", self.script)
        # Let the historical script run without importing its machine-specific
        # construction dependencies. The repaired script needs no ct_lib import.
        (self.script.parent / "ct_lib.py").write_text(f"V3 = {str(self.root)!r}\n")
        for pattern in ("instances/*/spec.json", "instances/*/validation.json",
                        "instances/*/reproduction.json",
                        "new_bug_variants/*/bug-1/L20/*/variant_manifest.json",
                        "review/VARIANT_KEY.json"):
            for source in ARCHIVE.glob(pattern):
                destination = self.root / source.relative_to(ARCHIVE)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
        self.key_path = self.root / "review/VARIANT_KEY.json"
        self.expected = json.loads(self.key_path.read_text())
        for entry in self.expected.values():
            entry["fresh"] = str(self.root / "construction/fresh" / entry["project"])

    def run_script(self, code=None):
        command = [sys.executable, "-B", str(self.script)]
        if code is not None:
            command = [sys.executable, "-B", "-c", code, str(self.script)]
        return subprocess.run(command, capture_output=True, text=True, timeout=30)

    def edit_spec(self, iid, **changes):
        path = self.root / "instances" / iid / "spec.json"
        spec = json.loads(path.read_text())
        spec.update(changes)
        path.write_text(json.dumps(spec))

    def test_rebuild_reproduces_all_43_archived_entries(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        actual = json.loads(self.key_path.read_text())
        self.assertEqual(sorted(actual), sorted(self.expected))
        self.assertEqual(actual, self.expected)

    def test_derived_overrides_can_clear_inherited_fields(self):
        self.edit_spec("P4-COMPRESS07-r1", group=None, entry_points=[],
                       evidence=[], fault_lines=["replacement fault line"])
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        actual = json.loads(self.key_path.read_text())
        self.assertTrue("CTV-822194" in actual, "valid derived instance was dropped")
        expected = dict(self.expected["CTV-822194"], group=None, entry_points=[],
                        evidence=[], fault_lines=["replacement fault line"])
        self.assertEqual(actual["CTV-822194"], expected)

    def test_unresolved_or_inconsistent_parent_preserves_existing_key(self):
        for changes in ({"parent_iid": "MISSING"},
                        {"parent_variant": "CTV-NOT-A-PARENT"},
                        {"parent_iid": "P4-COMPRESS07-r1",
                         "parent_variant": "CTV-822194"}):
            with self.subTest(changes=changes):
                self.edit_spec("P4-COMPRESS07-r1",
                               parent_iid="RH-LB-COMPRESS-07-ADAPTER",
                               parent_variant="CTV-1139CC")
                self.edit_spec("P4-COMPRESS07-r1", **changes)
                before = self.key_path.read_bytes()
                result = self.run_script()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.key_path.read_bytes(), before)

    def test_malformed_manifest_preserves_existing_key(self):
        manifest = next(self.root.glob("new_bug_variants/*/bug-1/L20/CTV-E7D846/variant_manifest.json"))
        manifest.write_text('{"artifact_hashes": {}}')
        before = self.key_path.read_bytes()
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.key_path.read_bytes(), before)

    def test_interrupted_write_preserves_existing_key(self):
        before = self.key_path.read_bytes()
        result = self.run_script("""
import json, runpy, sys
sys.path.insert(0, str(__import__('pathlib').Path(sys.argv[1]).parent))
def interrupted_dump(value, stream, **kwargs):
    stream.write('{"incomplete":')
    raise OSError('simulated write failure')
json.dump = interrupted_dump
runpy.run_path(sys.argv[1], run_name='__main__')
""")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("simulated write failure", result.stderr)
        self.assertEqual(self.key_path.read_bytes(), before)
        self.assertEqual(list(self.key_path.parent.iterdir()), [self.key_path])

    def test_import_does_not_rewrite_key(self):
        before = self.key_path.read_bytes()
        result = self.run_script("""
import runpy, sys
sys.path.insert(0, str(__import__('pathlib').Path(sys.argv[1]).parent))
runpy.run_path(sys.argv[1], run_name='safe_import')
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.key_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
