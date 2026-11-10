---
name: nipoppy-cli
description: Curates and processes neuroimaging datasets with the Nipoppy CLI, from raw DICOMs through BIDS conversion (e.g. dcm2bids) to processing pipelines (e.g. fMRIPrep, MRIQC, FreeSurfer, custom scripts) and imaging-derived phenotype extraction, locally or on HPC (Slurm or SGE). Use when a user mentions Nipoppy or wants to standardize (using BIDS) or process neuroimaging data. Also use when a .nipoppy directory, global_config.json, or manifest.tsv file is present.
license: MIT
---

# Nipoppy CLI

This skill describes Nipoppy 0.4.8. Commands and layout may differ in other versions.

## Important rules

- **Always get exact syntax from the CLI itself.**
  - Do not rely on prior knowledge of older Nipoppy versions.
  - Before running any Nipoppy command, run its help first, e.g. `nipoppy process -h` or `nipoppy pipeline install -h`. Use only flags shown there. The installed version is the source of truth.
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
    - any `--force` flag
    - editing pipeline bundle files (invocation, descriptor, tracker or HPC configs) or `code/hpc/job_script_template.sh`, since these change how pipelines run and tracking statuses
  - `manifest.tsv` is the user's ground truth for which participants and visits exist. Do not add or remove rows without explicit confirmation.

## Step 1: Check environment

1. Check that the CLI works: `nipoppy --version`.
   - If it is not installed, ask the user about any existing installation.
   - If needed, with user confirmation, install `nipoppy` from PyPI with the user's preferred environment management tool.

## Step 2: Check study state

1. Determine if a study is expected to already exist.
   - If so, find the study root (`<root>`): the directory that contains a `.nipoppy/` directory. Then inspect the study state (read-only):
     - `global_config.json`: in particular `PIPELINE_VARIABLES` entries that are still `null`
     - `manifest.tsv`
     - `pipelines/{bidsification,processing,extraction}/`: installed pipelines
     - `sourcedata/imaging/curation_status.tsv` and `derivatives/processing_status.tsv`
     - `nipoppy status --study <root>` and `nipoppy pipeline list --study <root>` for a summary
   - If not, read [references/study-setup.md](references/study-setup.md).

Study layout (created by `nipoppy init`):

```
<root>/
├── .nipoppy/                  # Marks the study root
├── global_config.json         # Study-wide config, including PIPELINE_VARIABLES
├── manifest.tsv               # Participants/visits/sessions (user-maintained)
├── code/hpc/                  # HPC job template + scheduler configs
├── containers/                # Container images (e.g. .sif files)
├── pipelines/<type>/<name>-<version>/   # Installed pipeline bundles
├── sourcedata/imaging/
│   ├── curation_status.tsv    # in_pre_reorg / in_post_reorg / in_bids per participant-session
│   ├── pre_reorg/             # Raw DICOMs (input to reorg)
│   └── post_reorg/            # sub-<participant_id>/ses-<session_id>/ (output of reorg)
├── bids/                      # BIDS data (output of bidsify)
├── derivatives/
│   ├── <name>/<version>/output/        # Pipeline outputs
│   └── processing_status.tsv  # SUCCESS/FAIL per participant-session, pipeline and step
├── logs/                      # One subdirectory per command; HPC output in logs/hpc/
├── scratch/work/              # Pipeline working directories
└── tabular/                   # Phenotypic data
```

## Step 3: Load the relevant reference

Typical workflow:

1. `nipoppy init`, then edit `manifest.tsv` and `global_config.json`
2. Put raw DICOMs in `sourcedata/imaging/pre_reorg/`, then `nipoppy track-curation`
3. `nipoppy reorg`
4. Install and configure a BIDS converter pipeline, then `nipoppy bidsify` (then `track-curation` if `in_bids` was not updated)
5. Install and configure processing pipelines, then `nipoppy process`, then `nipoppy track-processing`
6. `nipoppy extract`

Users may start at any point. BIDS-first studies skip steps 2-4.

Read the reference that matches the study state and what the user wants:

| Topic | Reference |
|---|---|
| `init`, `manifest.tsv`, `global_config.json`, containers (Apptainer/Singularity/Docker) | [references/study-setup.md](references/study-setup.md) |
| Raw DICOMs → BIDS: `reorg`, `bidsify`, `track-curation` | [references/curation.md](references/curation.md) |
| Installing and running pipelines (`pipeline search/install/list`, `process`, `track-processing`, `extract`), including setting/changing pipeline arguments | [references/pipelines.md](references/pipelines.md) |
| Running on a cluster (`--hpc slurm`/`sge`) | [references/hpc.md](references/hpc.md) |

## Glossary

- **Study**: a directory managed by Nipoppy (contains `.nipoppy/`).
- **Pipeline bundle**: a directory with a pipeline's `config.json`, and other configuration files (e.g., Boutiques descriptor, invocation, tracker and HPC configs). Pipeline types: `bidsification`, `processing`, `extraction`.
- **Pipeline step**: a named stage of a pipeline (e.g. `prepare` and `convert` for dcm2bids), selected with `--pipeline-step`. The default is the first step.
- **`PIPELINE_VARIABLES`**: per-pipeline values in `global_config.json` (e.g. license paths) that are `null` after install and must be set before running.
- **Curation status file** (`curation_status.tsv`): where each participant-session is in the raw → BIDS path. Written by `track-curation`, `reorg`, and `bidsify`.
- **Processing status file** (`processing_status.tsv`): whether each participant-session's pipeline outputs exist. Written only by `track-processing`.
- **IDP**: imaging-derived phenotype, a measure extracted from pipeline outputs by `extract`.

## Troubleshooting

- Logs are under `<root>/logs/`. There is one subdirectory per command, and pipeline runs have a `<pipeline>-<version>/` subdirectory with one timestamped log per participant-session. HPC scheduler output is in `logs/hpc/`.
- To debug a pipeline run, rerun one failed participant-session with `--keep-workdir` and `-v`. The work directory is kept under `scratch/work/`.
- Runners skip participant-sessions already marked complete. Plain re-runs therefore only redo what is missing or failed, provided the status files are up to date.
