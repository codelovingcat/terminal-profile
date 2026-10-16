#!/usr/bin/env python3
"""Render an animated, terminal-style SVG from data/profile.json."""
from __future__ import annotations

import argparse
import json
import textwrap
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "data" / "profile.json"
DEFAULT_OUTPUT = ROOT / "assets" / "terminal.svg"
DEFAULT_LINKS_OUTPUT = ROOT / "docs" / "generated-links.md"
WIDTH = 880
LEFT = 28
CHAR_WIDTH = 8.4
FONT_SIZE = 14
LINE_HEIGHT = 23
START_Y = 64
MAX_CHARS = 94


def _is_http_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"https", "http"} and bool(parsed.netloc)


def _validate_profile(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("Profile config must be a JSON object.")

    profile = data.get("profile")
    if not isinstance(profile, dict):
        raise ValueError("Config must contain a 'profile' object.")
    for field in ("name", "headline", "tagline"):
        if not isinstance(profile.get(field), str) or not profile[field].strip():
            raise ValueError(f"profile.{field} must be a non-empty string.")
    for field in ("interests", "learning", "plan"):
        values = profile.get(field, [])
        if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
            raise ValueError(f"profile.{field} must be a list of strings.")

    for collection_name in ("projects", "packages"):
        items = data.get(collection_name, [])
        if not isinstance(items, list):
            raise ValueError(f"{collection_name} must be a list.")
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f"{collection_name}[{index}] must be an object.")
            for required in ("name", "description"):
                if not isinstance(item.get(required), str) or not item[required].strip():
                    raise ValueError(f"{collection_name}[{index}].{required} must be a non-empty string.")
            for url_field in ("url", "source_url", "release_url", "package_url"):
                url = item.get(url_field)
                if url is not None and not _is_http_url(url):
                    raise ValueError(f"{collection_name}[{index}].{url_field} must be an HTTP(S) URL or null.")
    return data


def load_profile(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Profile config not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc.msg} at line {exc.lineno}") from exc
    return _validate_profile(data)


def _truncate(value: str, max_chars: int = MAX_CHARS) -> str:
    clean = " ".join(value.split())
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 1].rstrip() + "…"


def _text_element(x: float, y: int, text: str, color: str, *, size: int = FONT_SIZE,
                  weight: str | None = None, anchor: str | None = None, extra: str = "") -> str:
    truncated = _truncate(text, max_chars=MAX_CHARS)
    clean = escape(truncated, quote=False)
    estimated_width = len(truncated) * CHAR_WIDTH * size / FONT_SIZE
    attrs = [f'x="{x:.1f}"', f'y="{y}"', f'fill="{color}"', f'font-size="{size}"',
             f'textLength="{estimated_width:.1f}"', 'lengthAdjust="spacingAndGlyphs"']
    if weight:
        attrs.append(f'font-weight="{weight}"')
    if anchor:
        attrs.append(f'text-anchor="{anchor}"')
    return f'<text {" ".join(attrs)}{extra}>{clean}</text>'


def _wrap_lines(value: str) -> list[str]:
    value = " ".join(value.split())
    if not value:
        return []
    return textwrap.wrap(value, width=MAX_CHARS, break_long_words=True, break_on_hyphens=False) or [value]


def build_rows(data: dict[str, Any]) -> list[dict[str, str]]:
    profile = data["profile"]
    rows: list[dict[str, str]] = []

    def command(text: str) -> None:
        rows.append({"kind": "command", "text": text})

    def output(text: str, kind: str = "output") -> None:
        for line in _wrap_lines(text):
            rows.append({"kind": kind, "text": line})

    command("whoami")
    output(profile["name"], "name")
    output(f'{profile["headline"]}  |  {profile["tagline"]}')

    command("cat ~/.interests")
    for interest in profile.get("interests", []):
        output(f"> {interest}", "interest")

    command("ls ~/projects --featured")
    for project in data.get("projects", []):
        output(f'{project["name"]} — {project["description"]}', "project")

    packages = [p for p in data.get("packages", []) if p.get("status", "preview") != "hidden"]
    if packages:
        command("nuget list --featured")
        for package in packages:
            suffix = " · NuGet link pending publication" if not package.get("package_url") else " · NuGet"
            output(f'{package["name"]} — {package["description"]}{suffix}', "package")

    if profile.get("learning"):
        command("cat ~/.learning")
        for item in profile["learning"]:
            output(item, "learning")

    if profile.get("plan"):
        command("cat ~/.plan")
        for item in profile["plan"]:
            output(item, "plan")

    return rows


def render_svg(data: dict[str, Any]) -> str:
    rows = build_rows(_validate_profile(data))
    height = START_Y + len(rows) * LINE_HEIGHT + 38
    pieces: list[str] = []
    timeline = 0.4

    for index, row in enumerate(rows):
        y = START_Y + index * LINE_HEIGHT
        text = row["text"]
        if row["kind"] == "command":
            duration = max(0.38, min(2.3, len(text) * 0.035))
            clip_id = f"command-clip-{index}"
            # Use the same discrete character steps for both the text reveal and caret.
            # The textLength set by _text_element makes each character occupy CHAR_WIDTH.
            character_count = max(1, len(_truncate(text, max_chars=MAX_CHARS)))
            step_widths = [step * CHAR_WIDTH for step in range(character_count + 1)]
            width_values = ";".join(f"{width:.1f}" for width in step_widths)
            cursor_values = ";".join(f"{49 + width:.1f}" for width in step_widths)
            key_times = ";".join(f"{step / character_count:.5f}" for step in range(character_count + 1))
            end_width = max(CHAR_WIDTH, character_count * CHAR_WIDTH)
            pieces.append(
                f'<clipPath id="{clip_id}"><rect x="49" y="{y - 16}" width="0" height="19">'
                f'<animate attributeName="width" values="{width_values}" keyTimes="{key_times}" '
                f'calcMode="discrete" begin="{timeline:.2f}s" dur="{duration:.2f}s" '
                f'fill="freeze"/></rect></clipPath>'
            )
            pieces.append(
                f'<g opacity="0"><set attributeName="opacity" to="1" '
                f'begin="{timeline:.2f}s" fill="freeze"/>'
                + _text_element(LEFT, y, "$", "#00ff88", weight="700") + "</g>"
            )
            pieces.append(
                f'<g clip-path="url(#{clip_id})">'
                + _text_element(49, y, text, "#e6edf3", extra=f' aria-label="{escape(text, quote=True)}"')
                + "</g>"
            )
            # Share the text reveal's exact key times so the caret advances with each character.
            # Keep it blinking during typing, briefly at the command end, then hide before the next row.
            pieces.append(
                f'<rect x="49" y="{y - 13}" width="{CHAR_WIDTH:.1f}" height="16" '
                f'fill="#00ff88" visibility="hidden">'
                f'<set attributeName="visibility" to="visible" begin="{timeline:.2f}s" '
                f'dur="{duration + 0.12:.2f}s" fill="remove"/>'
                f'<animate attributeName="x" values="{cursor_values}" keyTimes="{key_times}" '
                f'calcMode="discrete" begin="{timeline:.2f}s" dur="{duration:.2f}s" fill="freeze"/>'
                f'<animate attributeName="opacity" values="1;0" calcMode="discrete" '
                f'dur="0.3s" begin="{timeline:.2f}s" repeatCount="indefinite"/>'
                '</rect>'
            )
            timeline += duration + 0.22
        else:
            if row["kind"] == "name":
                color, weight = "#00ff88", "700"
            elif row["kind"] == "project":
                color, weight = "#e6edf3", "700"
            elif row["kind"] == "package":
                color, weight = "#f5c26b", None
            elif row["kind"] in {"interest", "learning", "plan"}:
                color, weight = "#9da7b3", None
            else:
                color, weight = "#e6edf3", None
            pieces.append(
                f'<g opacity="0"><set attributeName="opacity" to="1" '
                f'begin="{timeline:.2f}s" fill="freeze"/>'
                + _text_element(LEFT, y, text, color, weight=weight) + "</g>"
            )
            timeline += 0.18

    prompt_y = START_Y + len(rows) * LINE_HEIGHT + 1
    pieces.append(
        f'<g opacity="0"><set attributeName="opacity" to="1" begin="{timeline:.2f}s" fill="freeze"/>'
        f'{_text_element(LEFT, prompt_y, "$", "#00ff88", weight="700")}'
        f'<rect x="49" y="{prompt_y - 13}" width="8.4" height="16" fill="#00ff88">'
        '<animate attributeName="opacity" values="1;0" calcMode="discrete" dur="1s" '
        f'begin="{timeline:.2f}s" repeatCount="indefinite"/></rect></g>'
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" aria-labelledby="title description">
<title id="title">Animated developer terminal profile</title>
<desc id="description">Terminal-style profile for {escape(data["profile"]["name"], quote=False)}, with interests, selected projects, package information, learning topics, and plans.</desc>
<defs>
  <linearGradient id="top-glow" x1="0" x2="1"><stop offset="0" stop-color="#00ff88" stop-opacity="0"/><stop offset=".5" stop-color="#00ff88" stop-opacity=".85"/><stop offset="1" stop-color="#00ff88" stop-opacity="0"/></linearGradient>
</defs>
<style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"DejaVu Sans Mono",monospace;white-space:pre}}</style>
<rect x="1" y="1" width="{WIDTH - 2}" height="{height - 2}" rx="14" fill="#0d1117" stroke="#1f3a2c" stroke-width="2"/>
<rect x="40" y="1" width="800" height="2" fill="url(#top-glow)"/>
<circle cx="26" cy="22" r="6" fill="#ff5f57"/><circle cx="46" cy="22" r="6" fill="#febc2e"/><circle cx="66" cy="22" r="6" fill="#28c840"/>
{_text_element(WIDTH / 2, 27, 'urem@github: ~', '#7d8590', anchor='middle')}
<g><circle cx="810" cy="22" r="4" fill="#ff3b3b"><animate attributeName="opacity" values="1;.25;1" dur="1.4s" repeatCount="indefinite"/></circle>
{_text_element(820, 27, 'REC', '#ff3b3b', weight='700')}</g>
<line x1="1" y1="40" x2="{WIDTH - 1}" y2="40" stroke="#1f3a2c"/>
{"".join(pieces)}
</svg>
'''


def render_links_markdown(data: dict[str, Any]) -> str:
    """Generate accessible Markdown links from the same validated config."""
    rows = [
        "<!-- Generated by scripts/render_profile.py. Edit data/profile.json instead. -->",
        "## Featured projects",
        "",
    ]
    for project in data.get("projects", []):
        name = project["name"].replace("\\", "\\\\").replace("]", "\\]")
        description = project["description"].replace("\n", " ")
        url = project.get("url")
        if url:
            rows.append(f'- [{name}]({url}) — {description}')
        else:
            rows.append(f"- **{name}** — {description}")

    packages = [p for p in data.get("packages", []) if p.get("status", "preview") != "hidden"]
    if packages:
        rows.extend(["", "## Package links", ""])
        for package in packages:
            name = package["name"].replace("\\", "\\\\").replace("]", "\\]")
            description = package["description"].replace("\n", " ")
            links: list[str] = []
            if package.get("package_url"):
                links.append(f'[NuGet]({package["package_url"]})')
            if package.get("source_url"):
                links.append(f'[source]({package["source_url"]})')
            if package.get("release_url"):
                links.append(f'[preview release]({package["release_url"]})')
            suffix = " · ".join(links) if links else "links not configured yet"
            if not package.get("package_url"):
                suffix += " · NuGet listing pending confirmation"
            rows.append(f'- **{name}** — {description} · {suffix}')

    return "\n".join(rows).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Path to profile JSON config")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output SVG path")
    parser.add_argument("--links-output", type=Path, default=DEFAULT_LINKS_OUTPUT, help="Output Markdown links path")
    args = parser.parse_args()

    try:
        data = load_profile(args.config)
        svg = render_svg(data)
        links = render_links_markdown(data)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(svg, encoding="utf-8")
    args.links_output.parent.mkdir(parents=True, exist_ok=True)
    args.links_output.write_text(links, encoding="utf-8")
    print(f"Generated {args.output} ({len(svg)} bytes)")
    print(f"Generated {args.links_output} ({len(links)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
