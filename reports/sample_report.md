# RepoInspector report

- Quality score: **50/100** (indicative)
- Files: 4 (2 Python, 2 JavaScript)
- Lines: 95 total, 85 code, 0 comments, 10 blank
- Findings: 10

## Scoring method

100 minus 2/6/12/20 points for low/medium/high/critical findings, bounded to 0..100; indicative only.

## Findings

- **low** `python.unused_import` — `bad.py:1` — Imported name 'os' appears unused; confidence: heuristic
- **low** `python.unused_import` — `bad.py:2` — Imported name 'math' appears unused; confidence: heuristic
- **medium** `python.empty_except` — `bad.py:47` — Exception handler is empty or only suppresses the error
- **medium** `python.broad_except` — `bad.py:47` — Exception handler catches too broadly
- **high** `security.dynamic_eval` — `bad.py:6` — Use of eval can execute input as code
- **medium** `function.too_long` — `bad.py:9` — Function 'too_long' spans 34 lines
- **low** `javascript.unused_import` — `web/app.js:1` — Imported name 'fs' appears unused; confidence: heuristic
- **low** `javascript.unused_import` — `web/app.js:2` — Imported name 'join' appears unused; confidence: heuristic
- **medium** `security.dom_injection` — `web/app.js:36` — innerHTML assignment can introduce DOM injection
- **medium** `function.too_long` — `web/app.js:4` — Function 'render' spans 34 lines

## Limitations

Import and security checks are heuristic. This is not a complete type checker, linter, dependency scanner, or security audit.
