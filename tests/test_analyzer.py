import tempfile
import unittest
from pathlib import Path

from repoinspector import analyze_path


class AnalyzerTests(unittest.TestCase):
    def analyze(self, files):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel, content in files.items():
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(content, bytes):
                    target.write_bytes(content)
                else:
                    target.write_text(content, encoding="utf-8")
            return analyze_path(root)

    def test_recursive_detection_and_line_counts(self):
        report = self.analyze({
            "nested/sample.py": "# module comment\nimport math\nimport os\n\ndef area(r):\n    return math.pi * r * r\n",
            "web/app.js": "// comment\nconst label = \"ok\";\n\n",
            "ignored/node_modules/vendor.js": "eval(x);\n",
        })
        self.assertEqual(report["summary"]["files"]["python"], 1)
        self.assertEqual(report["summary"]["files"]["javascript"], 1)
        py = next(item for item in report["files"] if item["path"] == "nested/sample.py")
        self.assertEqual(py["lines"], {"total": 6, "code": 4, "blank": 1, "comments": 1})
        self.assertFalse(any("node_modules" in item["path"] for item in report["files"]))

    def test_python_unused_import_is_reported_conservatively(self):
        report = self.analyze({"a.py": "import os\nimport math\nprint(math.pi)\n"})
        findings = [f for f in report["findings"] if f["rule"] == "python.unused_import"]
        self.assertEqual([(f["line"], f["message"]) for f in findings], [(1, "Imported name 'os' appears unused")])
        self.assertIn("heuristic", findings[0]["confidence"].lower())

    def test_python_flags_empty_and_broad_except(self):
        report = self.analyze({"a.py": "try:\n    work()\nexcept:\n    pass\ntry:\n    work()\nexcept Exception:\n    pass\n"})
        rules = {f["rule"] for f in report["findings"]}
        self.assertIn("python.empty_except", rules)
        self.assertIn("python.broad_except", rules)

    def test_python_long_function_and_security(self):
        body = "\n".join(f"    value_{i} = {i}" for i in range(35))
        report = self.analyze({"a.py": "def long_task():\n" + body + "\n\ndef run(user_input):\n    return eval(user_input)\n"})
        self.assertTrue(any(f["rule"] == "function.too_long" and f["symbol"] == "long_task" for f in report["findings"]))
        self.assertTrue(any(f["rule"] == "security.dynamic_eval" for f in report["findings"]))

    def test_javascript_unused_import_long_function_and_security(self):
        body = "\n".join(f"  const value{i} = {i};" for i in range(35))
        source = "import fs from 'node:fs';\nimport { join } from 'node:path';\nconsole.log(join);\nfunction render(input) {\n" + body + "\n  target.innerHTML = input;\n}\n"
        report = self.analyze({"src/app.js": source})
        rules = {f["rule"] for f in report["findings"]}
        self.assertIn("javascript.unused_import", rules)
        self.assertIn("function.too_long", rules)
        self.assertIn("security.dom_injection", rules)

    def test_empty_directory_has_perfect_indicative_score(self):
        report = self.analyze({})
        self.assertEqual(report["summary"]["files"]["total"], 0)
        self.assertEqual(report["summary"]["quality_score"], 100)

    def test_missing_path_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"
            with self.assertRaises(FileNotFoundError):
                analyze_path(missing)

    def test_bad_encodings_are_reported_and_analysis_continues(self):
        report = self.analyze({"bad.py": b"\xff\xfe", "bad.js": b"\xff", "ok.py": "x = 1\n"})
        errors = [f for f in report["findings"] if f["rule"] == "file.read_error"]
        self.assertEqual(len(errors), 2)
        self.assertIn("ok.py", {f["path"] for f in report["files"]})

    def test_score_is_bounded_and_decreases_with_findings(self):
        clean = self.analyze({"ok.py": "x = 1\n"})
        noisy = self.analyze({"bad.py": "import os\ndef f(x):\n    return eval(x)\n"})
        self.assertGreaterEqual(noisy["summary"]["quality_score"], 0)
        self.assertLessEqual(noisy["summary"]["quality_score"], 100)
        self.assertLess(noisy["summary"]["quality_score"], clean["summary"]["quality_score"])


if __name__ == "__main__":
    unittest.main()
