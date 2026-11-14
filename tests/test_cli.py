import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def test_help_lists_required_options(self):
        result = subprocess.run([sys.executable, "-m", "repoinspector", "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--path", result.stdout)
        self.assertIn("--output", result.stdout)

    def test_cli_writes_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            (project / "main.py").write_text("print('hello')\n", encoding="utf-8")
            prefix = root / "reports" / "scan"
            result = subprocess.run([sys.executable, "-m", "repoinspector", "--path", str(project), "--output", str(prefix)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            json_path = prefix.with_suffix(".json")
            md_path = prefix.with_suffix(".md")
            self.assertTrue(json_path.is_file())
            self.assertTrue(md_path.is_file())
            parsed = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(parsed["summary"]["files"]["total"], 1)
            self.assertIn("RepoInspector", md_path.read_text(encoding="utf-8"))

    def test_cli_rejects_missing_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, "-m", "repoinspector", "--path", str(Path(tmp) / "missing")], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not exist", result.stderr)


if __name__ == "__main__":
    unittest.main()
