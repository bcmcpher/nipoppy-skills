# skills

This repository contains skills for LLM agents to work with Nipoppy users.

Each skill lives in `skills/<name>/` as a `SKILL.md` plus any `references/` and
`scripts/` it needs. The same directory is consumed by two agent harnesses:

- **Claude Code**, via the plugin manifest in `.claude-plugin/` (see below)
- **GitHub Copilot**, via `.github/skills`, which is a symlink to `skills/`

Adding a directory under `skills/` is enough for both — there is no manifest to
update.

## Available skills

| Skill | Use it for |
|---|---|
| [`argparse-argdump-serializer`](skills/argparse-argdump-serializer) | Serializing Python `argparse` parsers from a repository into JSON with `argdump` |
| [`boutiques-descriptor-creator`](skills/boutiques-descriptor-creator) | Generating a Boutiques 0.5 descriptor for a CLI tool from its help text, including containerized tools |

## Install for Claude Code

```bash
claude plugin marketplace add nipoppy/skills
claude plugin install nipoppy-skills@nipoppy
```

Restart Claude Code afterwards. To try the skills from a local clone without
installing them:

```bash
claude --plugin-dir /path/to/skills
```

## Install for GitHub Copilot

Copilot discovers skills in `.github/skills` automatically once the repository
is available to it. No extra configuration is required.

## Contributing

- One skill per pull request. Prefix the title with `[ENH]`.
- Keep `SKILL.md` focused on the workflow. Move field references, schemas, and
  long tables into `references/` so they are only read when needed.
- Refer to supporting files with plain skill-relative paths
  (`references/foo.md`, `scripts/bar.sh`), not harness-specific variables — the
  same file has to resolve under both Claude Code and Copilot.
- Make any script the skill tells the agent to run executable (`chmod +x`).

CI checks the manifests, the skill frontmatter, that every `references/` and
`scripts/` path named in a `SKILL.md` exists, and that the Boutiques examples
still pass `bosh validate`. Run it locally with:

```bash
.github/scripts/validate-skills.sh
```

## License

MIT. See [LICENSE](LICENSE).
