# Editing profile content

Edit `data/profile.json` to update the generated terminal panel. The renderer reads the configuration and regenerates `assets/terminal.svg` and `docs/generated-links.md`.

- `profile.name`, `headline`, and `tagline` define the intro.
- `profile.interests` lists your technical focus areas.
- `projects` is deliberately curated. Keep only projects worth featuring; the current priority is Conversa and Backend Safety Kit.
- `packages` stores package metadata and links. `package_url` can stay `null` until a package is confirmed published; `source_url` and `release_url` can still point to the source and preview release.
- `profile.learning` and `profile.plan` can be updated without changing renderer code.

Use only public repository/package URLs in this public profile. Do not add secrets, internal URLs, private repository details, or personal data that should not be public.

## Current package publication status

Backend Safety Kit has a GitHub preview release. A NuGet gallery URL should be added to `package_url` only after the package page is confirmed live. Until then, the profile points readers to the source and preview release instead of pretending that package installation from NuGet is already available.

## Local workflow

    python scripts/render_profile.py
    python -m unittest discover -s tests -v

The generated SVG is `assets/terminal.svg`. On GitHub, use regular Markdown links below the image for reliable navigation to repositories and package pages; SVG hotspots are not relied on for project links.
