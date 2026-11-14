# RepoInspector

RepoInspector is a small, dependency-free Python CLI that scans a local project containing Python and/or JavaScript and produces indicative quality findings.

## Features

- recursive `.py`, `.js`, `.jsx`, `.mjs`, and `.cjs` discovery;
- counts total, code, blank, and comment lines;
- flags long functions (more than 30 lines);
- heuristic unused-import detection;
- Python empty/broad `except` detection;
- a small set of security smell checks (`eval`, unsafe DOM assignment, `shell=True`, and similar);
- JSON and Markdown reports;
- an indicative score documented in each report.

This is not a full linter, type checker, dependency scanner, or security audit. Import and JavaScript checks are intentionally conservative heuristics.

## Usage

```bash
python -m repoinspector --help
python -m repoinspector --path examples/sample_project --output reports/sample
```

The command creates `reports/sample.json` and `reports/sample.md`.

## Tests

```bash
python -m unittest discover -s tests -v
```

No third-party package is required. GitHub Actions runs the same standard-library test command.
