#!/usr/bin/env python3
"""Validate the example descriptors embedded in the Boutiques skill.

Every fenced ```json block in boutiques-descriptor-creator/SKILL.md that looks
like a complete descriptor is extracted, checked for command-line/inputs
consistency in both directions, and run through `bosh validate`.

Keeps the worked examples honest: they are what the agent copies from.
"""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2] / "skills/boutiques-descriptor-creator/SKILL.md"
VALUE_KEY = re.compile(r"\[[A-Z0-9_]+\]")


def descriptors(text):
    for block in re.findall(r"```json\n(.*?)```", text, re.S):
        block = block.strip()
        # Skip fragments and the skeleton, which uses a literal "..." placeholder.
        if not block.startswith("{") or '"schema-version"' not in block or "..." in block:
            continue
        yield json.loads(block)


def main():
    failures = 0
    found = 0

    for desc in descriptors(SKILL.read_text()):
        found += 1
        label = f"{desc['name']}-{desc['tool-version']}"

        in_template = set(VALUE_KEY.findall(desc["command-line"]))
        in_inputs = {i["value-key"] for i in desc["inputs"]}

        for missing in sorted(in_template - in_inputs):
            print(f"  ✘ {label}: {missing} is in command-line but has no input")
            failures += 1
        for missing in sorted(in_inputs - in_template):
            print(f"  ✘ {label}: {missing} is an input but is not in command-line")
            failures += 1

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(desc, fh, indent=4)
            path = fh.name

        result = subprocess.run(
            ["bosh", "validate", path], capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  ✘ {label}: bosh validate failed")
            print(result.stdout.strip() or result.stderr.strip())
            failures += 1
        else:
            print(f"  ✔ {label}: valid")

    if found == 0:
        print("✘ no example descriptors found in SKILL.md — did the format change?")
        return 1

    print(f"\n{found} example(s) checked, {failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
