欢迎关注B站及YouTube频道：深度云创科技，感兴趣的朋友欢迎加入新时代智能体交流社群

客服微信：16773345788

# Academic Skills

Academic Skills is a curated collection of agent skills for research, science,
engineering, analysis, finance, writing, and scientific communication.

This repository is prepared as a neutral fork of an open-source Agent Skills
collection. It keeps the reusable skill content and removes upstream
organization-specific promotion, install paths, and integration tracking.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)
[![Agent Skills](https://img.shields.io/badge/Standard-Agent_Skills-blueviolet.svg)](https://agentskills.io/)

## What Is Included

This snapshot contains 139 skill directories under `academic-skills/`.

The collection covers:

- Bioinformatics, genomics, single-cell analysis, and multi-omics workflows
- Cheminformatics, drug discovery, molecular modeling, and protein engineering
- Scientific Python packages such as RDKit, Scanpy, scikit-learn, PyMC,
  NetworkX, Matplotlib, SymPy, Dask, Astropy, and many others
- Scientific databases and lookup workflows
- Geospatial science, remote sensing, materials science, physics, and astronomy
- Clinical research, treatment planning, regulatory writing, and medical imaging
- Literature review, peer review, scientific writing, posters, slides, diagrams,
  citation management, and document processing
- AI, machine learning, forecasting, reinforcement learning, and model
  interpretation workflows

Each skill usually includes a `SKILL.md` file plus optional examples, scripts,
references, assets, or tests.

## Getting Started

These instructions install the portable Agent Skills layer: each skill directory
contains a `SKILL.md` file plus optional `scripts/`, `references/`, `assets/`,
or `tests/` content. Agent-specific features such as Claude Code hooks,
subagent forks, dynamic shell injection, Codex plugin packaging, and OpenCode
permission policy are intentionally out of scope for this repository.

### Check Compatibility

Validate the repository before installing:

```bash
python scripts/validate_compat.py
```

Preview available skills without installing:

```bash
npx skills add crazymsn/academic-skills --list --full-depth
```

### Claude Code

Install every skill for Claude Code into the current project:

```bash
npx skills add crazymsn/academic-skills --skill '*' --agent claude-code --copy -y --full-depth
```

Install globally for the current user:

```bash
npx skills add crazymsn/academic-skills --skill '*' --agent claude-code --global --copy -y --full-depth
```

Claude Code project installs use `.claude/skills/`; user installs use
`~/.claude/skills/` unless `CLAUDE_CONFIG_DIR` points elsewhere.

Verify a project install:

```bash
python scripts/validate_compat.py --agent claude --scope project
```

### Codex

Install every skill for Codex into the current project:

```bash
npx skills add crazymsn/academic-skills --skill '*' --agent codex --copy -y --full-depth
```

Install globally for the current user:

```bash
npx skills add crazymsn/academic-skills --skill '*' --agent codex --global --copy -y --full-depth
```

Codex project installs use `.agents/skills/`. Depending on the Codex surface and
installer version, user installs may be read from `~/.agents/skills/` or
`~/.codex/skills/`; the compatibility checker inspects both.

Verify a project install:

```bash
python scripts/validate_compat.py --agent codex --scope project
```

### OpenCode

Install every skill for OpenCode into the current project:

```bash
npx skills add crazymsn/academic-skills --skill '*' --agent opencode --copy -y --full-depth
```

Install globally for the current user:

```bash
npx skills add crazymsn/academic-skills --skill '*' --agent opencode --global --copy -y --full-depth
```

OpenCode's native project path is `.opencode/skills/` and its native user path
is `~/.config/opencode/skills/`. It also reads compatible skills from
`.agents/skills/`, `.claude/skills/`, `~/.agents/skills/`, and
`~/.claude/skills/`; the `npx skills` installer currently targets the shared
`.agents/skills/` project path for OpenCode.

Verify a project install:

```bash
python scripts/validate_compat.py --agent opencode --scope project
```

### Install Selected Skills

Install one skill:

```bash
npx skills add crazymsn/academic-skills --skill scanpy --agent codex --copy -y --full-depth
```

Install several skills:

```bash
npx skills add crazymsn/academic-skills --skill scanpy anndata scvi-tools --agent codex --copy -y --full-depth
```

Verify selected skills:

```bash
python scripts/validate_compat.py --skill scanpy --skill anndata --skill scvi-tools
```

### Manual Install

You can also copy an individual directory from `academic-skills/` into an
agent's local skills directory. For example, copy `academic-skills/scanpy/` as
one complete skill directory.

## Security Notes

Skills can influence an AI coding agent to run commands, install packages, make
network requests, read environment variables, or modify files. Review each skill
before installing it, especially if it includes scripts, shell commands,
third-party API calls, or unpinned dependency installation instructions.

A local review for this fork is summarized in [SECURITY.md](SECURITY.md).

To run your own scan:

```bash
uv pip install cisco-ai-skill-scanner
skill-scanner scan academic-skills --use-behavioral
```

## Repository Layout

```text
academic-skills/      Skill directories
docs/                   Generated indexes and ecosystem notes
scripts/                Compatibility and install validation helpers
scan_skills.py          Security scan helper
scan_pr_skills.py       Pull-request scan helper
pyproject.toml          Python project metadata
uv.lock                 Locked Python dependency metadata
```

## Maintenance Checklist

- Review new or changed `SKILL.md` files before merging.
- Prefer pinned dependency versions for executable examples.
- Avoid hardcoded credentials, tokens, account identifiers, and tracking headers.
- Keep generated security reports current after large skill updates.
- Preserve required third-party license notices.

## License

This repository is distributed under the MIT License. See [LICENSE.md](LICENSE.md).

The original MIT copyright notice is intentionally retained in the license file,
as required when redistributing or modifying MIT-licensed software.
