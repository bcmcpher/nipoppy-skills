# Running on HPC (Slurm / SGE)

`bidsify`, `process` and `extract` accept `--hpc slurm` or `--hpc sge`. Nipoppy then submits a **job array with one job per participant-session** instead of running locally.

## One-time setup in `global_config.json`

- `HPC_PREAMBLE`: shell lines run at the start of every job. These **must activate the Nipoppy Python environment**, for example:
  - `"source <venv>/bin/activate"`
  - `"source ~/.bashrc; conda activate <env>"`

  You can also add `module load apptainer` or similar here.
- `HPC_QUEUE_LIMIT`: Nipoppy submits only as many jobs as fit under this limit given your current queue (`null` means no limit). Rerun the same command later to submit the rest; completed participant-sessions are skipped once tracked.
- `SUBSTITUTIONS` → `[[HPC_ACCOUNT_NAME]]`: the allocation or account. Pipeline HPC configs use it as `ACCOUNT`, which becomes the Slurm `--account` or the SGE `-q`. Leave it empty if not needed.

## Per-pipeline resources

Resources are set in the bundle's HPC config, usually `pipelines/<type>/<name>-<version>/hpc.json` or `hpc.json5`. The exact file name is given by `HPC_CONFIG_FILE` in the step config. Keys:
- `TIME`
- `CORES` (Slurm)
- `MEMORY`
- `ARRAY_CONCURRENCY_LIMIT`
- `PARTITION` (Slurm)
- `ACCOUNT`: leave it as `[[HPC_ACCOUNT_NAME]]`

Use an empty string for keys you don't need. If a step has no HPC config, create one (e.g. `hpc.json5`) and add `"HPC_CONFIG_FILE"` to that step in the bundle's `config.json`.

## Submitting

1. Submit a single job first: `--participant-id X --session-id Y --hpc slurm`.
2. Check that it succeeds.
3. Submit the rest.
4. Afterwards, update statuses: `track-processing` after `process`, or `track-curation` after `bidsify` if `in_bids` was not updated.

Confirm with the user before submitting jobs.

## The job script template

Every submission renders `code/hpc/job_script_template.sh`, a [Jinja](https://jinja.palletsprojects.com) template, into a job script. It is one template for all pipelines and both schedulers.

Template variables: `NIPOPPY_*` variables (e.g. `NIPOPPY_HPC`, `NIPOPPY_JOB_NAME`, `NIPOPPY_COMMANDS`, `NIPOPPY_DPATH_LOGS`) are set by Nipoppy. **Every key in the step's HPC config is also passed to the template** under the same name.

### Customizing

Read and edit `code/hpc/job_script_template.sh` in the study based on use-case.
- **Same setting for every job and pipeline:** add a plain directive line inside the scheduler's block (`{% if NIPOPPY_HPC == 'slurm' %}` or the `sge` one), e.g. `#SBATCH --nice=10` or `#SBATCH --gres=gpu:1`.
- **Per-pipeline setting:** add a conditional in the template, then set the key in that pipeline's HPC config:
  ```bash
  {% if NICE %}
  #SBATCH --nice={{ NICE }}
  {%- endif %}
  ```
  and `"NICE": "10"` in `hpc.json5`. Pipelines without the key get no directive.
- **Extra per-job setup or cleanup:** add shell lines around the command, using the available shell variables: `DPATH_ROOT`, `PIPELINE_NAME`, `PIPELINE_VERSION`, `PIPELINE_STEP`, and per task `PARTICIPANT_ID` and `SESSION_ID`. For environment setup shared by all jobs, prefer `HPC_PREAMBLE` over customizing the job script template.
- Don't change lines that use `NIPOPPY_*` variables unless necessary. Don't use reserved HPC config keys: `queue`, `working_directory`, `command`, or anything starting with `NIPOPPY_`.
- To check the result, submit one participant-session with `--keep-workdir` (with user confirmation) and read the rendered `run_queue.sh` (see Troubleshooting).

## Troubleshooting

- Scheduler stdout/stderr is in `logs/hpc/`. Pipeline logs are in the usual `logs/<command>/...` locations.
- The generated job script is deleted after submission. Rerun with `--keep-workdir` to keep `scratch/work/.../run_queue.sh` for inspection.
- Editing `run_queue.sh` has no effect on future submissions. Change the template instead (see "The job script template").

## Other schedulers

- **PySQA-supported schedulers:** add `<name>.yaml` in `code/hpc/`, register it in `code/hpc/clusters.yaml`, and add an `{% elif NIPOPPY_HPC == '<name>' %}` block with that scheduler's directives to the template. Then run with `--hpc <name>`.
- **Fully manual submission:** use the write-subcohort option to dump the participant-session list to a TSV, then have each job run the command with the use-subcohort option on its share of that list.
