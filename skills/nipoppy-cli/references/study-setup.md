# Study setup: `init`, manifest, global config

## Initializing a study

- **New study from raw (DICOM) data:** `nipoppy init --study <root>`.
  - Creates the directory tree, `.nipoppy/`, a default `global_config.json`, and an *example* `manifest.tsv`.
  - The example manifest must be replaced with the study's real participants and visits. Use a script to generate a correct manifest file.
- **Starting from an existing BIDS dataset:** `nipoppy init --study <root> --bids-source <bids_dir>`.
  - Creates the directory tree, `.nipoppy/` and a default `global_config.json`, and generates a correct `manifest.tsv` from the BIDS `sub-*`/`ses-*` folders.
  - Session-less BIDS data gets the dummy session `unnamed`.
  - Curation steps (`reorg`, `bidsify`) can then be skipped.
- **Shared container images:** `--container-store <dir>` (or the `NIPOPPY_CONTAINER_STORE` env var) makes `containers/` a symlink to an existing shared directory. Only relevant if using Apptainer or Singularity. Added in 0.4.8.

## manifest.tsv

Tab-separated with columns `participant_id`, `visit_id`, `session_id`, `datatype`. Each row is one participant-visit.

```
participant_id	visit_id	session_id	datatype
01	BL	BL	['anat']
01	M06
01	M12	M12	['anat', 'dwi']
```

- Participants and sessions not in the manifest are invisible to every command.
- `participant_id` and `session_id` are alphanumeric only, with no `sub-`/`ses-` prefixes and no `-`, `_` or `.`.
- Leave `session_id` and `datatype` empty for visits without imaging.
- Original IDs often contain disallowed characters. Map them to valid IDs in a `recruitment.tsv` file, and agree on the mapping with the user. Never silently rewrite IDs.

## global_config.json

The file is JSON and may contain comments. These are the keys to know:

| Key | Purpose |
|---|---|
| `SUBSTITUTIONS` | String replacements applied to this file and to pipeline configs. Set `[[HPC_ACCOUNT_NAME]]` here. Built-in placeholders such as `[[NIPOPPY_DPATH_ROOT]]`, `[[NIPOPPY_DPATH_CODE]]` and `[[NIPOPPY_DPATH_CONTAINERS]]` resolve to study paths. |
| `DICOM_DIR_PARTICIPANT_FIRST` | `true` (default) means raw data is in `pre_reorg/<participant>/<session>/`. `false` means ``pre_reorg/<session>/<participant>/`. |
| `DICOM_DIR_MAP_FILE` | Alternative to the above: a TSV with columns `participant_id`, `session_id` and `participant_dicom_dir` for arbitrary raw layouts. |
| `CONTAINER_CONFIG` | Container engine settings: `COMMAND` (`"apptainer"`, `"singularity"`, `"docker"`, or `null` for baremetal execution), `ARGS`, `BIND_PATHS`, `ENV_VARS`. Pipeline configs can override these. |
| `HPC_PREAMBLE` | Shell lines prepended to HPC job scripts. They must activate the Python environment that has Nipoppy installed (see [hpc.md](hpc.md)). |
| `HPC_QUEUE_LIMIT` | Maximum number of your jobs allowed in the HPC queue (default config: 1000; `null` means no limit). |
| `PIPELINE_VARIABLES` | Per-pipeline values organized as `{BIDSIFICATION,PROCESSING,EXTRACTION} → name → version → variable`. They are added as `null` by `pipeline install` and **must be filled in before running**. |
| `CUSTOM` | Free-form; ignored by Nipoppy. |

### If using Docker instead of Apptainer

In `CONTAINER_CONFIG`:
- set `"COMMAND": "docker"`
- remove Apptainer-only args from `ARGS`, notably `--cleanenv`

Apply the same change to any `CONTAINER_CONFIG` in installed pipeline `config.json` files (top-level or per step).

`BIND_PATHS` requires Nipoppy >= 0.4.6. With older versions, use `--volume src:dst` in `ARGS`.

### Environment overrides

`.env` files are loaded before commands run: `<root>/.env` first, then `~/.nipoppy/.env`. Variables that are already set are not overridden. Useful variables: `NIPOPPY_CONTAINER_STORE` and `NIPOPPY_LAYOUT`.
