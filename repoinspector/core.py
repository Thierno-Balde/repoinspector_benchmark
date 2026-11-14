"""Standard-library static analysis for small Python/JavaScript projects."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

EXCLUDED_DIRS = {".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
PYTHON_SUFFIXES = {".py"}
JAVASCRIPT_SUFFIXES = {".js", ".jsx", ".mjs", ".cjs"}
LONG_FUNCTION_LINES = 30
SEVERITY_WEIGHTS = {"low": 2, "medium": 6, "high": 12, "critical": 20}


def _finding(path: str, line: int, rule: str, severity: str, message: str, **extra: Any) -> dict[str, Any]:
    item = {"path": path, "line": line, "rule": rule, "severity": severity, "message": message}
    item.update(extra)
    return item


def _line_metrics(text: str, language: str) -> dict[str, int]:
    lines = text.splitlines()
    blank = 0
    comments = 0
    in_block = False
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            blank += 1
            continue
        if language == "python":
            if stripped.startswith("#"):
                comments += 1
        else:
            if in_block:
                comments += 1
                if "*/" in stripped:
                    in_block = False
                continue
            if stripped.startswith("//"):
                comments += 1
            elif stripped.startswith("/*") or stripped.startswith("*") or stripped.startswith("*/"):
                comments += 1
                if "/*" in stripped and "*/" not in stripped:
                    in_block = True
    return {"total": len(lines), "code": len(lines) - blank - comments, "blank": blank, "comments": comments}


def _python_functions(tree: ast.AST, path: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    functions: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and getattr(node, "end_lineno", None):
            length = node.end_lineno - node.lineno + 1
            info = {"name": node.name, "line": node.lineno, "end_line": node.end_lineno, "lines": length}
            functions.append(info)
            if length > LONG_FUNCTION_LINES:
                findings.append(_finding(path, node.lineno, "function.too_long", "medium", f"Function '{node.name}' spans {length} lines", symbol=node.name, lines=length))
    return functions, findings


def _python_findings(tree: ast.AST, text: str, path: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    imports: list[tuple[str, int, str]] = []
    imported_nodes: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_nodes.add(id(node))
            for alias in node.names:
                bound = alias.asname or alias.name.split(".")[0]
                imports.append((bound, node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            imported_nodes.add(id(node))
            for alias in node.names:
                if alias.name == "*":
                    continue
                imports.append((alias.asname or alias.name, node.lineno, alias.name))
    used: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Store):
            used.add(node.id)
    for bound, line, original in imports:
        if bound not in used:
            findings.append(_finding(path, line, "python.unused_import", "low", f"Imported name '{original}' appears unused", confidence="heuristic"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            broad = node.type is None or (isinstance(node.type, ast.Name) and node.type.id in {"Exception", "BaseException"})
            empty = not node.body or all(isinstance(stmt, (ast.Pass, ast.Expr)) and (not isinstance(stmt, ast.Expr) or isinstance(stmt.value, ast.Constant) and stmt.value.value is Ellipsis) for stmt in node.body)
            if empty:
                findings.append(_finding(path, node.lineno, "python.empty_except", "medium", "Exception handler is empty or only suppresses the error"))
            if broad:
                findings.append(_finding(path, node.lineno, "python.broad_except", "medium", "Exception handler catches too broadly"))
    security_patterns = [
        (r"\beval\s*\(", "security.dynamic_eval", "high", "Use of eval can execute input as code"),
        (r"\bexec\s*\(", "security.dynamic_exec", "high", "Use of exec can execute input as code"),
        (r"pickle\.loads\s*\(", "security.unsafe_deserialization", "high", "pickle deserialization can execute unsafe payloads"),
        (r"subprocess\.[A-Za-z_]+\s*\([^\n]*shell\s*=\s*True", "security.shell_true", "high", "shell=True needs strict input control"),
    ]
    for pattern, rule, severity, message in security_patterns:
        for match in re.finditer(pattern, text):
            findings.append(_finding(path, text.count("\n", 0, match.start()) + 1, rule, severity, message))
    functions, function_findings = _python_functions(tree, path)
    findings.extend(function_findings)
    return functions, findings


def _js_functions(text: str, path: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    functions: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    starts = list(re.finditer(r"(?:function\s+([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{|(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>\s*\{)", text))
    for match in starts:
        name = match.group(1) or match.group(2) or "anonymous"
        brace = text.find("{", match.start(), match.end())
        depth = 0
        end = None
        for index in range(brace, len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    end = index
                    break
        if end is None:
            continue
        start_line = text.count("\n", 0, match.start()) + 1
        end_line = text.count("\n", 0, end) + 1
        length = end_line - start_line + 1
        info = {"name": name, "line": start_line, "end_line": end_line, "lines": length}
        functions.append(info)
        if length > LONG_FUNCTION_LINES:
            findings.append(_finding(path, start_line, "function.too_long", "medium", f"Function '{name}' spans {length} lines", symbol=name, lines=length))
    return functions, findings


def _javascript_findings(text: str, path: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    import_names: list[tuple[str, int, str]] = []
    import_lines: list[str] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped.startswith("import "):
            continue
        import_lines.append(line)
        match = re.match(r"import\s+(.+?)\s+from\s+['\"]", stripped)
        if not match:
            match = re.match(r"import\s+['\"]", stripped)
            continue
        clause = match.group(1).strip()
        if clause.startswith("{") and clause.endswith("}"):
            for part in clause[1:-1].split(","):
                part = part.strip()
                if part:
                    pieces = re.split(r"\s+as\s+", part)
                    import_names.append((pieces[-1].strip(), line_no, part))
        elif clause.startswith("*"):
            alias = re.search(r"\bas\s+([A-Za-z_$][\w$]*)", clause)
            if alias:
                import_names.append((alias.group(1), line_no, clause))
        else:
            default = clause.split(",", 1)[0].strip()
            if re.match(r"^[A-Za-z_$][\w$]*$", default):
                import_names.append((default, line_no, default))
    non_import = "\n".join(line for line in text.splitlines() if not line.strip().startswith("import "))
    for name, line, original in import_names:
        if not re.search(rf"\b{re.escape(name)}\b", non_import):
            findings.append(_finding(path, line, "javascript.unused_import", "low", f"Imported name '{original}' appears unused", confidence="heuristic"))
    for pattern, rule, severity, message in [
        (r"\beval\s*\(", "security.dynamic_eval", "high", "Use of eval can execute input as code"),
        (r"\bnew\s+Function\s*\(", "security.dynamic_function", "high", "new Function can execute input as code"),
        (r"\.innerHTML\s*=", "security.dom_injection", "medium", "innerHTML assignment can introduce DOM injection"),
        (r"document\.write\s*\(", "security.document_write", "medium", "document.write can introduce unsafe markup"),
    ]:
        for match in re.finditer(pattern, text):
            findings.append(_finding(path, text.count("\n", 0, match.start()) + 1, rule, severity, message))
    functions, function_findings = _js_functions(text, path)
    findings.extend(function_findings)
    return functions, findings


def analyze_path(root: str | Path) -> dict[str, Any]:
    root_path = Path(root)
    if not root_path.exists():
        raise FileNotFoundError(f"path does not exist: {root_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"path is not a directory: {root_path}")
    files: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for path in sorted(root_path.rglob("*")):
        if not path.is_file() or any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        suffix = path.suffix.lower()
        language = "python" if suffix in PYTHON_SUFFIXES else "javascript" if suffix in JAVASCRIPT_SUFFIXES else None
        if language is None:
            continue
        rel = path.relative_to(root_path).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            findings.append(_finding(rel, 1, "file.read_error", "high", f"Could not read source file: {exc}"))
            continue
        metrics = _line_metrics(text, language)
        file_item: dict[str, Any] = {"path": rel, "language": language, "lines": metrics}
        try:
            if language == "python":
                tree = ast.parse(text, filename=rel)
                functions, local_findings = _python_findings(tree, text, rel)
            else:
                functions, local_findings = _javascript_findings(text, rel)
            file_item["functions"] = functions
            findings.extend(local_findings)
        except SyntaxError as exc:
            file_item["functions"] = []
            findings.append(_finding(rel, exc.lineno or 1, "parse.syntax_error", "high", f"Could not parse source: {exc.msg}"))
        files.append(file_item)
    severity_counts = {severity: sum(1 for item in findings if item["severity"] == severity) for severity in SEVERITY_WEIGHTS}
    penalty = sum(SEVERITY_WEIGHTS[item["severity"]] for item in findings)
    totals = {key: sum(item["lines"][key] for item in files) for key in ("total", "code", "blank", "comments")}
    summary = {
        "files": {"total": len(files), "python": sum(item["language"] == "python" for item in files), "javascript": sum(item["language"] == "javascript" for item in files)},
        "lines": totals,
        "findings": len(findings),
        "findings_by_severity": severity_counts,
        "quality_score": max(0, min(100, 100 - penalty)),
        "score_method": "100 minus 2/6/12/20 points for low/medium/high/critical findings, bounded to 0..100; indicative only.",
    }
    return {"tool": "RepoInspector", "version": "0.1.0", "root": str(root_path), "summary": summary, "files": files, "findings": findings}


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# RepoInspector report",
        "",
        f"- Quality score: **{summary['quality_score']}/100** (indicative)",
        f"- Files: {summary['files']['total']} ({summary['files']['python']} Python, {summary['files']['javascript']} JavaScript)",
        f"- Lines: {summary['lines']['total']} total, {summary['lines']['code']} code, {summary['lines']['comments']} comments, {summary['lines']['blank']} blank",
        f"- Findings: {summary['findings']}",
        "",
        "## Scoring method",
        "",
        summary["score_method"],
        "",
        "## Findings",
        "",
    ]
    if not report["findings"]:
        lines.append("No findings.")
    else:
        for item in report["findings"]:
            confidence = f"; confidence: {item['confidence']}" if "confidence" in item else ""
            lines.append(f"- **{item['severity']}** `{item['rule']}` — `{item['path']}:{item['line']}` — {item['message']}{confidence}")
    lines.extend(["", "## Limitations", "", "Import and security checks are heuristic. This is not a complete type checker, linter, dependency scanner, or security audit.", ""])
    return "\n".join(lines)


def write_reports(report: dict[str, Any], output: str | Path) -> tuple[Path, Path]:
    prefix = Path(output)
    json_path = prefix.with_suffix(".json")
    markdown_path = prefix.with_suffix(".md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect Python and JavaScript source quality.")
    parser.add_argument("--path", required=True, help="Project directory to inspect")
    parser.add_argument("--output", default="repoinspector-report", help="Output prefix for .json and .md reports")
    args = parser.parse_args(argv)
    try:
        report = analyze_path(args.path)
        json_path, markdown_path = write_reports(report, args.output)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    print(f"Quality score: {report['summary']['quality_score']}/100")
    return 0
