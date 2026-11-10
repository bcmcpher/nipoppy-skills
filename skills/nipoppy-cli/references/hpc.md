# Running on HPC (Slurm / SGE)

`bidsify`, `process` and `extract` accept `--hpc slurm` or `--hpc sge`. Nipoppy then submits a **job array with one job per participant-session** instead of running locally.

## One-time setup in `global_config.json`

- `HPC_PREAMBLE`: shell lines run at the start of every job. These **must activate the Nipoppy Python environment**, for example:
  - `"source <venv>/bin/activate"`
  - `"source ~/.bashrc; conda activate <env>"`

  You can also add `module load apptainer` or similar here.
- `HPC_QUEUE_LIMIT`: Nipoppy submits only as many jobs as fit under this limit given your current queue (`null` means no limit). Rerun the same command later to submit the rest; completed participant-sessions are skipped once tracked.
- `SUBSTITUTIONS` → `[[HPC_ACCOUNT_NAME]]`: the allocation or account. It is passed as the Slurm account or SGE `-q`. Leave it empty if not needed.

## Per-pipeline resources

Resources are set in the bundle's HPC config, usually `pipelines/<type>/<name>-<version>/hpc.json` or `hpc.json5`. The exact file name is given by `HPC_CONFIG_FILE` in the step config. Keys:
- `TIME`
- `CORES`
- `MEMORY`
- `ARRAY_CONCURRENCY_LIMIT`
- `PARTITION` (Slurm)
- `ACCOUNT`: leave it as `[[HPC_ACCOUNT_NAME]]`

Use an empty string for keys you don't need. If a step has no HPC config, create one (e.g. `hpc.json5`) and add `"HPC_CONFIG_FILE"` to that step in the bundle's `config.json`.

## Submitting

1. Submit a single job first: `--participant-id X --session-id Y --hpc slurm`.
2. Check that it succeeds.
3. Submit the rest.
4. Afterwards, run `track-processing` (for `process`).

Confirm with the user before submitting jobs.

## Troubleshooting

- Scheduler stdout/stderr is in `logs/hpc/`. Pipeline logs are in the usual `logs/<command>/...` locations.
- "nipoppy: command not found" means `HPC_PREAMBLE` does not activate the environment.
- The generated job script is deleted after submission. Rerun with `--keep-workdir` to keep `scratch/work/.../run_queue.sh` for inspection.
- Editing that file has no effect on future submissions. Change the Jinja template `code/hpc/job_script_template.sh` instead. Any key added to the HPC config is available to the template, for example `{{ NICE }}`.
- Reserved HPC config keys you must not use: `queue`, `working_directory`, `command`, and anything starting with `NIPOPPY_`.

## Other schedulers

- **PySQA-supported schedulers:** add `<name>.yaml` in `code/hpc/`, register it in `code/hpc/clusters.yaml`, and add a section to the template. Then run with `--hpc <name>`.
- **Fully manual submission:** use the write-subcohort option to dump the participant-session list to a TSV, then have each job run the command with the use-subcohort option on its share of that list.
