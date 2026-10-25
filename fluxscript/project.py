"""Project export and storage helpers."""
from __future__ import annotations
import json
import os
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from .backends import BACKENDS
from .parser import parse_file, SourceError


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip(".-_").lower()
    return slug[:64] or "fluxscript-project"


def default_storage() -> Path:
    """Choose shared Android storage when mounted, otherwise a user-home directory."""
    android_storage = Path("/storage/emulated/0")
    if android_storage.is_dir() and os.access(android_storage, os.W_OK):
        return android_storage / "FluxScriptProjects"
    return Path.home() / "FluxScriptProjects"


def generate_project(source: Path, target: str, storage: Path, *, install_dependencies: bool = True) -> tuple[Path, Path, list[Path]]:
    """Generate a self-contained project directory and ZIP archive under storage."""
    if target not in (*BACKENDS.keys(), "all"):
        raise ValueError(f"Unsupported target {target!r}; choose {', '.join((*BACKENDS.keys(), 'all'))}.")
    spec = parse_file(source)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    name = safe_slug(spec.name)
    root = storage.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    project_dir = root / f"{name}-{target}-{stamp}"
    project_dir.mkdir(parents=False, exist_ok=False)
    generated: list[Path] = []
    selected = list(BACKENDS) if target == "all" else [target]
    try:
        for backend_name in selected:
            out = project_dir / backend_name if target == "all" else project_dir
            generated.extend(BACKENDS[backend_name](spec, out))
            if backend_name == "web":
                from bs4 import BeautifulSoup
                soup = BeautifulSoup((out / "index.html").read_text(encoding="utf-8"), "html.parser")
                if soup.title is None or soup.main is None or not soup.find_all("section", attrs={"data-route": True}):
                    raise RuntimeError("Generated website failed structural HTML validation.")
            elif backend_name == "android":
                from defusedxml import ElementTree
                ElementTree.parse(str(out / "app/src/main/AndroidManifest.xml"))
            elif backend_name == "ios":
                swift = (out / "GeneratedApp.swift").read_text(encoding="utf-8")
                if "@main" not in swift or "struct ContentView" not in swift:
                    raise RuntimeError("Generated iOS source failed entry-point validation.")
            elif backend_name == "cli":
                import ast
                ast.parse((out / "app_cli.py").read_text(encoding="utf-8"), filename="app_cli.py")
        manifest = {
            "name": spec.name, "version": "0.1.0", "source_file": Path(source).name,
            "targets": selected, "generated_at": datetime.now().astimezone().isoformat(),
            "files": sorted(str(p.relative_to(project_dir)) for p in generated),
        }
        manifest_path = project_dir / "fluxscript-project.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        generated.append(manifest_path)
        archive = root / f"{project_dir.name}.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for file in sorted(project_dir.rglob("*")):
                if file.is_file(): zf.write(file, file.relative_to(project_dir.parent))
        return project_dir, archive, generated
    except Exception:
        shutil.rmtree(project_dir, ignore_errors=True)
        raise
