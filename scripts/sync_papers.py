#!/usr/bin/env python3
"""Sync bibliographic metadata from docs/source.md; preview by default.

Scholar profiles identify people's papers; Crossref enriches publisher metadata
through its public API. Scholar CSV exports also work as a supplement.
Uses the existing system network settings, with no browser credentials or
CAPTCHA workarounds.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timezone
import hashlib
import html
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
from urllib.parse import parse_qs, unquote, urlencode, urlsplit, urljoin
from urllib.request import getproxies

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIELDS = "DOI,title,author,published,published-online,published-print,container-title,type,URL,relation"
PAPER_TYPES = {"journal-article", "proceedings-article", "posted-content"}


def normalized(value):
    value = unicodedata.normalize("NFKD", html.unescape(str(value))).casefold()
    return "".join(c for c in value if c.isalnum())


def author_key(value):
    # Handles both 'Given Family' and Scholar's 'Family, Given'. Full names
    # remain required: an initial is never expanded to a guessed identity.
    value = unicodedata.normalize("NFKD", str(value)).casefold()
    return tuple(sorted(re.findall(r"[^\W_]+", value, re.UNICODE)))


def doi_key(value):
    value = unquote(str(value or "")).strip()
    if re.match(r"https?://(?:dx\.)?doi\.org/", value, re.I):
        value = urlsplit(value).path.lstrip("/")
    value = re.sub(r"^doi:\s*", "", value, flags=re.I).casefold()
    return value if re.fullmatch(r"10\.\d{4,9}/\S+", value) else ""


def arxiv_key(value):
    match = re.search(r"(?:arxiv[.:/]\s*|arxiv\.org/(?:abs|pdf)/)(\d{4}\.\d{4,5})(?:v\d+)?", str(value), re.I)
    return match.group(1) if match else ""


def clean_text(value):
    return " ".join(html.unescape(re.sub(r"<[^>]*>", "", str(value))).split())


def read_sources(path):
    people = {}
    source_text = path.read_text()
    for number, line in enumerate(source_text.splitlines(), 1):
        match = re.match(r"^\s*[-*]\s+([^\s\[\]]+)\s+(?:\[[^]]*\]\()?((?:https://)[^\s)]+)\)?\s*$", line)
        if not match:
            continue
        name, url = match.groups()
        parsed = urlsplit(url)
        query = parse_qs(parsed.query)
        person = people.setdefault(name, {})
        if parsed.hostname == "scholar.google.com" and parsed.path == "/citations":
            identifier = query.get("user", [""])[0]
            if not re.fullmatch(r"[A-Za-z0-9_-]+", identifier):
                raise ValueError(f"{path}:{number}: invalid Scholar profile")
            kind, value = "scholar", "https://scholar.google.com/citations?" + urlencode({"user": identifier, "hl": "en"})
        elif parsed.hostname == "api.crossref.org" and parsed.path in ("/works", "/v1/works"):
            author = query.get("query.author", [""])[0].strip()
            if len(author.split()) < 2:
                raise ValueError(f"{path}:{number}: Crossref needs a complete author name")
            kind, value = "crossref", author
        else:
            raise ValueError(f"{path}:{number}: unsupported source URL: {url}")
        if kind in person and person[kind] != value:
            raise ValueError(f"Conflicting {kind} sources for {name}")
        person[kind] = value
    if not people:
        raise ValueError(f"No person sources found in {path}")
    identities = {}
    for block in re.findall(r"```yaml\s*\n(.*?)\n```", source_text, re.S):
        settings = yaml.safe_load(block) or {}
        identities.update(settings.get("identities", {}))
    for name, person in people.items():
        person["identity"] = identities.get(name, {})
        if "crossref" in person and not person["identity"].get("orcid") and not person["identity"].get("coauthors"):
            raise ValueError(f"{name}: add verified ORCID/coauthors in source.md to disambiguate names")
    return people


class Client:
    def __init__(self, cache_dir, offline=False, refresh=False):
        self.cache_dir, self.offline, self.refresh = Path(cache_dir), offline, refresh
        self.last_request = 0

    def get(self, url):
        return self._get(url, "json")

    def get_text(self, url):
        return self._get(url, "text")

    def _get(self, url, kind):
        key = hashlib.sha256(url.encode()).hexdigest()
        path = self.cache_dir / (key + ".json")
        if path.exists() and not self.refresh:
            cached = json.loads(path.read_text())
            age = datetime.now(timezone.utc).timestamp() - cached["fetched_at"]
            if cached["url"] == url and (self.offline or age < 86400):
                return cached["data"]
        if self.offline:
            raise ValueError(f"No cached response for {url}; run online first")
        delay = 1 - (time.monotonic() - self.last_request)
        if delay > 0:
            time.sleep(delay)
        # urllib reads the configured macOS system proxy as well as normal
        # proxy environment variables. Use the user's existing network setup.
        environment = os.environ.copy()
        for scheme, proxy in getproxies().items():
            if scheme in ("http", "https"):
                environment.setdefault(scheme + "_proxy", proxy)
        with tempfile.TemporaryDirectory(prefix="pilab-fetch-") as directory:
            body = Path(directory) / "response.json"
            result = subprocess.run([
                "curl", "--silent", "--show-error", "--location", "--compressed",
                "--connect-timeout", "10", "--max-time", "45",
                "--user-agent", "PiLabPaperSync/1.0 (+https://pilab-zju.github.io/)",
                "--output", str(body), "--write-out", "%{http_code}", url,
            ], capture_output=True, text=True, timeout=50, env=environment)
            self.last_request = time.monotonic()
            if result.returncode or result.stdout != "200":
                raise ValueError(f"Fetch failed ({result.stdout or result.returncode}): {url}; {result.stderr.strip()}")
            try:
                raw = body.read_bytes()
                if kind == "json":
                    data = json.loads(raw)
                else:
                    charset = re.search(br"charset\s*=\s*[\"']?([A-Za-z0-9_-]+)", raw[:4096], re.I)
                    data = raw.decode(charset[1].decode() if charset else "utf-8")
            except (ValueError, OSError) as error:
                raise ValueError(f"Source returned invalid JSON or an access challenge: {url}") from error
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        atomic_write(path, json.dumps({"url": url, "fetched_at": datetime.now(timezone.utc).timestamp(), "data": data}, ensure_ascii=False))
        return data


class Node:
    def __init__(self, tag="", attrs=None):
        self.tag, self.attrs, self.children = tag, dict(attrs or []), []

    def text(self):
        return "".join(c.text() if isinstance(c, Node) else c for c in self.children)

    def find(self, tag=None, cls=None, identifier=None):
        found = []
        for child in self.children:
            if isinstance(child, Node):
                if ((not tag or child.tag == tag) and (not cls or cls in child.attrs.get("class", "").split())
                        and (not identifier or child.attrs.get("id") == identifier)):
                    found.append(child)
                found.extend(child.find(tag, cls, identifier))
        return found


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack)-1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, value):
        self.stack[-1].children.append(value)


def scholar_rows(text):
    root = Document(text).root
    if not root.find(identifier="gsc_prf_in"):
        raise ValueError("Scholar returned an access challenge or unrecognized profile; use --crossref-only or a CSV export")
    rows = []
    for node in root.find("tr", cls="gsc_a_tr"):
        titles, years = node.find("a", cls="gsc_a_at"), node.find("td", cls="gsc_a_y")
        gray = node.find("div", cls="gs_gray")
        if not titles or not years:
            raise ValueError("Scholar profile layout changed; no papers were written")
        rows.append({"title": clean_text(titles[0].text()), "year": clean_text(years[0].text()),
                     "venue": clean_text(gray[1].text()) if len(gray) > 1 else "",
                     "url": urljoin("https://scholar.google.com", titles[0].attrs.get("href", ""))})
    return rows


def fetch_scholar(client, profile, as_of, years):
    query = parse_qs(urlsplit(profile).query)
    rows = []
    for offset in range(0, 1000, 100):
        params = {"user": query["user"][0], "hl": "en", "pagesize": 100, "sortby": "pubdate"}
        if offset:
            params["cstart"] = offset
        page = scholar_rows(client.get_text("https://scholar.google.com/citations?" + urlencode(params)))
        rows.extend(p for p in page if p["year"].isdigit() and as_of.year-years+1 <= int(p["year"]) <= as_of.year)
        if len(page) < 100 or any(p["year"].isdigit() and int(p["year"]) < as_of.year-years+1 for p in page):
            return rows
    raise ValueError("Scholar profile exceeds the 1000-record limit; narrow the source manually")


def scholar_detail(text, row, person, as_of, years):
    root = Document(text).root
    titles = root.find(identifier="gsc_oci_title")
    if not titles:
        raise ValueError("Scholar returned an access challenge or unrecognized paper detail")
    fields = {}
    for section in root.find(cls="gs_scl"):
        labels, values = section.find(cls="gsc_oci_field"), section.find(cls="gsc_oci_value")
        if labels and values:
            fields[clean_text(labels[0].text())] = clean_text(values[0].text())
    raw_date = fields.get("Publication date", row["year"])
    parts = raw_date.split("/")
    if not 1 <= len(parts) <= 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"Unrecognized Scholar publication date for {row['title']}: {raw_date}")
    published = date(*([int(p) for p in parts] + [1] * (3-len(parts))))
    if published > as_of or published.year < as_of.year-years+1:
        return None
    authors = [clean_text(a) for a in re.split(r"[,，;；]", fields.get("Authors", "")) if a.strip()]
    if not authors:
        raise ValueError(f"Missing Scholar authors for {row['title']}")
    venue = fields.get("Journal") or fields.get("Conference") or fields.get("Book") or fields.get("Source") or row["venue"]
    is_preprint = bool(re.search(r"arxiv|ssrn|corr\b|preprint|research square|biorxiv|medrxiv", venue, re.I))
    links = []
    for anchor in titles[0].find("a"):
        url = anchor.attrs.get("href", "")
        if urlsplit(url).scheme in ("http", "https"):
            links.append({"label": "原文", "url": url})
    links.append({"label": "Google Scholar", "url": row["url"]})
    doi = next((key for link in links if (key := doi_key(link["url"]))), "")
    return {"title": clean_text(titles[0].text()), "authors": authors, "date": published,
            "date_precision": {1: "year", 2: "month", 3: "day"}[len(parts)], "date_kind": "publication",
            "doi": doi, "venue": venue, "status": "Preprint" if is_preprint else "Published",
            "links": links, "source": row["url"], "source_members": [person],
            "imported_by": "sync_papers", "published": True}


def publication_date(item, as_of):
    # Prefer a publisher's online date. Never use created/deposited/indexed
    # timestamps, which describe metadata processing, not publication.
    for field in ("published-online", "published", "published-print"):
        parts = item.get(field, {}).get("date-parts", [[]])[0]
        if not 1 <= len(parts) <= 3:
            continue
        try:
            value = date(*(parts + [1] * (3 - len(parts))))
        except (ValueError, TypeError):
            continue
        if value <= as_of:
            return value, {1: "year", 2: "month", 3: "day"}[len(parts)]
    return None


def from_crossref(item, name, expected_author, as_of, years):
    if item.get("type") not in PAPER_TYPES:
        return None
    authors = [clean_text(" ".join(filter(None, (a.get("given"), a.get("family"))))) for a in item.get("author", [])]
    if author_key(expected_author) not in {author_key(a) for a in authors}:
        return None
    published = publication_date(item, as_of)
    doi = doi_key(item.get("DOI"))
    title = clean_text((item.get("title") or [""])[0])
    if not published or not doi or not title or published[0].year < as_of.year - years + 1:
        return None
    related = []
    for relation in ("is-preprint-of", "has-preprint", "is-version-of", "has-version"):
        for entry in item.get("relation", {}).get(relation, []):
            identifier = doi_key(entry.get("id"))
            if identifier:
                related.append(identifier)
    return {
        "title": title, "date": published[0], "date_precision": published[1],
        "date_kind": "publication", "authors": authors, "doi": doi,
        "venue": clean_text((item.get("container-title") or [""])[0]),
        "status": "Preprint" if item["type"] == "posted-content" else "Published",
        "links": [{"label": "DOI", "url": "https://doi.org/" + doi}],
        "source": "https://api.crossref.org/works/" + doi,
        "source_members": [name], "related_dois": sorted(set(related)),
        "imported_by": "sync_papers", "published": True,
    }


def identity_matches(item, author, identity, known_title=False):
    matched = [a for a in item.get("author", []) if author_key(" ".join(filter(None, (a.get("given"), a.get("family"))))) == author_key(author)]
    observed = {a["ORCID"].rstrip("/").split("/")[-1].upper() for a in matched if a.get("ORCID")}
    expected = str(identity.get("orcid", "")).upper()
    if observed and expected:
        return expected in observed
    coauthors = {author_key(" ".join(filter(None, (a.get("given"), a.get("family"))))) for a in item.get("author", [])}
    coauthors.discard(author_key(author))
    return known_title or bool(coauthors & {author_key(a) for a in identity.get("coauthors", [])})


def fetch_crossref(client, name, author, as_of, years, limit, identity, scholar_titles=None):
    params = {"query.author": author, "filter": f"from-pub-date:{as_of.year-years+1}-01-01,until-pub-date:{as_of.isoformat()}",
              "rows": limit, "select": FIELDS}
    url = "https://api.crossref.org/works?" + urlencode(params)
    response = client.get(url)
    message = response.get("message", {})
    if not isinstance(message.get("items"), list):
        raise ValueError(f"Invalid Crossref response for {name}")
    papers, rejected = [], []
    for item in message["items"]:
        paper = from_crossref(item, name, author, as_of, years)
        if paper:
            if identity_matches(item, author, identity, normalized(paper["title"]) in (scholar_titles or set())):
                papers.append(paper)
            else:
                rejected.append({"title": paper["title"], "doi": paper["doi"], "reason": "identity not confirmed"})
    return papers, {"person": name, "provider": "Crossref", "url": url,
                    "candidates": len(message["items"]), "matched": len(papers),
                    "identity_rejected": rejected,
                    "total_search_results": message.get("total-results", 0)}


def read_scholar_csv(path, name, profile, as_of, years):
    reader = csv.DictReader(io.StringIO(Path(path).read_text(encoding="utf-8-sig")))
    if not {"Title", "Authors", "Year"}.issubset(reader.fieldnames or []):
        raise ValueError("Scholar CSV must contain Title, Authors and Year columns")
    papers = []
    for row in reader:
        title, year = clean_text(row["Title"]), row["Year"].strip()
        if not re.fullmatch(r"\d{4}", year) or not as_of.year-years+1 <= int(year) <= as_of.year:
            continue
        authors = [clean_text(a) for a in row["Authors"].split(";") if a.strip()]
        if not title or not authors:
            raise ValueError(f"Incomplete Scholar CSV row in {path}")
        doi = doi_key(row.get("DOI"))
        url = row.get("URL", "").strip()
        if url and urlsplit(url).scheme not in ("http", "https"):
            raise ValueError(f"Unsafe CSV paper URL: {url}")
        links = ([{"label": "DOI", "url": "https://doi.org/" + doi}] if doi else [])
        if url and not doi_key(url):
            links.append({"label": "原文", "url": url})
        if not links:
            links = [{"label": "Google Scholar", "url": profile}]
        venue = clean_text(row.get("Publication", ""))
        papers.append({"title": title, "date": date(int(year), 1, 1), "date_precision": "year",
                       "date_kind": "publication", "authors": authors, "doi": doi, "venue": venue,
                       "status": "Preprint" if "arxiv" in venue.casefold() else "Published",
                       "links": links, "source": profile, "source_members": [name],
                       "imported_by": "sync_papers", "published": True})
    return papers


def identifiers(paper):
    values = [paper.get("doi", "")] + paper.get("related_dois", [])
    values += [link.get("url", "") for link in paper.get("links", [])]
    result = {"doi:" + key for value in values if (key := doi_key(value))}
    result.update("arxiv:" + key for value in values + [paper.get("venue", "")] if (key := arxiv_key(value)))
    return result


def same_work(left, right):
    if identifiers(left) & identifiers(right):
        return True
    if normalized(left.get("title", "")) != normalized(right.get("title", "")):
        return False
    return bool({author_key(a) for a in left.get("authors", [])} & {author_key(a) for a in right.get("authors", [])})


def merge_records(target, incoming, preserve=False):
    original = dict(target)
    # Curated metadata, body, source links and explicit draft decisions survive.
    # An auto-imported preprint may be upgraded to the publisher version.
    if not preserve and target.get("status") == "Preprint" and incoming.get("status") == "Published":
        target.update(incoming)
    for field in ("source_members", "related_dois"):
        union = sorted(set(original.get(field, []) + incoming.get(field, [])))
        if union:
            target[field] = union
    links = original.get("links", []) + incoming.get("links", [])
    by_url = {}
    for link in links:
        by_url.setdefault(link["url"], link)
    target["links"] = list(by_url.values())
    if not target.get("doi") and incoming.get("doi"):
        target["doi"] = incoming["doi"]
    return target


def deduplicate(papers):
    groups = []
    # Prefer the formal version and publisher metadata to year-only CSV data.
    for paper in sorted(papers, key=lambda p: (p.get("status") == "Preprint", not bool(p.get("doi")),
                                              {"day": 0, "month": 1, "year": 2}.get(p.get("date_precision"), 3),
                                              normalized(p["title"]), p.get("doi", ""))):
        matches = [p for p in groups if same_work(p, paper)]
        if not matches:
            groups.append(dict(paper))
        else:
            target = matches[0]
            merge_records(target, paper)
            for duplicate in matches[1:]:
                merge_records(target, duplicate)
                groups.remove(duplicate)
    return groups


def load_papers(directory):
    result = []
    for path in sorted(Path(directory).glob("*.md")):
        text = path.read_text()
        match = re.match(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)(.*)\Z", text, re.S)
        if not match:
            raise ValueError(f"Invalid paper front matter: {path}")
        metadata = yaml.safe_load(match[1])
        if not isinstance(metadata, dict) or not metadata.get("title"):
            raise ValueError(f"Missing paper title: {path}")
        result.append({"path": path, "metadata": metadata, "body": match[2], "original": text})
    return result


def encode_paper(metadata, body=""):
    return "---\n" + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False, width=1000) + "---\n" + body


def paper_filename(paper):
    slug = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", paper["title"]).encode("ascii", "ignore").decode().lower()).strip("-")[:72].rstrip("-") or "paper"
    key = paper.get("doi") or normalized(paper["title"])
    return slug + "-" + hashlib.sha256(key.encode()).hexdigest()[:10] + ".md"


def plan_changes(existing, incoming, directory):
    writes, counts = {}, {"new": 0, "updated": 0, "unchanged": 0, "drafts_preserved": 0}
    # Existing ambiguous duplicates require a deliberate merge to preserve URLs.
    for paper in incoming:
        matches = [item for item in existing if same_work(item["metadata"], paper)]
        if len(matches) > 1:
            raise ValueError("Existing duplicate records need review: " + ", ".join(str(m["path"]) for m in matches))
        if matches:
            item = matches[0]
            if item["metadata"].get("published") is False:
                counts["drafts_preserved"] += 1
                continue
            before = json.dumps(item["metadata"], sort_keys=True, default=str, ensure_ascii=False)
            merged = merge_records(item["metadata"], paper, preserve=item["metadata"].get("imported_by") != "sync_papers")
            after = json.dumps(merged, sort_keys=True, default=str, ensure_ascii=False)
            if before == after:
                counts["unchanged"] += 1
            else:
                writes[item["path"]] = encode_paper(merged, item["body"])
                counts["updated"] += 1
        else:
            path = Path(directory) / paper_filename(paper)
            if path.exists() or path in writes:
                raise ValueError(f"Refusing to overwrite unmatched paper: {path}")
            writes[path] = encode_paper(paper)
            existing.append({"path": path, "metadata": paper, "body": "", "original": ""})
            counts["new"] += 1
    return writes, counts


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(content)
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "docs/source.md")
    parser.add_argument("--papers-dir", type=Path, default=ROOT / "_papers")
    parser.add_argument("--people-data", type=Path, default=ROOT / "_data/people_sources.yml")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "_private/paper-sync-cache")
    parser.add_argument("--report", type=Path, default=ROOT / "_private/paper-sync-report.json")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--years", type=int, default=3)
    parser.add_argument("--max-results", type=int, default=1000, help="Crossref candidates per person, maximum 1000")
    parser.add_argument("--csv", action="append", default=[], metavar="PERSON=FILE", help="Supplement with a Google Scholar CSV export")
    parser.add_argument("--offline", action="store_true", help="Use cached API responses")
    parser.add_argument("--refresh", action="store_true", help="Ignore the 24-hour cache")
    parser.add_argument("--write", action="store_true", help="Write planned changes after every source succeeds")
    parser.add_argument("--include-preprints", action="store_true", help="Also import works that only have a preprint version")
    parser.add_argument("--crossref-only", action="store_true", help="Explicit fallback when Scholar is unavailable; keep Scholar profile links")
    args = parser.parse_args(argv)
    if args.years < 1 or not 1 <= args.max_results <= 1000 or (args.offline and args.refresh):
        parser.error("years must be positive, max-results must be 1–1000; offline and refresh are exclusive")
    people = read_sources(args.source)
    csvs = {}
    for value in args.csv:
        name, separator, filename = value.partition("=")
        if not separator or name not in people or "scholar" not in people[name]:
            parser.error("--csv requires PERSON=FILE for a Scholar person in source.md")
        csvs.setdefault(name, []).append(filename)
    client = Client(args.cache_dir, args.offline, args.refresh)
    incoming, reports = [], []
    for name, person in people.items():
        if "crossref" not in person and (args.crossref_only or not person.get("scholar")) and name not in csvs:
            raise ValueError(f"{name}: no enabled source; use Scholar, add a verified Crossref source, or supply --csv")
        print(f"Fetching {name} ...", flush=True)
        rows = []
        if person.get("scholar") and not args.crossref_only:
            rows = fetch_scholar(client, person["scholar"], args.as_of, args.years)
            reports.append({"person": name, "provider": "Google Scholar", "url": person["scholar"], "matched": len(rows)})
        if "crossref" in person:
            papers, report = fetch_crossref(client, name, person["crossref"], args.as_of, args.years, args.max_results, person["identity"], {normalized(r["title"]) for r in rows})
            incoming.extend(papers)
            reports.append(report)
            print(f"  {report['matched']} exact author matches / {report['candidates']} candidates", flush=True)
        for row in rows:
            matches = [p for p in incoming if normalized(p["title"]) == normalized(row["title"])
                       and (name in p["source_members"] or (person.get("crossref")
                            and author_key(person["crossref"]) in {author_key(a) for a in p["authors"]}))]
            if matches:
                for paper in matches:
                    paper["source_members"] = sorted(set(paper["source_members"] + [name]))
                continue
            if not args.include_preprints and re.search(r"arxiv|ssrn|corr\b|preprint|research square|biorxiv|medrxiv", row["venue"], re.I):
                continue
            print(f"  Scholar detail: {row['title']}", flush=True)
            paper = scholar_detail(client.get_text(row["url"]), row, name, args.as_of, args.years)
            if paper:
                incoming.append(paper)
        for filename in csvs.get(name, []):
            papers = read_scholar_csv(filename, name, person["scholar"], args.as_of, args.years)
            incoming.extend(papers)
            reports.append({"person": name, "provider": "Scholar CSV", "matched": len(papers)})
    if not incoming:
        raise ValueError("No papers found; source data and existing papers were not changed")
    unique = deduplicate(incoming)
    preprints = sum(p.get("status") == "Preprint" for p in unique)
    if not args.include_preprints:
        unique = [p for p in unique if p.get("status") != "Preprint"]
    writes, counts = plan_changes(load_papers(args.papers_dir), unique, args.papers_dir)
    profiles = {name: {"scholar": person["scholar"]} for name, person in people.items() if person.get("scholar")}
    profile_content = "# Generated by scripts/sync_papers.py from docs/source.md\n" + yaml.safe_dump(profiles, allow_unicode=True, sort_keys=False)
    if not args.people_data.exists() or args.people_data.read_text() != profile_content:
        writes[args.people_data] = profile_content
    report = {"as_of": str(args.as_of), "years": args.years, "window": [args.as_of.year-args.years+1, args.as_of.year],
              "sources": reports, "raw_matches": len(incoming), "unique_matches": len(unique),
              "duplicates_merged": len(incoming)-len(unique)-(preprints if not args.include_preprints else 0),
              "preprints_excluded": preprints if not args.include_preprints else 0, **counts, "write": args.write,
              "files": sorted(str(path) for path in writes)}
    # Nothing in _papers or _data is touched until every source and merge has
    # succeeded. Missing upstream records never trigger deletion.
    if args.write:
        for path, content in writes.items():
            atomic_write(path, content)
    atomic_write(args.report, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("sources", "files")}, ensure_ascii=False, indent=2))
    print(f"Report: {args.report}")
    if not args.write:
        print("Preview only. Add --write to apply these changes.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
