"""Validate a generated site without network requests or extra dependencies."""
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path, self.ids, self.refs, self.errors = path, set(), [], []
        self.feed(path.read_text())

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "img" and not (attrs.get("src") or "").strip():
            self.errors.append("empty image URL")
        for key in ("href", "src"):
            if key in attrs:
                self.refs.append(attrs[key] or "")
        if tag == "time" and "datetime" in attrs:
            value = attrs["datetime"]
            try:
                if not re.fullmatch(r"\d{4}(-\d{2}){0,2}", value):
                    raise ValueError()
                date.fromisoformat(value + {4: "-01-01", 7: "-01", 10: ""}[len(value)])
            except (ValueError, KeyError):
                self.errors.append(f"invalid datetime: {value!r}")


root = Path(sys.argv[1]).resolve()
baseurl = sys.argv[2].rstrip("/") if len(sys.argv) > 2 else ""
pages = {path: Page(path) for path in root.rglob("*.html")}
errors = []
for path, page in pages.items():
    errors.extend(f"{path.relative_to(root)}: {e}" for e in page.errors)
    for ref in page.refs:
        url = urlsplit(ref)
        if url.scheme or url.netloc:
            continue
        route = unquote(url.path)
        if route.startswith("/"):
            if baseurl and not (route == baseurl or route.startswith(baseurl + "/")):
                errors.append(f"{path.relative_to(root)}: missing baseurl: {ref}")
                continue
            target = root / route[len(baseurl):].lstrip("/")
        else:
            target = path.parent / route if route else path
        target = target.resolve()
        if target.is_dir():
            target /= "index.html"
        if not target.is_file():
            errors.append(f"{path.relative_to(root)}: missing local target: {ref}")
        elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
            errors.append(f"{path.relative_to(root)}: missing anchor: {ref}")

for unwanted in (
    "_site", "docs", "scripts", "Gemfile", "Gemfile.lock", "README.md",
    "assets/img/logo-preview.html", "team/members.md", "retro_specimen.swift",
    "复古字体样张.pdf", ".github", ".claude", ".shots", ".bundle", ".git", "_private",
):
    if (root / unwanted).exists():
        errors.append(f"build-only content was published: {unwanted}")
for path in (root / "team").glob("*"):
    if path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
        errors.append(f"original member photo was published: {path.relative_to(root)}")
if errors:
    sys.exit("\n".join(errors))
print(f"PASS: {len(pages)} pages; local links, anchors, images, dates and output isolation ({baseurl or '/'})")
