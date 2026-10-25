"""Explicit, bounded external CLI invocation helpers. Never uses a shell."""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path

class ExternalToolError(RuntimeError): pass

def run_tool(executable: str, args: list[str], *, cwd: str | Path | None = None,
             timeout: float = 30.0, output_limit: int = 1_000_000) -> dict:
    """Run an explicitly named installed tool; callers must obtain user approval first.

    The function does not interpret shell syntax. It does not download or install tools.
    Use only with trusted executable names/paths and reviewed arguments.
    """
    resolved = shutil.which(executable)
    if not resolved: raise ExternalToolError(f"Required external executable is not installed: {executable}")
    if not isinstance(args, list) or any(not isinstance(x, str) for x in args):
        raise TypeError("args must be a list of strings")
    try:
        completed = subprocess.run([resolved, *args], cwd=str(cwd) if cwd else None,
                                   capture_output=True, text=True, timeout=max(1.0, min(timeout, 300.0)),
                                   shell=False, check=False)
    except subprocess.TimeoutExpired as exc:
        raise ExternalToolError(f"External tool timed out after {exc.timeout} seconds") from exc
    stdout, stderr = completed.stdout or "", completed.stderr or ""
    if len(stdout) > output_limit: stdout = stdout[:output_limit] + "\n[output truncated]"
    if len(stderr) > output_limit: stderr = stderr[:output_limit] + "\n[output truncated]"
    return {"command": resolved, "returncode": completed.returncode, "stdout": stdout, "stderr": stderr}
