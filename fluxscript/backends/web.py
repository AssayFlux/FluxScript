"""Generate a dependency-light, multi-page accessible web starter."""
from html import escape
from pathlib import Path
import json
from ..models import AppSpec, ElementSpec

def _render_element(e: ElementSpec) -> str:
    text = escape(e.text, quote=True)
    if e.kind == "text": return f'<p class="copy">{text}</p>'
    if e.kind == "heading":
        level = int(e.attributes.get("level", 1))
        return f'<h{level}>{text}</h{level}>'
    if e.kind == "button": return f'<button type="button" data-action="{escape(e.action or "", quote=True)}">{text}</button>'
    if e.kind == "input":
        name = escape(e.name or "", quote=True); typ = escape(e.attributes.get("input_type", "text"), quote=True)
        return f'<label>{text}<input name="{name}" type="{typ}" autocomplete="off" /></label>'
    raise ValueError(f"Unknown element kind: {e.kind}")

def _json_script(value) -> str:
    # JSON embedded in a script must not be able to close the script element.
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

def generate_web(spec: AppSpec, out: Path) -> list[Path]:
    issues = spec.validate()
    if issues: raise ValueError("Invalid application: " + "; ".join(issues))
    out.mkdir(parents=True, exist_ok=True)
    title = escape(spec.name, quote=True)
    nav = "\n      ".join(f'<a href="#{escape(page.path, quote=True)}" data-route-link="{escape(page.path, quote=True)}">{escape(page.title or page.path)}</a>' for page in spec.pages)
    sections=[]
    for index, page in enumerate(spec.pages):
        page_title = escape(page.title or spec.name, quote=True)
        body = "\n        ".join(_render_element(e) for e in page.elements)
        sections.append(f'<section class="page" data-route="{escape(page.path, quote=True)}" aria-label="{page_title}"{"" if index == 0 else " hidden"}>\n        <h1 class="page-title">{page_title}</h1>\n        {body}\n      </section>')
    html = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="{title} — generated with FluxScript" />
  <meta name="color-scheme" content="light dark" />
  <title>{title}</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <header class="topbar"><a class="brand" href="#/">{title}</a><nav aria-label="Main navigation">{nav}</nav></header>
  <main class="app-shell" data-flux-app="{title}">
    <div class="panel">\n      {' '.join(sections)}\n      <p class="status" role="status" aria-live="polite" hidden></p>
    </div>
  </main>
  <script src="app.js" defer></script>
</body>
</html>
'''
    css = '''* { box-sizing: border-box; }
:root { font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #172033; background: #f3f5f9; }
body { margin: 0; min-height: 100vh; }
.topbar { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 16px clamp(16px, 4vw, 48px); background: #fff; border-bottom: 1px solid #dce2ec; }
.brand { font-weight: 750; color: inherit; text-decoration: none; }
nav { display: flex; gap: 16px; flex-wrap: wrap; }
nav a { color: #2457d6; text-decoration: none; padding: 6px 2px; }
nav a[aria-current="page"] { font-weight: 700; text-decoration: underline; text-underline-offset: 5px; }
.app-shell { min-height: calc(100vh - 64px); display: grid; place-items: start center; padding: clamp(16px, 5vw, 56px); }
.panel { width: min(100%, 820px); padding: clamp(22px, 5vw, 48px); background: #fff; border: 1px solid #dce2ec; border-radius: 20px; box-shadow: 0 12px 36px #17203312; }
.page-title { margin-top: 0; line-height: 1.2; }
.copy { line-height: 1.7; color: #46536b; }
button { border: 0; border-radius: 10px; padding: 12px 18px; background: #2457d6; color: #fff; font: inherit; font-weight: 600; cursor: pointer; }
button:hover { background: #1744b4; }
button:focus-visible, input:focus-visible, a:focus-visible { outline: 3px solid #86a8ff; outline-offset: 3px; }
label { display: grid; gap: 8px; margin: 16px 0; font-weight: 550; }
input { width: 100%; max-width: 480px; padding: 11px 12px; border: 1px solid #aab5c7; border-radius: 8px; font: inherit; }
.status { margin-top: 24px; padding: 12px; background: #eef4ff; border-radius: 8px; color: #183b83; }
[hidden] { display: none !important; }
@media (max-width: 560px) { .topbar { align-items: flex-start; flex-direction: column; } nav { gap: 12px; } }
@media (prefers-color-scheme: dark) { :root { color: #eef2fa; background: #101521; } .topbar, .panel { background: #192131; border-color: #303b50; } .copy { color: #c0cadd; } input { background: #101521; color: inherit; border-color: #58657a; } .status { background: #20345b; color: #e2eaff; } }
'''
    js = '''/** FluxScript runtime bridge. App-specific behavior is registered by the developer. */
(() => {
  const root = document.querySelector("[data-flux-app]");
  if (!root) return;
  const pages = [...root.querySelectorAll("[data-route]")];
  const links = [...document.querySelectorAll("[data-route-link]")];
  const status = root.querySelector("[role=status]");
  const normalize = (route) => route && route.startsWith("/") ? route : "/";
  function navigate() {
    const route = normalize(location.hash.slice(1) || "/");
    const selected = pages.find((page) => page.dataset.route === route) || pages[0];
    pages.forEach((page) => { page.hidden = page !== selected; });
    links.forEach((link) => {
      if (link.dataset.routeLink === selected.dataset.route) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
  }
  window.addEventListener("hashchange", navigate);
  navigate();
  root.addEventListener("click", (event) => {
    const target = event.target;
    const button = target instanceof Element ? target.closest("button[data-action]") : null;
    if (!button) return;
    const action = button.dataset.action || "";
    const values = Object.fromEntries([...root.querySelectorAll("input[name]")].map((input) => [input.name, input.value]));
    const accepted = root.dispatchEvent(new CustomEvent("flux:action", { bubbles: true, cancelable: true, detail: { action, values } }));
    if (accepted && status) { status.hidden = false; status.textContent = `Action requested: ${action}. Connect a handler for application behavior.`; }
  });
  // Example integration: root.addEventListener("flux:action", (event) => { ... });
})();
'''
    ts = '''/** Typed counterpart of app.js; check with `npm install && npm run typecheck`. */
type FluxActionDetail = { action: string; values: Record<string, string> };
const root = document.querySelector<HTMLElement>("[data-flux-app]");
if (root) {
  const pages = Array.from(root.querySelectorAll<HTMLElement>("[data-route]"));
  const links = Array.from(document.querySelectorAll<HTMLAnchorElement>("[data-route-link]"));
  const status = root.querySelector<HTMLElement>("[role=status]");
  const normalize = (route: string): string => route.startsWith("/") ? route : "/";
  const navigate = (): void => {
    const route = normalize(location.hash.slice(1) || "/");
    const selected = pages.find((page) => page.dataset.route === route) ?? pages[0];
    if (!selected) return;
    pages.forEach((page) => { page.hidden = page !== selected; });
    links.forEach((link) => link.dataset.routeLink === selected.dataset.route ? link.setAttribute("aria-current", "page") : link.removeAttribute("aria-current"));
  };
  window.addEventListener("hashchange", navigate); navigate();
  root.addEventListener("click", (event: MouseEvent) => {
    const target = event.target;
    const button = target instanceof Element ? target.closest<HTMLButtonElement>("button[data-action]") : null;
    if (!button) return;
    const values = Object.fromEntries(Array.from(root.querySelectorAll<HTMLInputElement>("input[name]")).map((input) => [input.name, input.value]));
    root.dispatchEvent(new CustomEvent<FluxActionDetail>("flux:action", { bubbles: true, cancelable: true, detail: { action: button.dataset.action ?? "", values } }));
    if (status) { status.hidden = false; status.textContent = `Action requested: ${button.dataset.action ?? ""}. Connect a handler for application behavior.`; }
  });
}
'''
    files = {"index.html": html, "styles.css": css, "app.js": js, "app.ts": ts,
      "package.json": '{\n  "name": "fluxscript-generated-app",\n  "private": true,\n  "version": "0.1.0",\n  "scripts": { "typecheck": "tsc --noEmit" },\n  "devDependencies": { "typescript": "^5.0.0" }\n}\n',
      "tsconfig.json": '{\n  "compilerOptions": { "target": "ES2020", "module": "ES2020", "strict": true, "noEmit": true, "lib": ["ES2020", "DOM"] },\n  "include": ["app.ts"]\n}\n',
      "README.md": f"# {spec.name}\n\nGenerated by FluxScript 0.1.0. Supports all declared pages through hash navigation. Run `python -m http.server 8000` and open http://127.0.0.1:8000 to preview. For TypeScript validation, install Node.js/npm then run `npm install && npm run typecheck`. Buttons emit a cancellable `flux:action` event with `{{action, values}}; register an application handler before treating actions as business functionality. Review security, accessibility, persistence, API integration and browser support before production deployment.\n"}
    result=[]
    for name, content in files.items():
        path=out/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(content,encoding="utf-8"); result.append(path)
    return result
