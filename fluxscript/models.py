"""Stable, JSON-serializable semantic model shared by FluxScript backends."""
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ElementSpec:
    kind: str
    text: str = ""
    action: str | None = None
    name: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class PageSpec:
    path: str = "/"
    title: str = ""
    elements: list[ElementSpec] = field(default_factory=list)

@dataclass
class AppSpec:
    name: str
    pages: list[PageSpec] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not isinstance(self.name, str) or not self.name.strip():
            issues.append("Application name must be a non-empty string.")
        if len(self.name) > 120:
            issues.append("Application name must be at most 120 characters.")
        if not self.pages:
            issues.append("Application must define at least one page.")
        paths: set[str] = set()
        for page in self.pages:
            if not page.path.startswith("/") or ".." in page.path.split("/") or "\\" in page.path:
                issues.append(f"Page path must be an absolute, normalized URL path: {page.path!r}")
            if page.path in paths:
                issues.append(f"Duplicate page path: {page.path}")
            paths.add(page.path)
            if len(page.title) > 160:
                issues.append(f"Page title for {page.path!r} must be at most 160 characters.")
            for element in page.elements:
                if element.kind not in {"text", "heading", "button", "input"}:
                    issues.append(f"Unsupported element kind: {element.kind!r}")
                if len(element.text) > 10_000:
                    issues.append("Element text exceeds 10000 characters.")
                if element.kind == "button":
                    if not element.action or not element.action.strip(): issues.append(f"Button {element.text!r} has no action name.")
                    elif not element.action.isidentifier(): issues.append(f"Button action must be a valid identifier: {element.action!r}")
                if element.kind == "input":
                    if not element.name or not element.name.isidentifier(): issues.append(f"Input field name must be a valid identifier: {element.name!r}")
                    if element.attributes.get("input_type", "text") not in {"text", "email", "number", "password", "date"}:
                        issues.append(f"Unsupported input type: {element.attributes.get('input_type')!r}")
                if element.kind == "heading" and element.attributes.get("level", 1) not in (1,2,3,4,5,6):
                    issues.append("Heading level must be between 1 and 6.")
        return issues
