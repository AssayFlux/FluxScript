"""Explicit, bounded client for an operator-configured FluxScript-compatible execution API."""
from __future__ import annotations
import ipaddress, json, os
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

class ExecutionServiceError(RuntimeError): pass
class ExecutionServiceClient:
    def __init__(self, base_url: str | None = None, token: str | None = None, timeout: float = 10.0):
        self.base_url = (base_url or os.environ.get("FLUXSCRIPT_SERVICE_URL", "http://127.0.0.1:2000/api/v2")).rstrip("/")
        self.token = token if token is not None else os.environ.get("FLUXSCRIPT_SERVICE_TOKEN")
        self.timeout = max(1.0, min(float(timeout), 60.0))
        parts = urlsplit(self.base_url)
        if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
            raise ValueError("Execution service URL must be an HTTP(S) base URL without credentials, query, or fragment")
        if parts.scheme == "http":
            host = parts.hostname.lower().rstrip(".")
            local = host == "localhost"
            try: local = local or ipaddress.ip_address(host).is_loopback
            except ValueError: pass
            if not local: raise ValueError("Non-local execution-service endpoints must use HTTPS")
    def _request(self, path: str, payload: dict | None = None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Accept": "application/json", "User-Agent": "FluxScript/0.1.0"}
        if data is not None: headers["Content-Type"] = "application/json"
        if self.token: headers["Authorization"] = f"Bearer {self.token}"
        req = Request(f"{self.base_url}/{path.lstrip('/')}", data=data, headers=headers, method="POST" if data is not None else "GET")
        try:
            with urlopen(req, timeout=self.timeout) as response:
                raw = response.read(2_000_001)
                if len(raw) > 2_000_000: raise ExecutionServiceError("Execution service response exceeded 2 MB limit")
                result = json.loads(raw.decode("utf-8"))
        except HTTPError as exc: raise ExecutionServiceError(f"Execution service returned HTTP {exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc: raise ExecutionServiceError(f"Could not reach configured execution service ({exc.__class__.__name__})") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc: raise ExecutionServiceError("Execution service returned invalid JSON") from exc
        return result
    def runtimes(self) -> list[dict]:
        result = self._request("runtimes")
        if not isinstance(result, list) or any(not isinstance(x, dict) for x in result): raise ExecutionServiceError("Unexpected runtimes response schema")
        return result
    def execute(self, language: str, version: str, code: str, *, stdin: str = "", args: list[str] | None = None, compile_timeout_ms: int = 10_000, run_timeout_ms: int = 3_000) -> dict:
        if not isinstance(language, str) or not language.strip() or not isinstance(version, str) or not version.strip(): raise ValueError("language and version are required")
        if not isinstance(code, str) or len(code.encode("utf-8")) > 1_000_000: raise ValueError("Source must be text no larger than 1 MB")
        if not isinstance(stdin, str) or len(stdin.encode("utf-8")) > 100_000: raise ValueError("stdin must be text no larger than 100 KB")
        if args is not None and (not isinstance(args, list) or any(not isinstance(x, str) for x in args)): raise ValueError("args must be a list of strings")
        payload = {"language": language, "version": version, "files": [{"name": "main", "content": code}], "stdin": stdin, "args": list(args or []), "compile_timeout": max(100, min(int(compile_timeout_ms), 30_000)), "run_timeout": max(100, min(int(run_timeout_ms), 10_000)), "compile_memory_limit": 128_000_000, "run_memory_limit": 128_000_000}
        result = self._request("execute", payload)
        if not isinstance(result, dict) or not isinstance(result.get("run"), dict): raise ExecutionServiceError("Unexpected execute response schema")
        return result
