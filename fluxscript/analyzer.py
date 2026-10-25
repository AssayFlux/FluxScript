"""Read-only source/project analyzer. It never imports or executes analyzed files."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist", ".tox"}
MAX_FILES = 5000
MAX_SOURCE_BYTES = 2_000_000
RISKY_CALLS = {"eval", "exec", "compile", "__import__", "system", "popen", "Popen", "run", "call", "check_call", "check_output", "pickle", "loads"}


def analyze_path(path: str | Path) -> dict:
    root = Path(path).expanduser().resolve()
    if not root.exists(): raise FileNotFoundError(f"Path does not exist: {root}")
    files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file() and not any(part in SKIP_DIRS for part in p.parts))
    if len(files) > MAX_FILES: raise ValueError(f"Analysis limit is {MAX_FILES} files; narrow the input path.")
    report = {"tool": "FluxScript Analyzer", "version": "0.1.0", "root": str(root), "file_count": 0,
              "total_bytes": 0, "files": [], "python_summary": {"files": 0, "functions": [], "classes": [], "imports": [], "syntax_errors": []}, "findings": []}
    summary = report["python_summary"]
    for file in files:
        try: stat = file.stat()
        except OSError as exc:
            report["findings"].append({"severity": "warning", "file": str(file), "message": f"Cannot stat file: {type(exc).__name__}"}); continue
        item = {"path": str(file.relative_to(root) if root.is_dir() else file.name), "extension": file.suffix.lower(), "size_bytes": stat.st_size}
        if stat.st_size > MAX_SOURCE_BYTES:
            item["sha256"] = None
            item["note"] = f"Skipped content analysis: file exceeds {MAX_SOURCE_BYTES} bytes."
            report["findings"].append({"severity": "info", "file": item["path"], "message": item["note"]})
        else:
            try: raw = file.read_bytes()
            except OSError as exc:
                report["findings"].append({"severity": "warning", "file": item["path"], "message": f"Cannot read file: {type(exc).__name__}"}); continue
            item["sha256"] = hashlib.sha256(raw).hexdigest()
            if file.suffix.lower() == ".py":
                summary["files"] += 1
                try:
                    tree = ast.parse(raw.decode("utf-8"), filename=str(file))
                    functions = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                    imports = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import): imports.extend(alias.name for alias in node.names)
                        elif isinstance(node, ast.ImportFrom): imports.append(node.module or "")
                    summary["functions"].extend(f"{item['path']}:{name}" for name in functions)
                    summary["classes"].extend(f"{item['path']}:{name}" for name in classes)
                    summary["imports"].extend(imports)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
                            if name in RISKY_CALLS:
                                report["findings"].append({"severity": "review", "file": item["path"], "line": getattr(node, "lineno", None), "message": f"Review dynamic execution/process/deserialization call: {name}"})
                except (SyntaxError, UnicodeDecodeError) as exc:
                    issue = {"file": item["path"], "line": getattr(exc, "lineno", None), "message": str(exc)}
                    summary["syntax_errors"].append(issue)
                    report["findings"].append({"severity": "error", **issue})
        report["files"].append(item)
        report["total_bytes"] += stat.st_size
    report["file_count"] = len(report["files"])
    summary["imports"] = sorted(set(summary["imports"]))
    report["summary"] = {"errors": sum(1 for f in report["findings"] if f["severity"] == "error"),
                         "review_items": sum(1 for f in report["findings"] if f["severity"] == "review"),
                         "warnings": sum(1 for f in report["findings"] if f["severity"] == "warning")}
    return report


def write_report(report: dict, destination: str | Path) -> Path:
    output = Path(destination).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return output
