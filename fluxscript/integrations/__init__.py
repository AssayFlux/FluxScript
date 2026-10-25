"""FluxScript's built-in capability registry."""
from importlib.util import find_spec
from shutil import which

_CAPABILITIES = (
    {"name": "web-builder", "purpose": "Generate HTML, CSS, JavaScript and TypeScript", "kind": "built-in", "module": None, "command": None},
    {"name": "android-builder", "purpose": "Generate Kotlin and Gradle project source", "kind": "built-in", "module": None, "command": None},
    {"name": "ios-builder", "purpose": "Generate SwiftUI project source", "kind": "built-in", "module": None, "command": None},
    {"name": "cli-builder", "purpose": "Generate a standalone argparse-based CLI", "kind": "built-in", "module": None, "command": None},
    {"name": "source-analyzer", "purpose": "Read-only source inventory and static review", "kind": "built-in", "module": None, "command": None},
    {"name": "remote-execution", "purpose": "Call a configured remote source execution API", "kind": "optional-service", "module": None, "command": None},
    {"name": "node-toolchain", "purpose": "Optional JavaScript and TypeScript validation", "kind": "local-toolchain", "module": None, "command": "node"},
    {"name": "android-toolchain", "purpose": "Optional Android native compilation", "kind": "local-toolchain", "module": None, "command": "gradle"},
    {"name": "ios-toolchain", "purpose": "Optional Apple-platform compilation (macOS only)", "kind": "local-toolchain", "module": None, "command": "xcodebuild"},
)

def status() -> list[dict[str, str | bool]]:
    result = []
    for item in _CAPABILITIES:
        row = dict(item)
        row["available"] = True if item["kind"] == "built-in" else bool(item["command"] and which(item["command"]))
        result.append(row)
    return result
