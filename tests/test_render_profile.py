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

    def test_typing_cursor_moves_with_each_revealed_character(self) -> None:
        svg = render_svg(self.data)
        root = ET.fromstring(svg)
        ns = "{http://www.w3.org/2000/svg}"
        clip_animations: dict[float, object] = {}

        for clip_path in root.iter(f"{ns}clipPath"):
            clip_rect = clip_path.find(f"{ns}rect")
            if clip_rect is None:
                continue
            animation = next(
                (child for child in clip_rect
                 if child.tag == f"{ns}animate" and child.attrib.get("attributeName") == "width"),
                None,
            )
            if animation is not None:
                clip_animations[float(clip_rect.attrib["y"])] = animation

        cursor_rects = []
        for rect in root.iter(f"{ns}rect"):
            children = list(rect)
            x_animation = next(
                (child for child in children
                 if child.tag == f"{ns}animate" and child.attrib.get("attributeName") == "x"),
                None,
            )
            if x_animation is not None:
                cursor_rects.append((rect, children, x_animation))

        command_count = sum(row["kind"] == "command" for row in build_rows(self.data))
        self.assertEqual(len(cursor_rects), command_count)
        self.assertEqual(len(clip_animations), command_count)

        for rect, children, x_animation in cursor_rects:
            self.assertEqual(rect.attrib.get("visibility"), "hidden")
            self.assertTrue(any(
                child.tag == f"{ns}set"
                and child.attrib.get("attributeName") == "visibility"
                and child.attrib.get("to") == "visible"
                for child in children
            ))
            self.assertEqual(x_animation.attrib.get("calcMode"), "discrete")
            self.assertIsNone(x_animation.attrib.get("from"))
            self.assertTrue(any(
                child.tag == f"{ns}animate"
                and child.attrib.get("attributeName") == "opacity"
                and child.attrib.get("repeatCount") == "indefinite"
                and child.attrib.get("dur") == "0.3s"
                for child in children
            ))

            clip_y = float(rect.attrib["y"]) - 3
            width_animation = clip_animations[clip_y]
            self.assertEqual(width_animation.attrib.get("calcMode"), "discrete")
            self.assertEqual(x_animation.attrib.get("keyTimes"), width_animation.attrib.get("keyTimes"))
            self.assertEqual(x_animation.attrib.get("begin"), width_animation.attrib.get("begin"))
            self.assertEqual(x_animation.attrib.get("dur"), width_animation.attrib.get("dur"))

            widths = [float(value) for value in width_animation.attrib["values"].split(";")]
            positions = [float(value) for value in x_animation.attrib["values"].split(";")]
            self.assertEqual(len(positions), len(widths))
            for width, position in zip(widths, positions):
                self.assertAlmostEqual(position, 49 + width, places=3)

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
        self.assertIn("## NuGet packages", markdown)
        self.assertIn("Browse my published packages on [my NuGet profile](https://www.nuget.org/profiles/Urem).", markdown)

    def test_dynamic_text_is_xml_escaped(self) -> None:
        data = json.loads(json.dumps(self.data))
        data["profile"]["name"] = "Example <Developer> & Tester"
        svg = render_svg(data)
        ET.fromstring(svg)
        self.assertIn("&lt;Developer&gt; &amp; Tester", svg)

    def test_invalid_nuget_profile_url_is_rejected(self) -> None:
        data = json.loads(json.dumps(self.data))
        data["profile"]["nuget_url"] = "javascript:alert(1)"
        with self.assertRaisesRegex(ValueError, "profile.nuget_url"):
            render_svg(data)

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


    def test_checked_in_svg_matches_generator(self) -> None:
        generated = render_svg(self.data)
        checked_in = (ROOT / "assets" / "terminal.svg").read_text(encoding="utf-8")
        self.assertEqual(checked_in, generated)


if __name__ == "__main__":
    unittest.main()
