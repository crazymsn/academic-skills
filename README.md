# Academic Skills

Academic Skills is a curated collection of agent skills for research, science,
engineering, analysis, finance, writing, and scientific communication.

This repository is prepared as a neutral fork of an open-source Agent Skills
collection. It keeps the reusable skill content and removes upstream
organization-specific promotion, install paths, and integration tracking.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)
[![Agent Skills](https://img.shields.io/badge/Standard-Agent_Skills-blueviolet.svg)](https://agentskills.io/)

## What Is Included

This snapshot contains 139 skill directories under `scientific-skills/`.

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

Install the full collection with an Agent Skills-compatible tool:

```bash
npx skills add crazymsn/academic-skills
```

If you use GitHub CLI skill support:

```bash
gh skill install crazymsn/academic-skills
gh skill install crazymsn/academic-skills scanpy
gh skill install crazymsn/academic-skills --agent codex
```

You can also install or copy individual directories from `scientific-skills/`
into your agent's local skills directory.

## Security Notes

Skills can influence an AI coding agent to run commands, install packages, make
network requests, read environment variables, or modify files. Review each skill
before installing it, especially if it includes scripts, shell commands,
third-party API calls, or unpinned dependency installation instructions.

A local review for this fork is summarized in [SECURITY.md](SECURITY.md).

To run your own scan:

```bash
uv pip install cisco-ai-skill-scanner
skill-scanner scan scientific-skills --use-behavioral
```

## Repository Layout

```text
scientific-skills/      Skill directories
docs/                   Generated indexes and ecosystem notes
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
