# Security Review

**Review date:** 2026-05-25

This fork was reviewed locally before publishing. The review focused on obvious
secret exposure, repository-specific branding, tracking identifiers, and common
agent-skill risk patterns.

## Summary

- No real GitHub tokens, private keys, or OpenAI-style production secrets were
  found in repository files.
- Several fake tokens remain in `academic-skills/autoskill/tests/`; they are
  test fixtures used to verify redaction behavior.
- Many skills contain examples that install packages, call external APIs, read
  API keys from environment variables, or launch subprocesses. That is expected
  for this type of repository, but individual skills should still be reviewed
  before installation.
- The Exa search skill previously used a repository-specific integration header.
  This fork removes that header and the matching documentation/test assertion.
- Upstream organization-specific promotion, social links, install paths, and
  skill metadata were removed where practical.
- The MIT license file keeps the original copyright notice because preserving
  that notice is required for redistribution.

## Notable Risk Patterns

### External API Keys

Some skills read environment variables such as `EXA_API_KEY`,
`OPENROUTER_API_KEY`, `HF_TOKEN`, or service-specific credentials and send them
to the corresponding third-party API. This is normal for authenticated API use,
but users should understand which service receives each key.

### Unpinned Dependencies

Many examples use commands such as `pip install package-name` or
`uv pip install package-name` without version pins. For reproducible or
enterprise use, pin versions and prefer lockfiles or hashes.

### Shell Execution

Several skills include shell commands, subprocess calls, Docker commands,
LibreOffice automation, or examples using elevated system package managers.
Review these before running them on a workstation with sensitive files.

### Network Access

Database lookup, literature search, web search, model download, and cloud-lab
integration skills make outbound requests by design. Use a restricted network
environment when testing unfamiliar skills.

## Recommended Pre-Install Review

For any skill you plan to use:

1. Read the skill's `SKILL.md`.
2. Inspect any `scripts/`, `references/`, `assets/`, and `tests/` files.
3. Search for credential handling:

```bash
rg -n -i "(api[_-]?key|secret|token|password|bearer)" academic-skills/<skill>
```

4. Search for command execution and installation paths:

```bash
rg -n -i "(subprocess|os\.system|eval\(|exec\(|curl |wget |pip install|uv pip install|sudo)" academic-skills/<skill>
```

5. Run a scanner if the skill will be used in a sensitive environment:

```bash
uv pip install cisco-ai-skill-scanner
skill-scanner scan academic-skills/<skill> --use-behavioral
```

## Publishing Notes

Before pushing future updates:

- Run a secret scan.
- Check for repository-specific attribution or tracking strings.
- Confirm generated docs do not point users at obsolete install paths.
- Keep license notices intact.
