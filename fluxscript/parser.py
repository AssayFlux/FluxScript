"""Safe parser for FluxScript's declarative Python subset. Source is never executed."""
import ast
from pathlib import Path
from .dsl import App, Page, Text, Heading, Button, Input
from .models import AppSpec

CONSTRUCTORS = {"App": App, "Page": Page, "Text": Text, "Heading": Heading, "Button": Button, "Input": Input}
MAX_SOURCE_BYTES = 1_000_000
class SourceError(ValueError): pass

def _literal(node):
    try: value = ast.literal_eval(node)
    except (ValueError, TypeError, MemoryError, RecursionError) as exc:
        raise SourceError(f"Only literal arguments are allowed (line {getattr(node, 'lineno', '?')}).") from exc
    if isinstance(value, (str, bytes)) and len(value) > 10_000:
        raise SourceError(f"String/bytes literal is too large (line {getattr(node, 'lineno', '?')}).")
    return value

def _construct(call: ast.Call, line: int):
    if not isinstance(call.func, ast.Name) or call.func.id not in CONSTRUCTORS:
        raise SourceError(f"Only approved constructors are allowed (line {line}).")
    if any(k.arg is None for k in call.keywords): raise SourceError("**kwargs expansion is not supported.")
    ctor = CONSTRUCTORS[call.func.id]
    try:
        return ctor(*[_literal(a) for a in call.args], **{k.arg: _literal(k.value) for k in call.keywords})
    except (TypeError, ValueError, OverflowError) as exc:
        raise SourceError(f"Invalid {call.func.id} at line {line}: {exc}") from exc

def parse_source(source: str) -> AppSpec:
    if not isinstance(source, str): raise TypeError("source must be a string")
    if len(source.encode("utf-8")) > MAX_SOURCE_BYTES: raise SourceError("Source exceeds 1 MB limit.")
    try: tree = ast.parse(source)
    except (SyntaxError, ValueError, RecursionError) as exc:
        if isinstance(exc, SyntaxError): raise SourceError(f"Python syntax error at line {exc.lineno}: {exc.msg}") from exc
        raise SourceError("Source could not be parsed safely.") from exc
    env: dict[str, object] = {}; app: App | None = None
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            if node.level != 0 or node.module != "fluxscript" or any(a.name not in CONSTRUCTORS or a.asname for a in node.names):
                raise SourceError(f"Unsupported import at line {node.lineno}; import only approved names directly from fluxscript.")
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str): continue
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id.startswith("__"): raise SourceError(f"Private-looking names are not allowed (line {node.lineno}).")
            if not isinstance(node.value, ast.Call): raise SourceError(f"Only approved constructor assignments are allowed (line {node.lineno}).")
            obj = _construct(node.value, node.lineno)
            if not isinstance(obj, (App, Page, Text, Heading, Button, Input)): raise SourceError("Unsupported constructor.")
            env[node.targets[0].id] = obj
            if isinstance(obj, App):
                if app is not None: raise SourceError("Define exactly one App instance.")
                app = obj
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if not isinstance(call.func, ast.Attribute) or not isinstance(call.func.value, ast.Name):
                raise SourceError(f"Unsupported expression at line {node.lineno}.")
            receiver = env.get(call.func.value.id)
            if receiver is None: raise SourceError(f"Unknown declarative object {call.func.value.id!r} at line {node.lineno}.")
            if len(call.args) != 1 or call.keywords: raise SourceError(f"Expected exactly one positional argument (line {node.lineno}).")
            arg = call.args[0]
            if isinstance(arg, ast.Name):
                if arg.id not in env: raise SourceError(f"Unknown declarative object {arg.id!r} at line {node.lineno}.")
                argument = env[arg.id]
            elif isinstance(arg, ast.Call): argument = _construct(arg, node.lineno)
            else: raise SourceError(f"Method arguments must be a declared object or approved constructor (line {node.lineno}).")
            if isinstance(receiver, Page) and call.func.attr == "add" and isinstance(argument, (Text, Heading, Button, Input)): receiver.add(argument)
            elif isinstance(receiver, App) and call.func.attr == "add_page" and isinstance(argument, Page): receiver.add_page(argument)
            else: raise SourceError(f"Unsupported method call at line {node.lineno}.")
            continue
        raise SourceError(f"Unsupported statement at line {getattr(node, 'lineno', '?')}; only declarative app definitions are accepted.")
    if app is None: raise SourceError("No App(...) declaration found.")
    issues = app.spec.validate()
    if issues: raise SourceError("Application validation failed:\n- " + "\n- ".join(issues))
    return app.spec

def parse_file(path) -> AppSpec:
    p = Path(path)
    if not p.is_file(): raise SourceError(f"Source file not found: {p}")
    try:
        if p.stat().st_size > MAX_SOURCE_BYTES: raise SourceError("Source exceeds 1 MB limit.")
        return parse_source(p.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc: raise SourceError("Source must be UTF-8 encoded.") from exc
