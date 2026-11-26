from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from src import research as r


def candidate(index=1, repo="a/runtime"):
    url = f"https://github.com/{repo}/releases/tag/v{index}"
    return {"id": r.stable_id(url), "kind": "release", "title": f"v{index}", "url": url,
            "repo": repo, "tag": f"v{index}", "published": "2026-01-02T00:00:00Z", "text": "runtime update", "score": 10}


def analysis():
    return {"title": "运行时技术拆解", "sections": {key: [{
        "text": "基于有限证据，本段仅解释已提供的机制边界，未进行实际验证。" * 5,
        "evidence_type": "设计建议" if key == "practice" else "源码推断", "sources": ["S1"]
    }] for key in r.SECTION_KEYS}}


class Tests(unittest.TestCase):
    def test_stable_id(self):
        self.assertEqual(r.stable_id("x"), r.stable_id("x"))
        self.assertNotEqual(r.stable_id("x"), r.stable_id("y"))

    def test_timezone_boundary(self):
        moment = r.parse_time("2026-01-01T23:15:00Z")
        self.assertEqual(moment.astimezone(r.ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M"), "2026-01-02 07:15")

    def test_diversity_and_dedup(self):
        a, b, c = candidate(1), candidate(2), candidate(3, "b/agent")
        self.assertEqual(r.select_topics([a, b, c], set(), 2), [a, c])
        self.assertEqual(r.select_topics([a, b, c], {a["id"]}, 2), [b, c])

    def test_numbered_excerpt(self):
        text, covered, total = r.numbered("aa\nbb\ncc", 12)
        self.assertEqual((text, covered, total), ("1: aa\n2: bb\n", 2, 3))

    def test_valid_analysis(self):
        r.validate_analysis(analysis(), [{"id": "S1"}])

    def test_invalid_reference(self):
        value = analysis()
        value["sections"]["problem"][0]["sources"] = ["S99"]
        with self.assertRaises(ValueError):
            r.validate_analysis(value, [{"id": "S1"}])

    def test_no_links_or_html(self):
        for text in ("https://evil.example", "<img src=x>", "[x](evil)", "```bash"):
            value = analysis()
            value["sections"]["flow"][0]["text"] = text
            with self.assertRaises(ValueError):
                r.validate_analysis(value, [{"id": "S1"}])

    def test_reproduction_not_executed(self):
        value = analysis()
        value["sections"]["practice"][0]["evidence_type"] = "事实"
        with self.assertRaises(ValueError):
            r.validate_analysis(value, [{"id": "S1"}])

    def test_missing_section(self):
        value = analysis()
        del value["sections"]["limits"]
        with self.assertRaises(ValueError):
            r.validate_analysis(value, [{"id": "S1"}])

    def test_full_requires_credentials(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                r.run(Path(temp), {"timezone": "Asia/Shanghai"}, "full", datetime.now(timezone.utc))

    def test_run_idempotent_and_upgrade(self):
        cfg = {"timezone": "Asia/Shanghai", "lookback_hours": 72, "repositories": ["a/runtime"], "max_daily_topics": 2}
        now = r.parse_time("2026-01-02T00:00:00Z")
        c = candidate()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(r, "collect", return_value=([c], [])) as collect:
                r.run(root, cfg, "collect", now)
                r.run(root, cfg, "collect", now)
                self.assertEqual(collect.call_count, 1)
                self.assertEqual(json.loads((root / "data/state.json").read_text())["seen"], [])
                with patch.dict(os.environ, {"LLM_API_KEY": "unit-test-placeholder", "LLM_MODEL": "test-model"}), \
                     patch.object(r, "evidence_for", return_value=([{"id": "S1", "url": c["url"], "title": "release"}], [])), \
                     patch.object(r, "analyze", return_value=(analysis(), {"total_tokens": 10})):
                    r.run(root, cfg, "full", now)
                    r.run(root, cfg, "full", now)
                self.assertEqual(collect.call_count, 2)
                self.assertEqual(json.loads((root / "data/state.json").read_text())["seen"], [c["id"]])
                self.assertIn("运行时技术拆解", (root / "research/2026/01/2026-01-02.md").read_text())

    def test_failed_analysis_does_not_publish(self):
        cfg = {"timezone": "Asia/Shanghai", "lookback_hours": 72, "repositories": ["a/runtime"], "max_daily_topics": 2}
        with tempfile.TemporaryDirectory() as temp, \
             patch.dict(os.environ, {"LLM_API_KEY": "unit-test-placeholder", "LLM_MODEL": "test-model"}), \
             patch.object(r, "collect", return_value=([candidate()], [])), \
             patch.object(r, "evidence_for", return_value=([{"id": "S1"}], [])), \
             patch.object(r, "analyze", side_effect=ValueError("invalid")):
            with self.assertRaises(ValueError):
                r.run(Path(temp), cfg, "full", r.parse_time("2026-01-02T00:00:00Z"))
            self.assertFalse((Path(temp) / "data/state.json").exists())
            self.assertFalse((Path(temp) / "research/2026/01/2026-01-02.md").exists())

    def test_all_sources_failed(self):
        cfg = {"timezone": "Asia/Shanghai", "repositories": ["a/runtime"]}
        with tempfile.TemporaryDirectory() as temp, patch.object(r, "collect", return_value=([], ["repo", "arxiv"])):
            with self.assertRaises(RuntimeError):
                r.run(Path(temp), cfg, "collect", r.parse_time("2026-01-02T00:00:00Z"))

    def test_render_has_traceable_references(self):
        c = candidate()
        text = r.render_topic(c, [{"id": "S1", "url": c["url"], "title": "release"}], [], analysis())
        self.assertIn(f"[S1](#{c['id']}-s1)", text)
        self.assertIn("实验建议未执行", text)


if __name__ == "__main__":
    unittest.main()
