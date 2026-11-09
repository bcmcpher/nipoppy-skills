# Curation: raw DICOMs → BIDS

Skip this stage if the study was initialized from an existing BIDS dataset.

## 1. Populate `sourcedata/imaging/pre_reorg/`

- Use uncompressed DICOMs, one directory per participant-session.
- By default the layout is `pre_reorg/<participant_id>/<session_id>/...`.
- Folder names must match the manifest IDs exactly, with no `sub-`/`ses-` prefixes.
- Other layouts work through `DICOM_DIR_PARTICIPANT_FIRST: false` (session first) or a `DICOM_DIR_MAP_FILE` in `global_config.json` (see `study-setup.md`).

## 2. `nipoppy track-curation`

- Creates or updates `sourcedata/imaging/curation_status.tsv`. Columns:
  - `participant_id`, `visit_id`, `session_id`, `datatype`, `participant_dicom_dir`
  - the boolean columns `in_pre_reorg`, `in_post_reorg`, `in_bids`
- Each run regenerates the whole table from the manifest and what is on disk. The `--regenerate` flag is deprecated and no longer needed.
- Rerun it whenever files are added, removed or changed outside Nipoppy, such as manually copied DICOMs or a BIDS dataset created by hand.
- `reorg` and `bidsify` read this file to decide what to run. Stale statuses therefore cause participants to be skipped.

## 3. `nipoppy reorg`

- Processes participant-sessions with `in_pre_reorg = True` and `in_post_reorg = False`.
- Writes `post_reorg/sub-<participant_id>/ses-<session_id>/` and sets `in_post_reorg` itself.
- Creates **symlinks** by default. A copy option is available; see `-h`.
- An optional DICOM check reads headers and logs files with the `DERIVED` image type, which can break some BIDS converters.
- Logs go to `logs/reorg/`.

## 4. `nipoppy bidsify`

1. Install a BIDS converter pipeline if none is installed. It goes in `pipelines/bidsification/`; see `pipelines.md`.
2. Fill in its `PIPELINE_VARIABLES` in `global_config.json`.
3. Run it step by step. Each converter defines its own steps, which you can find in the bundle's `config.json` under `STEPS`. Without `--pipeline-step`, the first step runs.

Runs on participant-sessions that are reorganized (`in_post_reorg`) but not yet in BIDS (`in_bids`). Steps with `UPDATE_STATUS: true` in the pipeline config set `in_bids` automatically.

### Example: dcm2bids (steps `prepare` → `convert`)

```bash
# 1. In global_config.json, set
#    PIPELINE_VARIABLES.BIDSIFICATION.dcm2bids.<version>.DCM2BIDS_CONFIG_FILE
#    e.g. "[[NIPOPPY_DPATH_CODE]]/dcm2bids_config.json". prepare crashes if it is null.

# 2. Run dcm2bids_helper on one participant to inspect the sidecar JSONs
nipoppy bidsify --study <root> --pipeline dcm2bids --pipeline-step prepare \
  --participant-id 01 --session-id BL

# 3. Write code/dcm2bids_config.json: match sidecar metadata
#    (e.g. SeriesDescription) to BIDS datatype/suffix
# 4. Convert (simulate first, then one participant, then all)
nipoppy bidsify --study <root> --pipeline dcm2bids --pipeline-step convert --simulate
```

### After bidsify

- Validate `bids/` with the BIDS Validator.
- Check that `in_bids` is now `True` in `curation_status.tsv`.
- Add any non-imaging BIDS files the user wants, such as `dataset_description.json` and `participants.tsv`.
