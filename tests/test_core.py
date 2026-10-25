import contextlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from fluxscript import __version__
from fluxscript.parser import parse_source, parse_file, SourceError
from fluxscript.backends import BACKENDS
from fluxscript.dependencies import ensure_target_dependencies
from fluxscript.integrations.execution_service import ExecutionServiceClient, ExecutionServiceError
from fluxscript.project import generate_project, default_storage
from fluxscript.analyzer import analyze_path, write_report

VALID = '''from fluxscript import App, Page, Heading, Text, Button, Input
app = App("Test App")
home = Page("/", title="Home")
home.add(Heading("Hello", level=2))
home.add(Text("Welcome"))
home.add(Input("Email", name="email", input_type="email"))
home.add(Button("Submit", action="submit_form"))
app.add_page(home)
settings = Page("/settings", title="Settings")
settings.add(Text("Configuration"))
app.add_page(settings)
'''

class FluxScriptTests(unittest.TestCase):
    def test_version(self): self.assertEqual(__version__, "0.1.0")
    def test_parse_declarative_source(self):
        spec = parse_source(VALID)
        self.assertEqual(spec.name, "Test App"); self.assertEqual(len(spec.pages), 2)
        self.assertEqual(spec.pages[0].elements[2].name, "email")
    def test_rejects_imports_and_execution(self):
        for source in ["import os\n", "from fluxscript import App\napp=App('x')\nopen('/tmp/nope','w')", "from fluxscript import App as X\n"]:
            with self.subTest(source=source), self.assertRaises(SourceError): parse_source(source)
    def test_rejects_non_literal(self):
        with self.assertRaises(SourceError): parse_source("from fluxscript import App\nname='x'\napp=App(name)")
    def test_rejects_bad_page_and_action(self):
        with self.assertRaises(SourceError): parse_source('from fluxscript import App, Page\napp=App("x")\np=Page("../escape")\napp.add_page(p)')
        with self.assertRaises(SourceError): parse_source('from fluxscript import App, Page, Button\napp=App("x")\np=Page("/")\np.add(Button("Run", "bad-action"))\napp.add_page(p)')
    def test_source_size_limit(self):
        with self.assertRaises(SourceError): parse_source(' ' * 1_000_001)
    def test_generators_emit_files_and_all_pages(self):
        spec = parse_source(VALID)
        with tempfile.TemporaryDirectory() as tmp:
            for name, generator in BACKENDS.items():
                target = Path(tmp) / name
                files = generator(spec, target)
                self.assertTrue(files, name)
                self.assertTrue(all(f.exists() for f in files), name)
            html = (Path(tmp)/"web"/"index.html").read_text()
            self.assertIn('data-route="/settings"', html)
            swift = (Path(tmp)/"ios"/"GeneratedApp.swift").read_text()
            self.assertIn("GeneratedApp", swift)
            import ast
            generated_cli = Path(tmp)/"cli"/"app_cli.py"
            ast.parse(generated_cli.read_text(encoding="utf-8"))
            self.assertIn("submit_form", generated_cli.read_text(encoding="utf-8"))
    def test_service_rejects_insecure_remote_and_host_spoof(self):
        for url in ["http://example.com/api", "http://127.0.0.1.evil.test/api", "ftp://localhost/api", "http://user:pass@localhost/api"]:
            with self.subTest(url=url), self.assertRaises(ValueError): ExecutionServiceClient(url)
        self.assertEqual(ExecutionServiceClient("http://127.0.0.1:2000/api/v2").base_url, "http://127.0.0.1:2000/api/v2")
        self.assertEqual(ExecutionServiceClient("https://example.com/api").base_url, "https://example.com/api")
    def test_service_payload_and_schema(self):
        client = ExecutionServiceClient("http://localhost:2000/api/v2")
        with patch.object(client, "_request", return_value={"run": {"code": 0, "stdout": "ok"}}) as request:
            result = client.execute("python", "3.12", "print('ok')", stdin="", args=["x"])
            self.assertEqual(result["run"]["stdout"], "ok")
            self.assertEqual(request.call_args.args[1]["files"][0]["content"], "print('ok')")
        with patch.object(client, "_request", return_value=[]): self.assertEqual(client.runtimes(), [])
        with patch.object(client, "_request", return_value={"unexpected": True}), self.assertRaises(ExecutionServiceError): client.execute("python", "3.12", "pass")
    def test_dependency_manager_target_contract(self):
        self.assertEqual(ensure_target_dependencies("ios"), [])
        with self.assertRaises(ValueError): ensure_target_dependencies("unknown")
    def test_builder_dependency_manager_requests_latest_helper(self):
        with patch("fluxscript.dependencies._is_importable", return_value=True), \
             patch("fluxscript.dependencies.subprocess.run") as run:
            self.assertEqual(ensure_target_dependencies("web"), ["beautifulsoup4"])
            args = run.call_args.args[0]
            self.assertIn("--upgrade", args)
            self.assertIn("beautifulsoup4", args)
        with patch("fluxscript.dependencies._is_importable", return_value=True), \
             patch("fluxscript.dependencies.subprocess.run") as run:
            self.assertEqual(ensure_target_dependencies("android"), ["defusedxml"])
            self.assertIn("--upgrade", run.call_args.args[0])
    def test_generate_project_creates_directory_and_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "app.py"; src.write_text(VALID, encoding="utf-8")
            storage = Path(tmp) / "storage"
            project, archive, files = generate_project(src, "web", storage)
            self.assertTrue(project.is_dir()); self.assertTrue(archive.is_file()); self.assertTrue(files)
            with zipfile.ZipFile(archive) as zf:
                self.assertTrue(any(n.endswith("index.html") for n in zf.namelist()))
                self.assertTrue(any(n.endswith("fluxscript-project.json") for n in zf.namelist()))
    def test_read_only_analyzer_and_json_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "safe.py").write_text("def hello():\n    return 'ok'\n", encoding="utf-8")
            (root / "review.py").write_text("eval('1 + 1')\n", encoding="utf-8")
            report = analyze_path(root)
            self.assertEqual(report["python_summary"]["files"], 2)
            self.assertEqual(report["summary"]["review_items"], 1)
            out = write_report(report, root / "report.json")
            self.assertEqual(json.loads(out.read_text())["version"], "0.1.0")
    def test_cli_guide_and_version(self):
        from fluxscript.cli import main
        output = io.StringIO()
        with contextlib.redirect_stdout(output): self.assertEqual(main(["guide"]), 0)
        self.assertIn("generate-project", output.getvalue())
        alias_output = io.StringIO()
        with contextlib.redirect_stdout(alias_output): self.assertEqual(main(["Guide"]), 0)
        self.assertIn("COMMAND GUIDE", alias_output.getvalue())
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as generated_help: main(["Generate", "Project", "--help"])
        self.assertEqual(generated_help.exception.code, 0)
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as raised: main(["--version"])
        self.assertEqual(raised.exception.code, 0)
        with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(main(["targets"]), 0)

if __name__ == "__main__": unittest.main()
