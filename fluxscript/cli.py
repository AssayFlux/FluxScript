"""FluxScript command line interface."""
from __future__ import annotations
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from . import __version__
from .backends import BACKENDS
from .dependencies import ensure_target_dependencies
from .analyzer import analyze_path, write_report
from .integrations import status as integration_status
from .integrations.execution_service import ExecutionServiceClient, ExecutionServiceError
from .parser import parse_file, SourceError
from .project import default_storage, generate_project

EXAMPLE = '''"""Describe an application using FluxScript's safe declarative Python API."""
from fluxscript import App, Page, Heading, Text, Button, Input

app = App("Research Manager")
home = Page("/", title="Research Manager")
home.add(Heading("Welcome to Research Manager"))
home.add(Text("Describe your interface once and generate a project for a target platform."))
home.add(Input("Project name", name="project_name"))
home.add(Button("Save project", action="save_project"))
app.add_page(home)
'''

GUIDE = r'''FluxScript 0.1.0 — COMMAND GUIDE
================================

GET STARTED
  python -m pip install .             (run from the extracted source directory)
  # After PyPI publication: python -m pip install --upgrade FluxScript
  fluxscript --version
  fluxscript new my_app
  cd my_app
  fluxscript check app.py

BUILDERS (builder commands install the latest required Python validation helper)
  fluxscript website app.py               (clean alias; website-builder also works)
  fluxscript website-builder app.py --out build/site
  fluxscript android app.py               (clean alias; android-builder also works)
  fluxscript ios app.py                   (clean alias; ios-builder also works)
  fluxscript cli app.py                   (clean alias; cli-builder also works)
  fluxscript build app.py --target all --out build/all
  Add --no-install-deps to prevent automatic pip installation.

GENERATE PROJECT (creates a directory AND ZIP in storage)
  fluxscript generateproject --source app.py --target web  (generate-project also works)
  fluxscript generate-project --source app.py --target android --storage ~/FluxScriptProjects
  fluxscript generate-project --source app.py --target all
  Default storage: /storage/emulated/0/FluxScriptProjects when writable, otherwise
  ~/FluxScriptProjects. Both the generated directory and a ZIP archive are saved there.

PROJECT UTILITIES
  fluxscript new [directory]      Create a starter source project
  fluxscript check [source.py]    Validate source without executing it
  fluxscript targets              List supported source generators
  fluxscript doctor               Detect local native/toolchain executables
  fluxscript device               Detect current runtime device/OS type
  fluxscript developer            Show project developer name
  fluxscript integrations         Show built-in capabilities and optional toolchains
  fluxscript analyze ./source     Inspect source files without executing them
  fluxscript analyze ./source --out report.json
  fluxscript review ./source      Alias for the read-only analyzer
  fluxscript guide                Print this full command guide

REMOTE EXECUTION SERVICE
  fluxscript service status
  export FLUXSCRIPT_SERVICE_URL='http://127.0.0.1:2000/api/v2'
  export FLUXSCRIPT_SERVICE_TOKEN='your-token-if-required'
  fluxscript service runtimes
  fluxscript service run python 3.12 main.py
  fluxscript service run javascript 20.11.1 app.js --stdin-file input.txt
  Remote non-local endpoints must use HTTPS. The service must be separately deployed;
  FluxScript never silently executes submitted code on your own machine.

NOTES
  The source format is a restricted declarative Python subset, not arbitrary Python.
  Android compilation needs a JDK, Android SDK and compatible Gradle environment.
  iOS compilation/signing needs macOS and Xcode. pip cannot install those toolchains.
  Generated buttons emit action requests; connect real business logic and APIs yourself.
'''

def _new(path: Path) -> int:
    path = path.expanduser()
    if path.exists() and not path.is_dir():
        print(f"error: not a directory: {path}", file=sys.stderr); return 2
    path.mkdir(parents=True, exist_ok=True)
    source = path / "app.py"
    if source.exists(): print(f"error: refusing to overwrite existing file: {source}", file=sys.stderr); return 2
    source.write_text(EXAMPLE, encoding="utf-8")
    (path / "fluxscript.toml").write_text('[project]\nname = "Research Manager"\nsource = "app.py"\nversion = "0.1.0"\n\n[targets]\ndefault = ["web"]\n', encoding="utf-8")
    print(f"Created project at {path}\nNext: cd {path} && fluxscript check app.py && fluxscript website-builder app.py")
    return 0

def _validate_generated(target: str, output: Path) -> None:
    if target == "web":
        from bs4 import BeautifulSoup
        html = (output / "index.html").read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")
        if soup.title is None or soup.main is None or not soup.find_all("section", attrs={"data-route": True}):
            raise RuntimeError("Generated web output failed structural HTML validation.")
        if not (output / "styles.css").is_file() or not (output / "app.js").is_file():
            raise RuntimeError("Generated web output is missing CSS or JavaScript.")
    elif target == "android":
        from defusedxml import ElementTree
        manifest = output / "app/src/main/AndroidManifest.xml"
        ElementTree.parse(str(manifest))
        if not (output / "app/src/main/java/dev/fluxscript/generated/MainActivity.kt").is_file():
            raise RuntimeError("Generated Android output is missing its Kotlin entry point.")
    elif target == "ios":
        source = output / "GeneratedApp.swift"
        if not source.is_file() or "@main" not in source.read_text(encoding="utf-8"):
            raise RuntimeError("Generated iOS output is missing its SwiftUI entry point.")
    elif target == "cli":
        import ast
        source = output / "app_cli.py"
        ast.parse(source.read_text(encoding="utf-8"), filename=str(source))

def _builder(source: Path, target: str, out: Path, *, no_install_deps: bool = False) -> int:
    try:
        dependencies = ensure_target_dependencies(target, no_install=no_install_deps)
        spec = parse_file(source)
        files = BACKENDS[target](spec, out.expanduser())
        _validate_generated(target, out.expanduser())
        print(f"FluxScript {target} builder: validated {len(files)} generated files in {out}")
        print("Python validation helpers: " + (", ".join(dependencies) if dependencies else "none required"))
        if target == "android": print("Native build requirement: JDK + Android SDK + compatible Gradle/Android Gradle Plugin.")
        if target == "ios": print("Native build requirement: macOS + Xcode; this command generates source, not an IPA.")
        return 0
    except (SourceError, OSError, ValueError, RuntimeError, ImportError) as exc:
        print(f"builder error: {exc}", file=sys.stderr); return 2

def _build(source: Path, target: str, out: Path, no_install_deps: bool = False) -> int:
    if target == "all":
        code = 0
        for name in BACKENDS:
            result = _builder(source, name, out / name, no_install_deps=no_install_deps)
            if result: code = result
        return code
    return _builder(source, target, out, no_install_deps=no_install_deps)

def _service(args: argparse.Namespace) -> int:
    try:
        client = ExecutionServiceClient(base_url=args.url, token=args.token, timeout=args.timeout)
        if args.service_command == "status":
            endpoint = args.url or os.environ.get("FLUXSCRIPT_SERVICE_URL")
            print(json.dumps({"service": "FluxScript remote execution API", "base_url": client.base_url,
                "endpoint_configured": bool(endpoint), "using_default_endpoint": not bool(endpoint),
                "token_configured": bool(client.token), "network_checked": False}, indent=2))
            return 0
        if args.service_command == "runtimes":
            print(json.dumps(client.runtimes(), indent=2, ensure_ascii=False)); return 0
        if args.service_command == "run":
            code = Path(args.file).read_text(encoding="utf-8")
            stdin = Path(args.stdin_file).read_text(encoding="utf-8") if args.stdin_file else (args.stdin or "")
            result = client.execute(args.language, args.runtime_version, code, stdin=stdin, args=args.arg or [], run_timeout_ms=args.run_timeout)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            run = result.get("run", {})
            return 0 if run.get("code", 0) == 0 and not run.get("signal") else 1
    except (ExecutionServiceError, OSError, ValueError) as exc:
        print(f"service error: {exc}", file=sys.stderr); return 2
    return 2

def _device_info() -> dict[str, object]:
    """Return best-effort host/device details without installing extra packages."""
    system = platform.system() or os.name
    release = platform.release()
    machine = platform.machine()
    env = os.environ
    if env.get("ANDROID_ARGUMENT") or env.get("ANDROID_ROOT") or "ANDROID_DATA" in env:
        device_type = "android"
    elif sys.platform == "ios":
        device_type = "ios"
    elif system == "Windows":
        device_type = "windows_pc"
    elif system == "Darwin":
        device_type = "mac"
    elif system == "Linux":
        device_type = "linux_device"
    else:
        device_type = "unknown"
    return {
        "device_name": platform.node() or "unknown",
        "device_type": device_type,
        "system": system,
        "system_release": release,
        "machine_architecture": machine,
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "termux": bool(env.get("TERMUX_VERSION")),
        "note": "Best-effort runtime detection; some phones/tablets report the terminal or host name rather than the hardware model.",
    }

def _doctor() -> int:
    checks = {"device": _device_info(), "python_version": sys.version.split()[0], "python_supported": sys.version_info >= (3, 10),
        "node": shutil.which("node"), "npm": shutil.which("npm"), "java": shutil.which("java"),
        "gradle": shutil.which("gradle"), "xcodebuild": shutil.which("xcodebuild"),
        "android_home": os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")}
    print(json.dumps(checks, indent=2)); return 0 if checks["python_supported"] else 1

def main(argv: list[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    # Friendly command names omit punctuation. Legacy hyphenated forms remain accepted.
    aliases = {
        "new": "new", "check": "check", "build": "build", "guide": "guide",
        "targets": "targets", "doctor": "doctor", "device": "device", "detectdevice": "device",
        "developer": "developer", "author": "developer", "integrations": "integrations",
        "analyze": "analyze", "review": "review", "service": "service",
        "website": "website-builder", "web": "website-builder", "websitebuilder": "website-builder",
        "webbuilder": "website-builder", "android": "android-builder", "androidbuilder": "android-builder",
        "ios": "ios-builder", "iosbuilder": "ios-builder", "cli": "cli-builder", "clibuilder": "cli-builder",
        "generate": "generate-project", "generateproject": "generate-project",
    }
    if raw_args:
        first = raw_args[0].lower()
        normalized = first.replace("-", "").replace("_", "")
        # Also accept familiar two-word command forms such as "website builder".
        if len(raw_args) >= 2 and (first + " " + raw_args[1].lower()) in {
            "website builder", "web builder", "android builder", "ios builder", "cli builder", "generate project"
        }:
            phrase = first + " " + raw_args[1].lower()
            target = {"website builder": "website-builder", "web builder": "website-builder",
                      "android builder": "android-builder", "ios builder": "ios-builder",
                      "cli builder": "cli-builder", "generate project": "generate-project"}[phrase]
            raw_args[:2] = [target]
        elif normalized in aliases:
            raw_args[0] = aliases[normalized]
    parser = argparse.ArgumentParser(prog="fluxscript", description="FluxScript — a Python-first multi-target project generator")
    parser.add_argument("--version", action="version", version=f"FluxScript {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    newp = sub.add_parser("new", help="create a starter project"); newp.add_argument("path", nargs="?", default=".")
    check = sub.add_parser("check", help="validate declarative source without executing it"); check.add_argument("source", nargs="?", default="app.py")
    build = sub.add_parser("build", help="build one or all generated source targets"); build.add_argument("source", nargs="?", default="app.py"); build.add_argument("--target", choices=["web", "android", "ios", "cli", "all"], default="web"); build.add_argument("--out", default="build"); build.add_argument("--no-install-deps", "--noinstalldeps", dest="no_install_deps", action="store_true")
    for command, target, description in [
        ("website-builder", "web", "generate and validate a website project"),
        ("android-builder", "android", "generate and validate an Android project"),
        ("ios-builder", "ios", "generate and validate an iOS source project"),
        ("cli-builder", "cli", "generate a standalone command-line application"),
    ]:
        bp = sub.add_parser(command, help=description); bp.add_argument("source", nargs="?", default="app.py"); bp.add_argument("--out", default=f"build/{target}"); bp.add_argument("--no-install-deps", "--noinstalldeps", dest="no_install_deps", action="store_true"); bp.set_defaults(builder_target=target)
    analyze = sub.add_parser("analyze", help="read-only source/project analysis; never executes analyzed files"); analyze.add_argument("path", nargs="?", default="."); analyze.add_argument("--out", default=None, help="write JSON report to this path")
    review = sub.add_parser("review", help="alias for the read-only source/project analyzer"); review.add_argument("path", nargs="?", default="."); review.add_argument("--out", default=None, help="write JSON report to this path")
    gp = sub.add_parser("generate-project", help="generate project files and export a ZIP into storage")
    gp.add_argument("--source", default="app.py"); gp.add_argument("--target", choices=["web", "android", "ios", "cli", "all"], default="web"); gp.add_argument("--storage", default=None, help="output storage directory (default: shared Android storage or ~/FluxScriptProjects)"); gp.add_argument("--no-install-deps", "--noinstalldeps", dest="no_install_deps", action="store_true")
    sub.add_parser("guide", help="print all FluxScript commands and usage examples")
    sub.add_parser("device", help="detect the current runtime device/operating-system type")
    sub.add_parser("developer", help="show FluxScript developer/author information")
    sub.add_parser("integrations", help="show built-in capabilities and detected toolchains")
    sub.add_parser("targets", help="list available generation targets")
    sub.add_parser("doctor", help="check local development toolchains")
    service = sub.add_parser("service", help="call a configured remote execution service")
    svc = service.add_subparsers(dest="service_command", required=True)
    for name, help_text in [("status", "show local service configuration"), ("runtimes", "fetch available remote runtimes")]:
        sp = svc.add_parser(name, help=help_text); sp.add_argument("--url", default=None); sp.add_argument("--token", default=None); sp.add_argument("--timeout", type=float, default=10.0)
    run = svc.add_parser("run", help="submit source to the remote execution service"); run.add_argument("language"); run.add_argument("runtime_version"); run.add_argument("file"); run.add_argument("--stdin", default=None); run.add_argument("--stdin-file"); run.add_argument("--arg", action="append", default=[]); run.add_argument("--run-timeout", type=int, default=3000); run.add_argument("--url", default=None); run.add_argument("--token", default=None); run.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args(raw_args)
    if args.command == "new": return _new(Path(args.path))
    if args.command == "guide": print(GUIDE); return 0
    if args.command == "device": print(json.dumps(_device_info(), indent=2)); return 0
    if args.command == "developer": print(json.dumps({"name": "Md Safarujjaman", "project": "FluxScript", "version": __version__}, indent=2)); return 0
    if args.command == "integrations": print(json.dumps(integration_status(), indent=2)); return 0
    if args.command == "targets":
        print(json.dumps({"web": {"description": "HTML/CSS/JavaScript/TypeScript", "validation": "HTML structure", "native_toolchain": "browser; Node.js optional"}, "android": {"description": "Kotlin/Gradle project", "validation": "XML manifest structure", "native_toolchain": "JDK + Android SDK + Gradle"}, "ios": {"description": "SwiftUI source project", "validation": "SwiftUI entry-point checks", "native_toolchain": "macOS + Xcode"}, "cli": {"description": "Python argparse command-line project", "validation": "Python syntax parsing", "native_toolchain": "Python 3.10+"}}, indent=2)); return 0
    if args.command == "doctor": return _doctor()
    if args.command == "service": return _service(args)
    if args.command == "check":
        try:
            spec = parse_file(args.source); print(f"OK: {spec.name} ({len(spec.pages)} page(s)); source parsed without executing it."); return 0
        except (SourceError, OSError) as exc: print(f"error: {exc}", file=sys.stderr); return 2
    if args.command in {"analyze", "review"}:
        try:
            report = analyze_path(args.path)
            if args.out:
                destination = write_report(report, args.out)
                print(f"Analysis report written to {destination}")
                print(json.dumps(report["summary"], indent=2))
            else:
                print(json.dumps(report, indent=2, ensure_ascii=False))
            return 1 if report["summary"]["errors"] else 0
        except (OSError, ValueError) as exc:
            print(f"analysis error: {exc}", file=sys.stderr); return 2
    if args.command == "build": return _build(Path(args.source), args.target, Path(args.out), args.no_install_deps)
    if args.command in {"website-builder", "android-builder", "ios-builder", "cli-builder"}:
        return _builder(Path(args.source), args.builder_target, Path(args.out), no_install_deps=args.no_install_deps)
    if args.command == "generate-project":
        try:
            storage = Path(args.storage).expanduser() if args.storage else default_storage()
            for target in (["web", "android", "ios", "cli"] if args.target == "all" else [args.target]):
                ensure_target_dependencies(target, no_install=args.no_install_deps)
            directory, archive, files = generate_project(Path(args.source), args.target, storage)
            print(f"Project directory: {directory}\nProject ZIP: {archive}\nGenerated files: {len(files)}")
            return 0
        except (SourceError, OSError, ValueError, RuntimeError, ImportError) as exc:
            print(f"project generation error: {exc}", file=sys.stderr); return 2
    return 2

if __name__ == "__main__": raise SystemExit(main())
