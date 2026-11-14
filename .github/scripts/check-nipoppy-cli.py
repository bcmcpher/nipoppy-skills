#!/usr/bin/env python3
"""Check the nipoppy-cli skill against the installed Nipoppy CLI.

Every `nipoppy <subcommand> ... --flag` written in the skill's code (inline
code spans and fenced blocks) must name a real subcommand and a flag that
subcommand accepts. Every inline code span that is only a flag (e.g.
`--simulate`) must be a flag of some Nipoppy command.

The command tree comes from the click group behind the `nipoppy` console
script, which is also what renders `nipoppy <subcommand> -h`.

Usage:
    check-nipoppy-cli.py [--skill-dir DIR]     run the check
    check-nipoppy-cli.py --print-pin           print metadata.nipoppy-version

Exits 0 with a notice when the skill directory does not exist.
"""

import argparse
import re
import sys
from importlib.metadata import entry_points, version
from pathlib import Path

DEFAULT_SKILL = Path(__file__).resolve().parents[2] / "skills/nipoppy-cli"

# Flags that appear in the skill but belong to other tools.
NOT_NIPOPPY = {
    "--cleanenv",  # Apptainer argument, mentioned when switching to Docker
    "--account",  # Slurm directive that HPC_ACCOUNT_NAME maps to
    "-q",  # SGE directive that HPC_ACCOUNT_NAME maps to
}

PIN = re.compile(r'^\s+nipoppy-version:\s*"?([^"\s]+)"?\s*$', re.M)
FENCE = re.compile(r"```[^\n]*\n(.*?)```", re.S)
SPAN = re.compile(r"`([^`\n]+)`")
INVOCATION = re.compile(r"(?<![\w.-])nipoppy((?:[ \t]+[a-z][a-z-]*)*)")
FLAG = re.compile(r"(?<![\w-])(--?[A-Za-z][\w-]*)")
ONLY_FLAG = re.compile(r"^--?[A-Za-z][\w-]*$")
HELP = {"-h", "--help"}


def read_pin(skill_dir):
    manifest = skill_dir / "SKILL.md"
    frontmatter = manifest.read_text().split("---", 2)[1]
    match = PIN.search(frontmatter)
    return match.group(1) if match else None


def code_units(text):
    """Yield (line_number, text) for each fenced-block command and inline span."""
    for block in FENCE.finditer(text):
        start = text.count("\n", 0, block.start(1)) + 1
        logical, first = "", None
        for offset, line in enumerate(block.group(1).splitlines()):
            if first is None:
                first = start + offset
            logical += line.rstrip("\\") + " "
            if not line.rstrip().endswith("\\"):
                yield first, logical
                logical, first = "", None
    outside = FENCE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    for span in SPAN.finditer(outside):
        yield outside.count("\n", 0, span.start()) + 1, span.group(1)


def opts(command):
    names = set(HELP)
    for param in command.params:
        names.update(param.opts)
        names.update(param.secondary_opts)
    return names


def resolve(group, words):
    """Walk subcommand words down the click tree. Return (command, path, bad_word)."""
    command, path = group, ["nipoppy"]
    for word in words:
        sub = getattr(command, "commands", {}).get(word)
        if sub is None:
            # A bare word after a leaf command is an argument, not a subcommand.
            return command, path, word if hasattr(command, "commands") else None
        command, path = sub, path + [word]
    return command, path, None


def load_cli():
    """Load the object behind the `nipoppy` console script, whatever module holds it."""
    import click

    (entry,) = entry_points(group="console_scripts", name="nipoppy")
    cli = entry.load()
    if not isinstance(cli, click.Command):
        raise SystemExit(
            f"✘ {entry.value} is not a click command; this checker needs updating"
        )
    return cli


def check(skill_dir):
    cli = load_cli()

    every_flag = set()
    stack = [cli]
    while stack:
        command = stack.pop()
        every_flag |= opts(command)
        stack.extend(getattr(command, "commands", {}).values())

    problems, invocations = [], 0
    for md in sorted(skill_dir.rglob("*.md")):
        rel = md.relative_to(skill_dir)
        for lineno, unit in code_units(md.read_text()):
            if ONLY_FLAG.match(unit.strip()):
                flag = unit.strip()
                if flag not in every_flag and flag not in NOT_NIPOPPY:
                    problems.append(f"{rel}:{lineno}: {flag} is not a flag of any nipoppy command")
                continue
            matches = list(INVOCATION.finditer(unit))
            for i, match in enumerate(matches):
                words = match.group(1).split()
                if not words:
                    continue
                invocations += 1
                command, path, bad = resolve(cli, words)
                if bad:
                    problems.append(f"{rel}:{lineno}: '{' '.join(path)} {bad}' is not a subcommand")
                    continue
                if hasattr(command, "commands"):
                    continue  # a group named without a subcommand, e.g. `nipoppy pipeline`
                end = matches[i + 1].start() if i + 1 < len(matches) else len(unit)
                accepted = opts(command)
                for flag in FLAG.findall(unit[match.end():end]):
                    if flag not in accepted:
                        problems.append(f"{rel}:{lineno}: {' '.join(path)} has no option {flag}")

    for problem in problems:
        print(f"  ✘ {problem}")
    print(f"\n{invocations} nipoppy invocation(s) checked, {len(problems)} problem(s)")
    return 1 if problems else 0


def main():
    parser = argparse.ArgumentParser(description="Check the nipoppy-cli skill against the installed Nipoppy CLI.")
    parser.add_argument("--skill-dir", type=Path, default=DEFAULT_SKILL)
    parser.add_argument("--print-pin", action="store_true")
    args = parser.parse_args()

    if not (args.skill_dir / "SKILL.md").is_file():
        print(f"notice: {args.skill_dir} not found; skipping nipoppy-cli check", file=sys.stderr)
        return 1 if args.print_pin else 0

    pin = read_pin(args.skill_dir)
    if args.print_pin:
        if pin is None:
            print("✘ SKILL.md frontmatter has no metadata.nipoppy-version", file=sys.stderr)
            return 1
        print(pin)
        return 0

    installed = version("nipoppy")
    print(f"skill pin: {pin}   installed nipoppy: {installed}")
    return check(args.skill_dir)


if __name__ == "__main__":
    sys.exit(main())
