---
name: nipoppy-cli
description: Curate and process neuroimaging datasets. Use when a user mentions Nipoppy or wants to standardize (using BIDS) or process neuroimaging data, with or without HPC (Slurm or SGE). Also use when a .nipoppy directory, global_config.json, or manifest.tsv file are present.
license: MIT
---

# Nipoppy CLI

This skill is based on the documentation at https://nipoppy.readthedocs.io/en/0.4.8/.
Commands/layout may be different for other versions.

## Important rules

- **Always get exact syntax from the CLI itself**: When planning a command, run `nipoppy <command> [subcommand] -h` first. The installed version is the source of truth.
- **Run safely**
  - Read-only commands can run freely: `-h`, `status`, `pipeline list`, `pipeline search`.
  - `--dry-run` (all commands) prints what would happen. `--simulate` (`bidsify`, `process`, `extract` only) prints the generated pipeline command without running it.
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

## Step 1: Check environment

1. Check that the CLI works: `nipoppy --version`.
  - If it is not installed, ask user about any existing installation.
  - If needed, with user confirmation, install `nipoppy` from PyPI with the user's preferred environment management tool.

## Step 2: Check study state

1. Determine if a study is expected to already exist.
  - If so, find the study root: the directory that contains a `.nipoppy/` directory. Then inspect the study state (read-only):
    - `global_config.json`: in particular `PIPELINE_VARIABLES` entries that are still `null`
    - `manifest.tsv`
    - `pipelines/{bidsification,processing,extraction}/`: installed pipelines
    - `sourcedata/imaging/curation_status.tsv` and `derivatives/processing_status.tsv`
    - `nipoppy status --study <root>` and `nipoppy pipeline list --study <root>` for a summary
  - If not, see `references/study-setup.md`.

## Step 3: Load the relevant reference

The typical workflow is: `init` → manifest + raw data + `track-curation` → `reorg` + `track-curation` → `bidsify` + `track-curation` → `process` + `track-processing` → `extract`.
Load the relevant reference based on the study state and what the user wants.

| Topic | Reference |
|---|---|
| Overall workflow, directory layout, glossary | `references/workflow-overview.md` |
| `init`, `manifest.tsv`, `global_config.json`, containers (Apptainer/Docker) | `references/study-setup.md` |
| Raw DICOMs → BIDS: `reorg`, `bidsify`, `track-curation` | `references/curation.md` |
| Installing and running pipelines: `pipeline search/install/list`, `process`, `track-processing`, `extract` | `references/pipelines.md` |
| Running on a cluster (`--hpc slurm`/`sge`) | `references/hpc.md` |
| Making or sharing a pipeline: `pipeline create/validate/upload` | `references/pipeline-authoring.md` |

## Troubleshooting

- Logs are under `<root>/logs/`. There is one subdirectory per command, and pipeline runs have a `<pipeline>-<version>/` subdirectory with one timestamped log per participant-session. HPC scheduler output is in `logs/hpc/`.
- To debug a pipeline run, rerun one failed participant-session with `--keep-workdir` and `-v`. The work directory is kept under `scratch/work/`.
- Runners skip participant-sessions already marked complete. Plain re-runs therefore only redo what is missing or failed, provided the status files are up to date.
