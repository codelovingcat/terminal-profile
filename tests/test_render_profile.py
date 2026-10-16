from __future__ import annotations

import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.render_profile import load_profile, render_links_markdown, render_svg

ROOT = Path(__file__).resolve().parents[1]


class RenderProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = load_profile(ROOT / "data" / "profile.json")

    def test_default_config_contains_priority_projects(self) -> None:
        names = [item["name"] for item in self.data["projects"]]
        self.assertEqual(names, ["Conversa", "Backend Safety Kit"])

    def test_svg_is_valid_xml_and_has_terminal_accessibility_metadata(self) -> None:
        svg = render_svg(self.data)
        root = ET.fromstring(svg)
        self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}title"))
        self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}desc"))
        self.assertIn("REC", svg)
        self.assertIn("animate", svg)

    def test_svg_includes_interests_projects_learning_and_plan(self) -> None:
        svg = render_svg(self.data)
        for expected in (
            "Ürem Sancaktutan",
            "Senior Full Stack Developer",
            "Backend engineering",
            "Conversa",
            "Backend Safety Kit",
            "AI-assisted development workflows",
            "Move Conversa closer to a usable product",
        ):
            self.assertIn(expected, svg)
        self.assertNotIn("github-snake-remix", svg.lower())

    def test_generated_markdown_links_use_configured_urls(self) -> None:
        markdown = render_links_markdown(self.data)
        self.assertIn("https://github.com/codelovingcat/AI-Powered-Real-Time-Conversation-Assistant", markdown)
        self.assertIn("https://github.com/codelovingcat/Backend-Safety-Kit", markdown)
        self.assertIn("NuGet listing pending confirmation", markdown)

    def test_dynamic_text_is_xml_escaped(self) -> None:
        data = json.loads(json.dumps(self.data))
        data["profile"]["name"] = "Example <Developer> & Tester"
        svg = render_svg(data)
        ET.fromstring(svg)
        self.assertIn("&lt;Developer&gt; &amp; Tester", svg)

    def test_invalid_project_url_is_rejected(self) -> None:
        data = json.loads(json.dumps(self.data))
        data["projects"][0]["url"] = "javascript:alert(1)"
        with self.assertRaises(ValueError):
            render_svg(data)

    def test_config_loader_reports_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Invalid JSON"):
                load_profile(path)


if __name__ == "__main__":
    unittest.main()
