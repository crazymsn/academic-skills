#!/usr/bin/env python3
"""Validate Academic Skills compatibility across common agent skill loaders."""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", re.S)
PORTABLE_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}


@dataclass
class SkillInfo:
    path: Path
    directory: str
    name: str | None
    description: str | None
    keys: set[str]


@dataclass
class Issue:
    level: str
    path: Path | None
    message: str


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_frontmatter(text: str, path: Path) -> tuple[dict[str, str], set[str]]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("missing YAML frontmatter delimited by ---")

    lines = match.group(1).splitlines()
    data: dict[str, str] = {}
    keys: set[str] = set()
    index = 0

    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        if line[0].isspace() or ":" not in line:
            index += 1
            continue

        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        keys.add(key)

        if value in {">", "|", ">-", "|-", ">+", "|+"}:
            block_lines: list[str] = []
            index += 1
            while index < len(lines):
                next_line = lines[index]
                if next_line and not next_line[0].isspace() and ":" in next_line:
                    break
                block_lines.append(next_line.strip())
                index += 1
            data[key] = " ".join(part for part in block_lines if part) if value.startswith(">") else "\n".join(block_lines).strip()
            continue

        data[key] = strip_quotes(value) if value else ""
        index += 1

    return data, keys


def load_skill(path: Path) -> SkillInfo:
    data, keys = parse_frontmatter(path.read_text(encoding="utf-8"), path)
    return SkillInfo(path=path, directory=path.parent.name, name=data.get("name"), description=data.get("description"), keys=keys)


def iter_skill_files(root: Path, selected: set[str] | None = None) -> list[Path]:
    if not root.exists():
        return []
    files = sorted(root.glob("*/SKILL.md"))
    if not selected:
        return files
    result: list[Path] = []
    for path in files:
        if path.parent.name in selected:
            result.append(path)
            continue
        try:
            info = load_skill(path)
        except Exception:
            continue
        if info.name in selected:
            result.append(path)
    return result


def validate_skill(info: SkillInfo, strict_unknown: bool = False) -> list[Issue]:
    issues: list[Issue] = []
    if not info.name:
        issues.append(Issue("error", info.path, "missing required frontmatter field: name"))
    else:
        if len(info.name) > 64:
            issues.append(Issue("error", info.path, f"name is {len(info.name)} characters; max is 64"))
        if not NAME_RE.fullmatch(info.name):
            issues.append(Issue("error", info.path, "name must match ^[a-z0-9]+(-[a-z0-9]+)*$"))
        if info.name != info.directory:
            issues.append(Issue("error", info.path, f"name {info.name!r} does not match directory {info.directory!r}"))

    if not info.description:
        issues.append(Issue("error", info.path, "missing required frontmatter field: description"))
    elif len(info.description) > 1024:
        issues.append(Issue("error", info.path, f"description is {len(info.description)} characters; max is 1024"))

    for key in sorted(info.keys - PORTABLE_FIELDS):
        level = "error" if strict_unknown else "warning"
        issues.append(Issue(level, info.path, f"non-portable frontmatter field: {key}"))
    return issues


def validate_repository(root: Path, selected: set[str] | None, strict_unknown: bool) -> tuple[list[SkillInfo], list[Issue]]:
    issues: list[Issue] = []
    skills: list[SkillInfo] = []
    files = iter_skill_files(root, selected)
    if not files:
        issues.append(Issue("error", root, "no skill directories with SKILL.md were found"))
        return skills, issues

    seen: dict[str, Path] = {}
    for path in files:
        try:
            info = load_skill(path)
        except Exception as exc:
            issues.append(Issue("error", path, str(exc)))
            continue
        skills.append(info)
        issues.extend(validate_skill(info, strict_unknown=strict_unknown))
        if info.name:
            previous = seen.get(info.name)
            if previous:
                issues.append(Issue("error", path, f"duplicate skill name {info.name!r}; first seen at {previous}"))
            else:
                seen[info.name] = path

    if selected:
        available = {info.directory for info in skills} | {info.name for info in skills if info.name}
        for name in sorted(selected - available):
            issues.append(Issue("error", root, f"requested skill {name!r} was not found"))
    return skills, issues


def xdg_config_home() -> Path:
    raw = os.environ.get("XDG_CONFIG_HOME")
    return Path(raw).expanduser() if raw else Path.home() / ".config"


def known_agent_paths(agent: str, scope: str, cwd: Path) -> list[Path]:
    home = Path.home()
    project_paths = {
        "claude": [cwd / ".claude" / "skills"],
        "codex": [cwd / ".agents" / "skills"],
        "opencode": [cwd / ".opencode" / "skills", cwd / ".agents" / "skills", cwd / ".claude" / "skills"],
    }
    global_paths = {
        "claude": [Path(os.environ.get("CLAUDE_CONFIG_DIR", home / ".claude")) / "skills"],
        "codex": [Path(os.environ.get("CODEX_HOME", home / ".codex")) / "skills", home / ".agents" / "skills"],
        "opencode": [xdg_config_home() / "opencode" / "skills", home / ".agents" / "skills", home / ".claude" / "skills"],
    }
    paths: list[Path] = []
    if scope in {"project", "all"}:
        paths.extend(project_paths[agent])
    if scope in {"global", "all"}:
        paths.extend(global_paths[agent])
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        path = path.expanduser()
        if path not in seen:
            seen.add(path)
            deduped.append(path)
    return deduped


def validate_installation(agent: str, scope: str, cwd: Path, expected_names: set[str], strict_unknown: bool) -> list[Issue]:
    issues: list[Issue] = []
    paths = known_agent_paths(agent, scope, cwd)
    discovered: dict[str, Path] = {}
    for base in paths:
        if not base.exists():
            continue
        for skill_file in sorted(base.glob("*/SKILL.md")):
            try:
                info = load_skill(skill_file)
            except Exception as exc:
                issues.append(Issue("error", skill_file, str(exc)))
                continue
            issues.extend(validate_skill(info, strict_unknown=strict_unknown))
            if info.name:
                discovered.setdefault(info.name, skill_file)

    missing = sorted(expected_names - set(discovered))
    if missing:
        checked = ", ".join(str(path) for path in paths)
        sample = ", ".join(missing[:10])
        suffix = "" if len(missing) <= 10 else f", ... ({len(missing)} total)"
        issues.append(Issue("error", None, f"{agent} {scope} install is missing: {sample}{suffix}. Checked: {checked}"))
    return issues


def print_issues(issues: list[Issue]) -> None:
    for issue in issues:
        location = f"{issue.path}: " if issue.path else ""
        print(f"{issue.level.upper()}: {location}{issue.message}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Academic Skills compatibility.")
    parser.add_argument("--skills-root", default="academic-skills", help="Repository skill directory root.")
    parser.add_argument("--skill", action="append", default=[], help="Limit checks to one skill name. Repeat as needed.")
    parser.add_argument("--agent", choices=["claude", "codex", "opencode", "all"], help="Also verify installed skill locations.")
    parser.add_argument("--scope", choices=["project", "global", "all"], default="all", help="Install scope to inspect with --agent.")
    parser.add_argument("--strict-unknown", action="store_true", help="Treat non-portable frontmatter fields as errors.")
    args = parser.parse_args()

    selected = set(args.skill) if args.skill else None
    skills, issues = validate_repository(Path(args.skills_root), selected, args.strict_unknown)
    expected_names = {info.name for info in skills if info.name}

    agents: list[str] = []
    if args.agent == "all":
        agents = ["claude", "codex", "opencode"]
    elif args.agent:
        agents = [args.agent]
    for agent in agents:
        issues.extend(validate_installation(agent, args.scope, Path.cwd(), expected_names, args.strict_unknown))

    print(f"Checked {len(skills)} repository skill(s).")
    if agents:
        print(f"Checked installed locations for: {', '.join(agents)} ({args.scope}).")
    print_issues(issues)

    error_count = sum(1 for issue in issues if issue.level == "error")
    warning_count = sum(1 for issue in issues if issue.level == "warning")
    if error_count:
        print(f"FAIL: {error_count} error(s), {warning_count} warning(s).")
        return 1
    print(f"OK: no compatibility errors ({warning_count} warning(s)).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
