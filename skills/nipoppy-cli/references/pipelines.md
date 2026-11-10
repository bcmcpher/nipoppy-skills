# Pipelines: install, process, track, extract

There are three pipeline types, each with its own command:

| Type | Command |
|---|---|
| `bidsification` | `bidsify` |
| `processing` | `process` |
| `extraction` | `extract` |

The three runners share many options (see `-h`).
If not given, the pipeline version defaults to the latest installed and the step to the first step defined in the pipeline config file.

## Installing pipelines

1. Look first: `nipoppy pipeline list --study <root>` shows what is installed. Bundles live in `pipelines/<type>/<name>-<version>/`.
2. Find one: `nipoppy pipeline search <query>` searches Nipoppy pipelines on Zenodo. It can filter by pipeline type.
3. Install: `nipoppy pipeline install --study <root> <SOURCE>`. `SOURCE` is a Zenodo record ID (e.g. `1234567`) or a local bundle directory.
   - If the container image is missing, it offers to pull it into `containers/`. This can be slow and large, so confirm with the user. For non-interactive use there are two flags, which are mutually exclusive: `--assume-yes` pulls the image, and `--skip-container` skips the pull.
   - It prints any new variable(s) it added to `global_config.json` → `PIPELINE_VARIABLES`.
4. **Set every new `null` variable** in `PIPELINE_VARIABLES.<TYPE>.<name>.<version>` before running. Examples: a FreeSurfer license path, a TemplateFlow directory, a config file path. Ask the user for values you cannot infer.

## Bundle files and custom arguments

An installed bundle (`pipelines/<type>/<name>-<version>/`) contains:
- `config.json`: the pipeline's name, version, container and `STEPS`. Each step names its descriptor, invocation, tracker and HPC config files (all optional).
- the files those steps name. These may be `.json` or `.json5` (which allows comments).

Nipoppy runs every step through [Boutiques](https://boutiques.github.io/), using two files:
- **Descriptor** (e.g. `descriptor.json`): describes the tool's command line. Each entry in `inputs` has an `id`, a type, and a `value-key` that marks where it goes in `command-line`. The descriptor defines which arguments *can* be set. Leave it alone unless an argument is missing from it.
- **Invocation** (e.g. `invocation.json`): the argument values for this study. Keys are input `id`s from the descriptor. **This is where to set custom runtime arguments**.

At run time, Nipoppy fills in placeholders in the invocation, then validates it against the descriptor and builds the command. Possible placeholders:
- `[[NIPOPPY_*]]` paths and IDs, e.g. `[[NIPOPPY_DPATH_BIDS]]`, `[[NIPOPPY_DPATH_PIPELINE_OUTPUT]]`, `[[NIPOPPY_DPATH_PIPELINE_WORK]]`, `[[NIPOPPY_PARTICIPANT_ID]]` (no prefix), `[[NIPOPPY_BIDS_PARTICIPANT_ID]]` (with `sub-`), and the matching session forms
- `[[<VARIABLE>]]` for the pipeline's own `PIPELINE_VARIABLES`, e.g. `[[FREESURFER_LICENSE_FILE]]`
- keys from `SUBSTITUTIONS` in `global_config.json`

To change how a pipeline runs:
1. Find the step's invocation file through `STEPS` in `config.json`.
2. Look up the argument's `id` in the descriptor's `inputs`. Don't guess it from the tool's flag name.
3. Set or edit that key in the invocation. Keep the placeholders that are already there.
4. If the argument is not in the descriptor at all, add an input for it to the descriptor (`id`, `name`, `type`, `optional: true`, `value-key`) and put the `value-key` in `command-line`. Then set it in the invocation. Inform the user the descriptor was missing an argument.
5. Check the result with `--simulate` on one participant-session. It prints the generated command.

Edits apply only to this study's installed copy of the bundle.

## `nipoppy process`

- Runs on participant-sessions that are `in_bids` in `curation_status.tsv` **and not** `SUCCESS` in `processing_status.tsv` for that pipeline, version and step.
- Outputs go to `derivatives/<name>/<version>/output/`. The work directory under `scratch/work/` is deleted on success unless explicitly kept via CLI option.
- A tar option (unique to `process` command) archives each participant-session's output directory after success. Consider using this if the system imposes a limit on the number of inodes (files), though note that downstream processes will have to untar relevant files. It requires `PARTICIPANT_SESSION_DIR` in the pipeline's tracker config.

Example command:

```bash
nipoppy process --study <root> --pipeline mriqc --participant-id 01 --session-id BL --simulate
```

## `nipoppy track-processing`

Run it after every `process` run. `process` does not update the status file itself, and it uses that file to decide which participant-sessions to skip.

### How status is decided

- Each step in the bundle's `config.json` names its tracker config with `TRACKER_CONFIG_FILE`. A step without one cannot be tracked.
- The tracker config has:
  - `PATHS`: expected output paths, relative to `derivatives/<name>/<version>/output/`. Globs (`*`) are allowed; a glob counts as found if at least one file matches. Placeholders `[[NIPOPPY_PARTICIPANT_ID]]`, `[[NIPOPPY_SESSION_ID]]`, `[[NIPOPPY_BIDS_PARTICIPANT_ID]]` and `[[NIPOPPY_BIDS_SESSION_ID]]` are filled in per participant-session.
  - `PARTICIPANT_SESSION_DIR` (optional): the participant-session output directory. Needed for the `process` tar option. When the output was tarred, `PATHS` are also looked for inside the tarball.
- The tracker config file can be customized based on use-case. Choose paths that only exist once a run has finished (e.g. a final report or the last output written), otherwise incomplete runs are marked `SUCCESS`.
- `status` is `SUCCESS` if every entry in `PATHS` is found, and `FAIL` otherwise. Only file presence counts, not exit codes or file contents. Tracking runs only on participant-sessions that are `in_bids`.
- Steps are tracked separately: pass the same `--pipeline-step` as for `process`.

### Output

`derivatives/processing_status.tsv`, with columns:
- `participant_id`, `bids_participant_id`, `session_id`, `bids_session_id`
- `pipeline_name`, `pipeline_version`, `pipeline_step`
- `status`

Rows for other pipelines and participant-sessions are left as they are. `nipoppy status` summarizes the file.

## `nipoppy extract`

- An extraction pipeline declares `PROC_DEPENDENCIES` (processing pipeline name, version and step) in its `config.json`.
- It runs on participant-sessions marked `SUCCESS` for **all** dependencies. Make sure the processing pipeline has completed and `track-processing` has been run first.
- Outputs typically go to `derivatives/<processing pipeline>/<version>/idp/`, though this depends on the extractor's invocation.
