from __future__ import annotations

import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.render_profile import build_rows, load_profile, render_links_markdown, render_svg

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

    def test_typing_cursor_follows_each_command_and_hides_afterward(self) -> None:
        svg = render_svg(self.data)
        root = ET.fromstring(svg)
        ns = "{http://www.w3.org/2000/svg}"
        cursor_rects = []

        for rect in root.iter(f"{ns}rect"):
            children = list(rect)
            if any(
                child.tag == f"{ns}animate" and child.attrib.get("attributeName") == "x"
                for child in children
            ):
                cursor_rects.append((rect, children))

        command_count = sum(row["kind"] == "command" for row in build_rows(self.data))
        self.assertEqual(len(cursor_rects), command_count)

        for rect, children in cursor_rects:
            self.assertEqual(rect.attrib.get("visibility"), "hidden")
            self.assertTrue(any(
                child.tag == f"{ns}set"
                and child.attrib.get("attributeName") == "visibility"
                and child.attrib.get("to") == "visible"
                for child in children
            ))
            x_animation = next(
                child for child in children
                if child.tag == f"{ns}animate" and child.attrib.get("attributeName") == "x"
            )
            self.assertEqual(x_animation.attrib.get("from"), "49")
            self.assertEqual(x_animation.attrib.get("calcMode"), "linear")
            opacity_animation = next(
                child for child in children
                if child.tag == f"{ns}animate" and child.attrib.get("attributeName") == "opacity"
            )
            self.assertEqual(opacity_animation.attrib.get("repeatCount"), "indefinite")

        # Keep the original blinking prompt cursor at the end of the animation.
        self.assertIn('values="1;0" calcMode="discrete" dur="1s"', svg)

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
