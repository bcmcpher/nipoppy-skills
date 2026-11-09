---
name: nipoppy-cli
description: Curate and process neuroimaging datasets. Use when a user mentions Nipoppy or wants to standardize (using BIDS) or process neuroimaging data, with or without HPC (Slurm or SGE). Also use when a .nipoppy directory, global_config.json, or manifest.tsv file are present.
license: MIT
---

# Nipoppy CLI

## Step 1: Orient

1. Check that the CLI works: `nipoppy --version`. If it is not installed, ask user about any existing installation. If needed, with user confirmation, install `nipoppy` from PyPI with the user's preferred environment tool.
2. Find the study root: the directory that contains a `.nipoppy/` directory. If none exists, the study must be initialized first (see `references/study-setup.md`).
3. Inspect the study state (read-only):
   - `global_config.json`: in particular `PIPELINE_VARIABLES` entries that are still `null`
   - `manifest.tsv`
   - `pipelines/{bidsification,processing,extraction}/`: installed pipelines
   - `sourcedata/imaging/curation_status.tsv` and `derivatives/processing_status.tsv`
   - `nipoppy status --study <root>` and `nipoppy pipeline list --study <root>` for a summary
4. Report what is present or missing before proposing or running commands.

## Step 2: Get exact syntax from the CLI

Do not rely on memory for flags or arguments. Before building a command, run `nipoppy <command> [subcommand] -h`. The installed version is the source of truth.

## Step 3: Load the relevant reference

| Topic | Reference |
|---|---|
| Overall workflow, directory layout, glossary | `references/workflow-overview.md` |
| `init`, `manifest.tsv`, `global_config.json`, containers (Apptainer/Docker) | `references/study-setup.md` |
| Raw DICOMs → BIDS: `reorg`, `bidsify`, `track-curation` | `references/curation.md` |
| Installing and running pipelines: `pipeline search/install/list`, `process`, `track-processing`, `extract` | `references/pipelines.md` |
| Running on a cluster (`--hpc slurm`/`sge`) | `references/hpc.md` |
| Making or sharing a pipeline: `pipeline create/validate/upload` | `references/pipeline-authoring.md` |

## Step 4: Run safely

- Read-only commands can run freely: `-h`, `status`, `pipeline list`, `pipeline search`.
- `--dry-run` (all commands) prints what would happen. `--simulate` (`bidsify`, `process`, `extract` only) prints the pipeline invocation without running the container.
- For `bidsify`, `process` and `extract`, work up in stages:
  1. `--simulate` on one participant-session (`--participant-id X --session-id Y`)
  2. a live run on that one participant-session
  3. the full cohort
- Ask the user before:
  - any live run that writes, moves or links data (`reorg`, `bidsify`, `process`, `extract`)
  - submitting HPC jobs
  - `pipeline install` (it may pull large container images)
  - `pipeline upload` (it publishes to Zenodo)
  - any `--force` flag
- `manifest.tsv` is the user's ground truth for which participants and visits exist. Do not add or remove rows without explicit confirmation.

## Step 5: Handle failures

- Logs are under `<root>/logs/`. There is one subdirectory per command, and pipeline runs have a `<pipeline>-<version>/` subdirectory with one timestamped log per participant-session. HPC scheduler output is in `logs/hpc/`.
- To debug, rerun one failed participant-session with `--keep-workdir` and `-v`. The work directory is kept under `scratch/work/`.
- Runners skip participant-sessions already marked complete. Plain re-runs therefore only redo what is missing or failed, provided the status files are up to date.

## Key facts

- `--study <root>` sets the study root. It defaults to the current directory or the closest parent containing `.nipoppy/`. Releases before 0.4.8 call it `--dataset`, which is now a deprecated alias.
- Participant and session IDs are alphanumeric only, with no `sub-`/`ses-` prefix in `manifest.tsv`. CLI ID options accept IDs with or without the prefix.
- Deprecated command names still work with a warning: `doughnut` → `track-curation`, `run` → `process`, `track` → `track-processing`.

## Typical order

`init` → manifest + raw data → `reorg` → `bidsify` → `process` → `track-processing` → `extract`. Run `track-curation` whenever raw or BIDS data changes outside Nipoppy. `status` can run at any time.
