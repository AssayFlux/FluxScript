"""Safe, on-demand management of FluxScript's build-time helper packages.

FluxScript's parser accepts a restricted declarative format and does not execute
arbitrary application imports, so it intentionally does not guess or install
third-party runtime dependencies for user applications. This module manages only
packages used by FluxScript itself to validate generated output.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Dependency:
    distribution: str
    module: str
    purpose: str


# Only third-party packages genuinely used by the generated-output validators.
# iOS and CLI validators use the Python standard library and need no pip package.
TARGET_DEPENDENCIES: dict[str, tuple[Dependency, ...]] = {
    "web": (Dependency("beautifulsoup4", "bs4", "validate generated HTML structure"),),
    "android": (Dependency("defusedxml", "defusedxml", "safely parse generated Android XML"),),
    "ios": (),
    "cli": (),
}


def _is_importable(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError, AttributeError):
        return False


def ensure_target_dependencies(
    target: str,
    *,
    no_install: bool = False,
    upgrade: bool = True,
    extra_dependencies: Iterable[Dependency] = (),
) -> list[str]:
    """Ensure the selected target's validator packages are available.

    By default, missing packages are installed and already-present packages are
    upgraded when a target builder is invoked. Set ``no_install`` to require all
    packages to be preinstalled. ``upgrade=False`` installs missing packages but
    leaves existing installations unchanged. All pip invocations use the active
    interpreter, disable pip's version-check notice, and fail with an actionable
    error rather than silently continuing.
    """
    if target not in TARGET_DEPENDENCIES:
        raise ValueError(f"Unknown target: {target}")

    dependencies = (*TARGET_DEPENDENCIES[target], *tuple(extra_dependencies))
    ensured: list[str] = []
    for dep in dependencies:
        installed = _is_importable(dep.module)
        if no_install:
            if not installed:
                raise RuntimeError(
                    f"Missing dependency {dep.distribution!r} ({dep.purpose}). "
                    "Install it with 'python -m pip install " + dep.distribution +
                    "' or rerun without --no-install-deps."
                )
            ensured.append(dep.distribution)
            continue

        if installed and not upgrade:
            ensured.append(dep.distribution)
            continue

        action = "upgrade" if installed else "install"
        print(f"FluxScript: {action} {dep.distribution} ({dep.purpose})...", flush=True)
        command = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check"]
        if upgrade and installed:
            command.append("--upgrade")
        command.append(dep.distribution)
        try:
            subprocess.run(command, check=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise RuntimeError(
                f"Could not {action} {dep.distribution}. Check internet access and pip permissions. "
                f"If it is already installed, rerun with --no-install-deps to skip pip."
            ) from exc
        if not _is_importable(dep.module):
            raise RuntimeError(
                f"pip reported success, but module {dep.module!r} is still not importable."
            )
        ensured.append(dep.distribution)
    return ensured
