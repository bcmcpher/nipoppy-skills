#!/bin/bash
# validate-skills.sh — check the plugin manifests and every skill under skills/
#
# Usage: .github/scripts/validate-skills.sh
#
# Requires: jq

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT" || exit 2

pass=0
fail=0

ok()  { echo "  ✔ $1"; pass=$((pass + 1)); }
bad() { echo "  ✘ $1"; fail=$((fail + 1)); }

# --- manifests -------------------------------------------------------------

echo "Manifests"

for manifest in .claude-plugin/plugin.json .claude-plugin/marketplace.json; do
    if [[ ! -f "$manifest" ]]; then
        bad "$manifest is missing"
        continue
    fi
    if ! jq empty "$manifest" 2>/dev/null; then
        bad "$manifest is not valid JSON"
        continue
    fi
    ok "$manifest parses"
done

if [[ -f .claude-plugin/plugin.json ]]; then
    for field in name description version; do
        if [[ -z "$(jq -r --arg f "$field" '.[$f] // empty' .claude-plugin/plugin.json)" ]]; then
            bad "plugin.json is missing required field: $field"
        else
            ok "plugin.json has $field"
        fi
    done
fi

if [[ -f .claude-plugin/marketplace.json ]]; then
    if [[ -z "$(jq -r '.owner.name // empty' .claude-plugin/marketplace.json)" ]]; then
        bad "marketplace.json is missing owner.name"
    else
        ok "marketplace.json has owner.name"
    fi
    if [[ "$(jq -r '.plugins | length' .claude-plugin/marketplace.json)" -lt 1 ]]; then
        bad "marketplace.json lists no plugins"
    else
        ok "marketplace.json lists at least one plugin"
    fi
fi

# --- skills ----------------------------------------------------------------

declare -A seen_names

for skill_dir in skills/*/; do
    skill="${skill_dir%/}"
    name="$(basename "$skill")"
    echo
    echo "$skill"

    manifest="$skill/SKILL.md"
    if [[ ! -f "$manifest" ]]; then
        bad "no SKILL.md"
        continue
    fi

    # Frontmatter must open with --- on line 1 and close with a later ---.
    if [[ "$(head -n 1 "$manifest")" != "---" ]]; then
        bad "SKILL.md does not start with a --- frontmatter delimiter"
        continue
    fi
    frontmatter="$(awk 'NR>1 { if ($0 == "---") exit; print }' "$manifest")"
    if [[ -z "$frontmatter" ]]; then
        bad "SKILL.md has an empty or unterminated frontmatter block"
        continue
    fi

    fm_name="$(echo "$frontmatter" | sed -n 's/^name:[[:space:]]*//p' | head -n 1)"
    fm_desc="$(echo "$frontmatter" | sed -n 's/^description:[[:space:]]*//p' | head -n 1)"

    if [[ -z "$fm_name" ]]; then
        bad "frontmatter has no name"
    elif [[ "$fm_name" != "$name" ]]; then
        bad "frontmatter name '$fm_name' does not match directory '$name'"
    else
        ok "name matches directory"
    fi

    if [[ -z "$fm_desc" ]]; then
        bad "frontmatter has no description"
    else
        ok "has a description"
    fi

    # The nipoppy-cli drift check (check-nipoppy-cli.py) reads its version pin here.
    if [[ "$name" == "nipoppy-cli" ]]; then
        if echo "$frontmatter" | grep -qE '^[[:space:]]+nipoppy-version:[[:space:]]*"?[0-9]'; then
            ok "has metadata.nipoppy-version"
        else
            bad "frontmatter has no metadata.nipoppy-version"
        fi
    fi

    if [[ -n "$fm_name" ]]; then
        if [[ -n "${seen_names[$fm_name]:-}" ]]; then
            bad "duplicate skill name '$fm_name' (also in ${seen_names[$fm_name]})"
        else
            seen_names[$fm_name]="$skill"
        fi
    fi

    # Every references/<file> named in the body must exist relative to the skill
    # directory. Catches paths that only resolve under one agent harness.
    missing_ref=0
    while read -r ref; do
        [[ -z "$ref" ]] && continue
        if [[ ! -f "$skill/$ref" ]]; then
            bad "SKILL.md names a missing file: $ref"
            missing_ref=1
        fi
    done < <(grep -oE '\breferences/[A-Za-z0-9._-]+' "$manifest" | sort -u)
    [[ $missing_ref -eq 0 ]] && ok "all references/ paths resolve"

    # Any scripts/<file>.sh the body tells the agent to run must be executable.
    missing_exec=0
    while read -r scr; do
        [[ -z "$scr" ]] && continue
        if [[ ! -f "$skill/$scr" ]]; then
            bad "SKILL.md names a missing script: $scr"
            missing_exec=1
        elif [[ ! -x "$skill/$scr" ]]; then
            bad "script is not executable: $scr"
            missing_exec=1
        fi
    done < <(grep -oE '\bscripts/[A-Za-z0-9._-]+\.sh' "$manifest" | sort -u)
    [[ $missing_exec -eq 0 ]] && ok "all scripts/ paths resolve and are executable"
done

echo
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
