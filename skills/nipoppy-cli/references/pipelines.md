# Pipelines: install, process, track, extract

There are three pipeline types, each with its own runner:

| Type | Runner |
|---|---|
| `bidsification` | `bidsify` |
| `processing` | `process` |
| `extraction` | `extract` |

The runners share options: `--pipeline` (required), `--pipeline-version` (default: latest installed), `--pipeline-step` (default: first step), participant/session filters, `--simulate`, `--keep-workdir`, `--hpc`, and subcohort files. Check `-h` for the exact spelling.

## Installing pipelines

1. Look first: `nipoppy pipeline list --study <root>` shows what is installed. Bundles live in `pipelines/<type>/<name>-<version>/`.
2. Find one: `nipoppy pipeline search <query>` searches Nipoppy pipelines on Zenodo. It can filter by pipeline type.
3. Install: `nipoppy pipeline install --study <root> <SOURCE>`. `SOURCE` is a Zenodo record ID (e.g. `zenodo.1234567` or `1234567`) or a local bundle directory.
   - If the container image is missing, it offers to pull it into `containers/`. This can be slow and large, so confirm with the user. For non-interactive use there are two flags, which are mutually exclusive: assume-yes pulls the image, and skip-container skips the pull.
   - It prints the new variables it added to `global_config.json` → `PIPELINE_VARIABLES`.
4. **Set every new `null` variable** in `PIPELINE_VARIABLES.<TYPE>.<name>.<version>` before running. Examples: a FreeSurfer license path, a TemplateFlow directory, a dcm2bids config file. Ask the user for values you cannot infer.

The pipeline's own settings (steps, container, tracker paths, HPC resources) are in the bundle's `config.json` and the files it references. These may be `.json` or `.json5`; newer bundles use `.json5`, which allows comments. You may edit these locally, for example the invocation args.

## `nipoppy process`

- Runs on participant-sessions that are `in_bids` in `curation_status.tsv` **and not** `SUCCESS` in `processing_status.tsv` for that pipeline, version and step.
- Outputs go to `derivatives/<name>/<version>/output/`. The work directory under `scratch/work/` is deleted on success unless kept.
- A tar option archives each participant-session's output directory after success. It requires `PARTICIPANT_SESSION_DIR` in the pipeline's tracker config.

```bash
nipoppy process --study <root> --pipeline mriqc --participant-id 01 --session-id BL --simulate
```

## `nipoppy track-processing`

- Run it after every `process` run. `process` does not update the status file itself, so without this, completed participants rerun and `extract` sees nothing.
- Writes `derivatives/processing_status.tsv` with columns:
  - `participant_id`, `bids_participant_id`, `session_id`, `bids_session_id`
  - `pipeline_name`, `pipeline_version`, `pipeline_step`
  - `status`
- `status` is `SUCCESS` if every path in `PATHS` of the bundle's tracker config exists (globs allowed, relative to `derivatives/<name>/<version>/output/`), and `FAIL` otherwise. It is based on file presence, not exit codes.
- To track in parallel, install `nipoppy[parallel]` and see `-h` for the jobs option.

## `nipoppy extract`

- An extraction pipeline declares `PROC_DEPENDENCIES` (processing pipeline name, version and step) in its `config.json`.
- It runs on participant-sessions marked `SUCCESS` for **all** dependencies. Make sure the processing pipeline has completed and `track-processing` has been run first.
- Outputs go to `derivatives/<processing pipeline>/<version>/idp/`, though this depends on the extractor's invocation.
