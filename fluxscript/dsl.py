"""Declarative Python API. The compiler parses source; it never imports this file."""
from .models import AppSpec, PageSpec, ElementSpec

class App:
    def __init__(self, name: str): self.spec = AppSpec(str(name))
    def add_page(self, page: "Page") -> "App": self.spec.pages.append(page.spec); return self
class Page:
    def __init__(self, path: str = "/", title: str = ""):
        self.spec = PageSpec(str(path), str(title))
    def add(self, element: "Element") -> "Page": self.spec.elements.append(element.spec); return self
class Element:
    def __init__(self, spec: ElementSpec): self.spec = spec
class Text(Element):
    def __init__(self, text: str): super().__init__(ElementSpec("text", str(text)))
class Heading(Element):
    def __init__(self, text: str, level: int = 1):
        level = int(level)
        if level not in (1,2,3,4,5,6): raise ValueError("Heading level must be 1–6")
        super().__init__(ElementSpec("heading", str(text), attributes={"level": level}))
class Button(Element):
    def __init__(self, text: str, action: str): super().__init__(ElementSpec("button", str(text), action=str(action)))
class Input(Element):
    def __init__(self, label: str, name: str, input_type: str = "text"):
        if input_type not in {"text", "email", "number", "password", "date"}: raise ValueError("Unsupported input_type")
        super().__init__(ElementSpec("input", str(label), name=str(name), attributes={"input_type": input_type}))
