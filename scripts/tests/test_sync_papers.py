from datetime import date
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sync_papers as sync

TODAY = date(2026, 9, 11)


def record(title="An Example: Graph Learning", doi="10.1234/example", status="Published", person="甲"):
    return {"title": title, "doi": doi, "authors": ["Zhuoren Jiang", "Weikang Yuan"],
            "date": date(2026, 3, 1), "date_precision": "month", "status": status,
            "source_members": [person], "links": [{"label": "DOI", "url": "https://doi.org/" + doi}],
            "imported_by": "sync_papers", "published": True}


class SyncTests(unittest.TestCase):
    def test_shared_paper_has_one_entry_and_all_people(self):
        a, b = record(person="甲"), record(person="乙")
        b["doi"] = "https://doi.org/10.1234/EXAMPLE"
        result = sync.deduplicate([a, b])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source_members"], ["乙", "甲"])

    def test_title_punctuation_and_unicode_versions_merge(self):
        a, b = record("Café: AI—Society", "10.1234/a"), record("CAFE AI Society", "10.1234/b")
        self.assertTrue(sync.same_work(a, b))

    def test_identical_generic_title_with_different_authors_is_not_merged(self):
        a, b = record("Introduction", "10.1234/a"), record("Introduction", "10.1234/b")
        b["authors"] = ["Another Person"]
        self.assertFalse(sync.same_work(a, b))

    def test_published_version_wins_over_preprint(self):
        preprint = record(doi="10.48550/arxiv.2401.01234", status="Preprint")
        final = record(doi="10.1234/publisher", person="乙")
        result = sync.deduplicate([preprint, final])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["doi"], "10.1234/publisher")
        self.assertEqual(len(result[0]["links"]), 2)

    def test_arxiv_versions_have_one_identity(self):
        self.assertEqual(sync.arxiv_key("https://arxiv.org/abs/2401.01234v3"), "2401.01234")
        self.assertEqual(sync.arxiv_key("10.48550/arXiv.2401.01234"), "2401.01234")

    def test_publisher_preprint_relationship_handles_renamed_title(self):
        a, b = record("Old title", "10.1234/pre"), record("New title", "10.1234/final")
        b["related_dois"] = ["10.1234/pre"]
        self.assertTrue(sync.same_work(a, b))

    def test_different_orcid_rejects_homonym_even_with_shared_coauthor(self):
        item = {"author": [{"given": "Pengwei", "family": "Yan", "ORCID": "https://orcid.org/WRONG"},
                           {"given": "Zhuoren", "family": "Jiang"}]}
        self.assertFalse(sync.identity_matches(item, "Pengwei Yan", {"orcid": "RIGHT", "coauthors": ["Zhuoren Jiang"]}))

    def test_homonym_without_identity_evidence_is_rejected(self):
        item = {"author": [{"given": "Weikang", "family": "Yuan"}, {"given": "Chemistry", "family": "Researcher"}]}
        self.assertFalse(sync.identity_matches(item, "Weikang Yuan", {"coauthors": ["Zhuoren Jiang"]}))

    def test_verified_coauthor_can_confirm_identity_when_orcid_is_missing(self):
        item = {"author": [{"given": "Weikang", "family": "Yuan"}, {"given": "Zhuoren", "family": "Jiang"}]}
        self.assertTrue(sync.identity_matches(item, "Weikang Yuan", {"coauthors": ["Zhuoren Jiang"]}))

    def test_exact_orcid_can_confirm_new_collaboration(self):
        item = {"author": [{"given": "Zhuoren", "family": "Jiang", "ORCID": "https://orcid.org/0000-0001-8562-8347"}]}
        self.assertTrue(sync.identity_matches(item, "Zhuoren Jiang", {"orcid": "0000-0001-8562-8347"}))

    def test_dates_preserve_precision_and_ignore_deposit_dates(self):
        self.assertEqual(sync.publication_date({"published": {"date-parts": [[2024]]}}, TODAY), (date(2024, 1, 1), "year"))
        self.assertEqual(sync.publication_date({"published": {"date-parts": [[2025, 7]]}}, TODAY), (date(2025, 7, 1), "month"))
        self.assertIsNone(sync.publication_date({"created": {"date-parts": [[2026, 1, 1]]}}, TODAY))
        self.assertIsNone(sync.publication_date({"published": {"date-parts": [[2027, 1]]}}, TODAY))

    def test_online_publication_can_precede_future_print_issue(self):
        data = {"published": {"date-parts": [[2027, 1]]}, "published-online": {"date-parts": [[2026, 8, 1]]}}
        self.assertEqual(sync.publication_date(data, TODAY), (date(2026, 8, 1), "day"))

    def test_three_calendar_years_and_full_name_filter(self):
        data = {"type": "journal-article", "title": ["A paper"], "DOI": "10.1234/a", "published": {"date-parts": [[2024]]},
                "author": [{"given": "Zhuoren", "family": "Jiang"}]}
        self.assertIsNotNone(sync.from_crossref(data, "蒋卓人", "Zhuoren Jiang", TODAY, 3))
        data["published"]["date-parts"] = [[2023]]
        self.assertIsNone(sync.from_crossref(data, "蒋卓人", "Zhuoren Jiang", TODAY, 3))
        data["published"]["date-parts"] = [[2026]]
        data["author"][0]["given"] = "Z"
        self.assertIsNone(sync.from_crossref(data, "蒋卓人", "Zhuoren Jiang", TODAY, 3))

    def test_curated_content_and_url_survive_and_second_sync_is_noop(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stable-url.md"
            old = record(); old.pop("imported_by"); old["summary"] = "人工维护的中文简介"
            body = "\n    Keep this indentation.\n"
            path.write_text(sync.encode_paper(old, body))
            incoming = record(person="乙"); incoming["title"] = "AN EXAMPLE GRAPH LEARNING"
            writes, counts = sync.plan_changes(sync.load_papers(directory), [incoming], directory)
            self.assertEqual(counts["updated"], 1)
            self.assertEqual(set(writes), {path})
            self.assertIn("人工维护的中文简介", writes[path])
            self.assertTrue(writes[path].endswith(body))
            path.write_text(writes[path])
            writes, counts = sync.plan_changes(sync.load_papers(directory), [incoming], directory)
            self.assertEqual(writes, {})
            self.assertEqual(counts["unchanged"], 1)

    def test_draft_cannot_be_resurrected_by_import(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.md"
            old = record(); old["published"] = False
            path.write_text(sync.encode_paper(old))
            writes, counts = sync.plan_changes(sync.load_papers(directory), [record()], directory)
            self.assertFalse(writes)
            self.assertEqual(counts["drafts_preserved"], 1)

    def test_scholar_csv_preserves_year_and_deduplicates_across_people(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scholar.csv"
            path.write_text('Title,Authors,Year,Publication\n"An Example: Graph Learning","Jiang, Zhuoren; Yuan, Weikang",2026,AAAI\nOld paper,Jiang,2023,Old venue\n')
            papers = sync.read_scholar_csv(path, "蒋卓人", "https://scholar.google.com/citations?user=A", TODAY, 3)
            self.assertEqual(len(papers), 1)
            self.assertEqual(papers[0]["date_precision"], "year")
            self.assertEqual(len(sync.deduplicate(papers + [record()])), 1)
            merged = sync.deduplicate(papers + [record()])[0]
            self.assertEqual(merged["date"], date(2026, 3, 1))
            self.assertEqual(merged["date_precision"], "month")

    def test_scholar_profile_handles_entities_and_rejects_challenges(self):
        text = '''<div id="gsc_prf_in">A Person</div><table><tr class="gsc_a_tr">
          <td><a class="gsc_a_at" href="/citations?view_op=view_citation&amp;citation_for_view=A:B">AI &amp; Society</a>
          <div class="gs_gray">A Person, B Person</div><div class="gs_gray">A Journal, 2025</div></td>
          <td class="gsc_a_y"><span>2025</span></td></tr></table>'''
        rows = sync.scholar_rows(text)
        self.assertEqual(rows[0]["title"], "AI & Society")
        self.assertEqual(rows[0]["url"], "https://scholar.google.com/citations?view_op=view_citation&citation_for_view=A:B")
        with self.assertRaises(ValueError):
            sync.scholar_rows("<h1>Verify you are human</h1>")

    def test_scholar_details_preserve_chinese_authors_and_year_precision(self):
        text = '''<div id="gsc_oci_title"><a href="https://doi.org/10.1234/example">A <i>Paper</i></a></div>
          <div class="gs_scl"><div class="gsc_oci_field">Authors</div><div class="gsc_oci_value">张三， 蒋卓人</div></div>
          <div class="gs_scl"><div class="gsc_oci_field">Publication date</div><div class="gsc_oci_value">2026</div></div>
          <div class="gs_scl"><div class="gsc_oci_field">Source</div><div class="gsc_oci_value">学术期刊</div></div>'''
        row = {"title": "A Paper", "year": "2026", "venue": "", "url": "https://scholar.google.com/citations?view_op=view_citation&citation_for_view=A:B"}
        paper = sync.scholar_detail(text, row, "蒋卓人", TODAY, 3)
        self.assertEqual(paper["authors"], ["张三", "蒋卓人"])
        self.assertEqual(paper["date_precision"], "year")
        self.assertEqual(paper["venue"], "学术期刊")
        self.assertEqual(paper["doi"], "10.1234/example")
        self.assertIsNone(sync.scholar_detail(text.replace("2026", "2027"), row, "蒋卓人", TODAY, 3))

    def test_scholar_only_source_can_sync_without_crossref(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("- 甲 https://scholar.google.com/citations?user=ABC\n")
            row = {"title": "A paper", "year": "2026", "venue": "Journal", "url": "https://scholar.google.com/citations?citation_for_view=ABC:A"}
            with patch.object(sync, "fetch_scholar", return_value=[row]), patch.object(sync.Client, "get_text", return_value="fixture"), patch.object(sync, "scholar_detail", return_value=record()):
                sync.main(["--source", str(source), "--papers-dir", str(root / "papers"), "--people-data", str(root / "people.yml"), "--report", str(root / "report.json"), "--write"])
            self.assertEqual(len(list((root / "papers").glob("*.md"))), 1)
            self.assertIn("user=ABC", (root / "people.yml").read_text())

    def test_scholar_title_does_not_override_conflicting_orcid(self):
        item = {"author": [{"given": "Pengwei", "family": "Yan", "ORCID": "https://orcid.org/WRONG"}]}
        self.assertFalse(sync.identity_matches(item, "Pengwei Yan", {"orcid": "RIGHT"}, known_title=True))

    def test_a_failed_source_never_partially_writes_site_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); sources = root / "source.md"; papers = root / "papers"
            sources.write_text('- 甲 https://api.crossref.org/works?query.author=Given%20One\n- 乙 https://api.crossref.org/works?query.author=Given%20Two\n```yaml\nidentities:\n  甲: {coauthors: [Known Person]}\n  乙: {coauthors: [Known Person]}\n```\n')
            with patch.object(sync, "fetch_crossref", side_effect=[([record()], {"matched": 1, "candidates": 1}), ValueError("rate limited")]):
                with self.assertRaises(ValueError):
                    sync.main(["--source", str(sources), "--papers-dir", str(papers), "--people-data", str(root / "people.yml"), "--report", str(root / "report.json"), "--write"])
            self.assertFalse(papers.exists())
            self.assertFalse((root / "people.yml").exists())


if __name__ == "__main__":
    unittest.main()
