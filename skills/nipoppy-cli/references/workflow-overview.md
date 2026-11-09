# Nipoppy Workflow Overview

## What is Nipoppy?

Nipoppy is a Python CLI tool for managing neuroimaging datasets in a standardized, reproducible way.
It wraps around Boutiques descriptors to provide a consistent interface for running BIDS conversion (BIDSification) and data processing or extraction pipelines.

### Key dependencies

- Python >= 3.10, Linux or macOS. Windows is not supported.
- Apptainer or Docker: recommended for most setups. Can be bypassed if using baremetal installation of software or if pipelines can be loaded using `lmod`.

### Installation

Nipoppy is indexed on PyPI as `nipoppy`.
Use the user's preferred Python environment management tool to install it if needed.

## End-to-end workflow

This is the full end-to-end workflow.
In practice the user may start at any point in this process, and the flow is not strictly linear.

```
[1] nipoppy init                — Create dataset directory structure + config stubs
        │
        ▼
[2] Generate manifest.tsv       — Register all expected participant-session pairs
        │
        ▼
[3] Populate pre_reorg          — Move/copy raw DICOM files into pre_reorg directory
        │
        ▼
[4] nipoppy track-curation      — Build/update curation status file (in_pre_reorg, in_post_reorg, in_bids statuses)
        │
        ▼
[5] nipoppy reorg               — Move/copy/rename DICOMs from pre_reorg to post_reorg directories
        │
        ▼
[6] nipoppy track-curation      — Update status after reorg
        │
        ▼
[7] nipoppy bidsify             — Convert DICOMs to BIDS (dcm2bids / HeuDiConv / BIDScoin)
        │
        ▼
[8] nipoppy track-curation      — Update status after BIDS conversion
        │
        ▼
[9] nipoppy process             — Execute processing pipeline (fMRIPrep, MRIQC, etc.)
        │
        ▼
[10] nipoppy track-processing    — Record per-participant pipeline completion
        │
        ▼
[11] nipoppy extract            — Extract IDPs into analysis-ready tables
```

`nipoppy status` can be run at any point to see current state.

---

## Key Files and Directories

### Dataset root (created by `nipoppy init`)

```
<dataset>/
├── .nipoppy/                      # Marks the study root
├── global_config.json             # Global config: minimum settings needed for commands/pipelines to run
├── manifest.tsv                   # Participant-visit registry (user-maintained ground truth)
├── code/hpc/                      # HPC job template + scheduler configs
├── containers/                    # Container images (e.g. .sif files)
├── pipelines/
│   └── {bidsification,processing,extraction}/<name>-<version>/   # Installed pipeline bundles
├── sourcedata/
│   └── imaging/
│       ├── curation_status.tsv    # Per-participant-session curation tracking
│       ├── pre_reorg/             # Raw DICOMs drop zone (input to reorg)
│       └── post_reorg/            # Reorg output: sub-<participant_id>/ses-<session_id> layout
├── bids/                          # BIDS-valid output from bidsify
├── derivatives/                   # Pipeline outputs: <pipeline_name>/<pipeline_version>/output/
│   └── processing_status.tsv      # Per-participant-session processing tracking
├── logs/                          # Log files (one subdirectory per command)
├── scratch/work/                  # Pipeline working directories
└── tabular/                       # Phenotypic/tabular data
```

### manifest.tsv columns

| Column | Description |
|--------|-------------|
| `participant_id` | Alphanumeric subject identifier, no `sub-` prefix (e.g., `001`) |
| `visit_id` | Visit label (e.g., `BL`); every row needs one |
| `session_id` | Alphanumeric imaging session label, no `ses-` prefix (can be the same as `visit_id`); empty if no imaging at that visit |
| `datatype` | List of BIDS datatypes (e.g., `['anat', 'dwi']`); empty if no imaging |

---

## Key Concepts & Glossary

| Term | Definition |
|------|------------|
| **Boutiques** | JSON descriptor standard for containerized tools; nipoppy uses it to resolve pipeline invocations |
| **Apptainer** | Default container engine (formerly Singularity); Docker or bare-metal installs also possible |
| **BIDS** | Brain Imaging Data Structure — the target format for `bidsify` output |
| **curation_status.tsv** | Tracks raw data availability, reorg completion, and BIDS conversion per participant-session |
| **processing_status.tsv** | Tracks pipeline completion (`SUCCESS`/`FAIL`) per participant-session, written by `track-processing` |
| **IDP** | Imaging-Derived Phenotype — quantitative measure extracted from a pipeline output (e.g., cortical thickness, FA values) |
| **pre_reorg** | Raw DICOM drop zone; unstructured |
| **post_reorg** | Structured DICOM layout: one folder per participant per session |
| **pipeline bundle** | Directory with a pipeline's `config.json`, Boutiques descriptor, invocation, and optional tracker/HPC configs |
| **pipeline step** | A sub-stage within a pipeline (e.g., `prepare`, `convert` in dcm2bids) |
| **simulate** | `--simulate` on `bidsify`/`process`/`extract`: print the pipeline invocation without running it (`--dry-run` is the general equivalent for all commands) |
