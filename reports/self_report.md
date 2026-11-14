# RepoInspector report

- Quality score: **32/100** (indicative)
- Files: 9 (7 Python, 2 JavaScript)
- Lines: 541 total, 483 code, 1 comments, 57 blank
- Findings: 13

## Scoring method

100 minus 2/6/12/20 points for low/medium/high/critical findings, bounded to 0..100; indicative only.

## Findings

- **low** `python.unused_import` — `examples/sample_project/bad.py:1` — Imported name 'os' appears unused; confidence: heuristic
- **low** `python.unused_import` — `examples/sample_project/bad.py:2` — Imported name 'math' appears unused; confidence: heuristic
- **medium** `python.empty_except` — `examples/sample_project/bad.py:47` — Exception handler is empty or only suppresses the error
- **medium** `python.broad_except` — `examples/sample_project/bad.py:47` — Exception handler catches too broadly
- **high** `security.dynamic_eval` — `examples/sample_project/bad.py:6` — Use of eval can execute input as code
- **medium** `function.too_long` — `examples/sample_project/bad.py:9` — Function 'too_long' spans 34 lines
- **low** `javascript.unused_import` — `examples/sample_project/web/app.js:1` — Imported name 'fs' appears unused; confidence: heuristic
- **low** `javascript.unused_import` — `examples/sample_project/web/app.js:2` — Imported name 'join' appears unused; confidence: heuristic
- **medium** `security.dom_injection` — `examples/sample_project/web/app.js:36` — innerHTML assignment can introduce DOM injection
- **medium** `function.too_long` — `examples/sample_project/web/app.js:4` — Function 'render' spans 34 lines
- **medium** `function.too_long` — `repoinspector/core.py:67` — Function '_python_findings' spans 58 lines
- **medium** `function.too_long` — `repoinspector/core.py:156` — Function '_javascript_findings' spans 43 lines
- **medium** `function.too_long` — `repoinspector/core.py:201` — Function 'analyze_path' spans 47 lines

## Limitations

Import and security checks are heuristic. This is not a complete type checker, linter, dependency scanner, or security audit.
