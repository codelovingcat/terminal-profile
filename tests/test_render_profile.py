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

    def test_default_config_hides_projects_packages_and_future_plans(self) -> None:
        self.assertEqual(self.data["projects"], [])
        self.assertEqual(self.data["packages"], [])
        self.assertEqual(self.data["profile"]["plan"], [])

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

    def test_svg_keeps_intro_interests_and_learning_only(self) -> None:
        svg = render_svg(self.data)
        for expected in (
            "Ürem Sancaktutan",
            "Senior Full Stack Developer",
            "Backend engineering",
            "AI-assisted development workflows",
            "Reusable backend safety infrastructure",
        ):
            self.assertIn(expected, svg)
        for unwanted in (
            "Conversa",
            "Backend Safety Kit",
            "BackendSafetyKit",
            "nuget",
            "NuGet",
            "featured",
            ".plan",
            "Move Conversa closer",
            "selected projects",
            "package information",
            "and plans",
        ):
            self.assertNotIn(unwanted.lower(), svg.lower())
        self.assertNotIn("github-snake-remix", svg.lower())

    def test_generated_markdown_omits_empty_project_and_package_sections(self) -> None:
        markdown = render_links_markdown(self.data)
        self.assertNotIn("Featured projects", markdown)
        self.assertNotIn("Package links", markdown)
        self.assertNotIn("NuGet", markdown)
        self.assertNotIn("Conversa", markdown)
        self.assertNotIn("Backend Safety Kit", markdown)

    def test_optional_project_and_package_sections_can_be_enabled_explicitly(self) -> None:
        data = json.loads(json.dumps(self.data))
        data["projects"] = [{
            "name": "Example Project",
            "description": "A sample app",
            "url": "https://example.com/project",
        }]
        data["packages"] = [{
            "name": "ExamplePackage",
            "description": "A sample package",
            "status": "preview",
            "source_url": "https://example.com/source",
            "release_url": None,
            "package_url": None,
        }]
        markdown = render_links_markdown(data)
        self.assertIn("## Featured projects", markdown)
        self.assertIn("## Package links", markdown)
        self.assertIn("https://example.com/project", markdown)

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
