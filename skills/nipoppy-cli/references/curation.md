# Curation: raw DICOMs (or NIfTIs) → BIDS

## From DICOMs

### 1. Populate `sourcedata/imaging/pre_reorg/`

- Use uncompressed DICOMs, one directory per participant-session.
- By default the layout is `pre_reorg/<participant_id>/<session_id>/...`.
- Folder names must match the manifest IDs exactly, with no `sub-`/`ses-` prefixes.
- Other layouts are set in `global_config.json`:
  - `DICOM_DIR_PARTICIPANT_FIRST: false` means `pre_reorg/<session_id>/<participant_id>/`.
  - `DICOM_DIR_MAP_FILE` points to a TSV with columns `participant_id`, `session_id` and `participant_dicom_dir`, for arbitrary layouts. It takes the place of the setting above.

### 2. `nipoppy track-curation`

- Creates or updates `sourcedata/imaging/curation_status.tsv`. Columns:
  - `participant_id`, `visit_id`, `session_id`, `datatype`, `participant_dicom_dir`
  - the boolean columns `in_pre_reorg`, `in_post_reorg`, `in_bids`
- Each run regenerates the whole table from the manifest and what is on disk.
- Rerun it whenever files are added, removed or changed outside Nipoppy, such as manually copied DICOMs or a BIDS dataset created by hand.
- `reorg` and `bidsify` read this file to decide what to run. Stale statuses therefore cause participants to be skipped.

### 3. `nipoppy reorg`

- Processes participant-sessions with `in_pre_reorg = True` and `in_post_reorg = False`.
- Writes `post_reorg/sub-<participant_id>/ses-<session_id>/` and sets `in_post_reorg` itself.
- Creates **symlinks** by default. A copy option is available; see `-h`.

### 4. `nipoppy bidsify`

This involes running a pipeline, see [pipelines.md](pipelines.md).

Most BIDSification pipelines in Nipoppy are divided into steps.
Between the steps there is usually a manual step of creating a configuration or heuristic file mapping some DICOM file characteristics to BIDS file paths.

BIDSification pipelines run on participant-sessions that are reorganized (`in_post_reorg`) but not yet in BIDS (`in_bids`). Steps with `UPDATE_STATUS: true` in the pipeline config set `in_bids` automatically.

#### Example: dcm2bids (steps: `prepare`, `convert`)

```bash
# 1. In global_config.json, set
#    PIPELINE_VARIABLES.BIDSIFICATION.dcm2bids.<version>.DCM2BIDS_CONFIG_FILE
#    e.g. "[[NIPOPPY_DPATH_CODE]]/dcm2bids_config.json"

# 2. Run dcm2bids_helper on one participant to inspect the sidecar JSONs
nipoppy bidsify --study <root> --pipeline dcm2bids --pipeline-step prepare \
  --participant-id 01 --session-id BL

# 3. Write code/dcm2bids_config.json: match sidecar metadata
#    (e.g. SeriesDescription) to BIDS datatype/suffix

# 4. Convert (simulate first, then one participant, then all)
nipoppy bidsify --study <root> --pipeline dcm2bids --pipeline-step convert --simulate
```

### From NIfTIs

Every NIfTI should have an associated JSON sidecar file.
If JSON sidecars are missing, they will need to be created using information from the DICOM headers.
Consult BIDS specification for which fields are required.

If NIfTI + JSON pairs are available, write a script to move/copy/symlink them into BIDS paths.
Consult the BIDS specification website and/or schema.

## After BIDSification

- Run the BIDS validator (`nipoppy pipeline search bids-validator`) and fix errors.
- Check that `in_bids` is now `True` in `curation_status.tsv`. Run `track-curation` if needed.
- Add any non-imaging BIDS files the user wants, such as `dataset_description.json`.
