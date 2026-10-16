# Terminal Profile

**An animated, terminal-style showcase for a developer's GitHub profile.**

Terminal Profile is a small project for turning a GitHub profile README into a more personal developer portfolio. It uses a dark terminal aesthetic, animated command/output lines, and a blinking `REC` indicator to introduce the developer, highlight selected projects and packages, and share what they're learning or planning next.

The goal is to make a profile feel like a tiny terminal session—not to build a large framework or a full website.

> **Status:** Project bootstrapped; implementation is planned. The roadmap below describes the intended features, not features that are already available.

## What it is intended to show

A generated terminal panel could look something like this:

```text
● ● ●                                      urem@github: ~  ● REC

$ whoami
Ürem Sancaktutan
Senior Full Stack Developer · .NET · React · AI

$ ls ~/projects --featured
Conversa             AI-powered conversation assistant
Backend-Safety-Kit   Reusable backend safety utilities
github-snake-remix   Animated GitHub contribution snake
commit-man            Contribution-grid animation

$ cat ~/.learning
Exploring AI-assisted development and backend tooling.

$ cat ~/.plan
Build. Experiment. Ship. Repeat.

$
```

This is a **concept preview**, not generated output from the project yet. The final layout and content will be configurable.

## Planned features

- **Animated terminal SVG** — terminal window, sequentially revealed lines, blinking cursor, and animated `REC` indicator.
- **Featured repositories** — a curated selection of projects with short descriptions and repository links.
- **Package showcase** — links to published NuGet packages or other package pages, with source links where useful.
- **Learning now** — a concise list of topics currently being explored.
- **Next up / plan** — upcoming projects or goals that can be edited without changing rendering logic.
- **GitHub Actions** — a repeatable workflow to validate the configuration and regenerate the SVG.
- **README integration** — a documented snippet for adding the generated panel to a GitHub profile README.

For reliable navigation on GitHub, repository and package links may be displayed as Markdown links alongside or below the SVG instead of relying on interactive hotspots inside the SVG.

## How it is expected to work

1. Keep profile copy, featured repositories, package URLs, learning topics, and plans in a small configuration file.
2. Run a generator that validates this data and creates the SVG.
3. Preview the generated SVG and run tests.
4. Use GitHub Actions to regenerate the output when needed.
5. Embed the generated image in a profile README and keep supporting links easy to find.

The initial implementation should stay small and understandable. No database or hosted web application is required for the first version.

## Roadmap

- [ ] [#1 — Bootstrap README and define the project scope](https://github.com/codelovingcat/terminal-profile/issues/1)
- [ ] [#2 — Create the animated terminal SVG template](https://github.com/codelovingcat/terminal-profile/issues/2)
- [ ] [#3 — Add configurable featured repositories and package links](https://github.com/codelovingcat/terminal-profile/issues/3)
- [ ] [#4 — Add editable learning and next-plan sections](https://github.com/codelovingcat/terminal-profile/issues/4)
- [ ] [#5 — Automate SVG generation with GitHub Actions](https://github.com/codelovingcat/terminal-profile/issues/5)

## Design principles

- **Small and focused:** a profile asset generator, not a portfolio platform.
- **Config-first:** content should be editable without rewriting the renderer.
- **Safe by default:** escape dynamic text before putting it into SVG, validate URLs, and avoid secrets when public GitHub data is enough.
- **Readable without animation:** keep text meaningful when the SVG is viewed as a static image.
- **Honest status:** generated output and documentation should not imply that planned features are already implemented.

## Inspiration

The terminal animation and compact profile showcase are inspired by the visual approach in [kgarbacinski's GitHub profile](https://github.com/kgarbacinski/kgarbacinski), particularly its [animated terminal SVG](https://github.com/kgarbacinski/kgarbacinski/blob/main/assets/boot.svg). This project will adapt the general idea for a configurable personal project showcase.

## Current status

The repository currently contains the initial scope and roadmap. The first implementation task is the animated SVG template.
