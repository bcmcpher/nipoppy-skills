# Creating and sharing pipeline bundles

Use this when no suitable pipeline exists on Zenodo (`nipoppy pipeline search`), or when an existing one needs a new version.

For detailed bundle authoring, use the sibling skills if they are available:
- `nipoppy-pipeline-config-from-existing-version`: make a new version from an existing bundle
- `boutiques-descriptor-creator`: write a Boutiques descriptor for a tool

## Workflow

1. **Create.** `nipoppy pipeline create <dir> --type {bidsification|processing|extraction}` scaffolds a bundle from templates. It can optionally be seeded from an existing Boutiques descriptor (`--source-descriptor`).
2. **Edit** the bundle files. Templates use `.json5`, which allows comments; the main config is always `config.json`.

   | File | Purpose |
   |---|---|
   | `config.json` | `NAME`, `VERSION`, `CONTAINER_INFO` (`FILE`, `URI`), `CONTAINER_CONFIG`, `STEPS` (each with descriptor, invocation, HPC and tracker file names; `UPDATE_STATUS` for bidsification), `VARIABLES` (become `PIPELINE_VARIABLES` on install), `PROC_DEPENDENCIES` (extraction only) |
   | `descriptor.json` | Boutiques descriptor of the tool's command line |
   | `invocation.json5` | Argument values, using Nipoppy substitutions such as `[[NIPOPPY_BIDS_PARTICIPANT_ID]]` and `[[NIPOPPY_DPATH_BIDS]]` |
   | `hpc.json5` | HPC resources (see `hpc.md`) |
   | `tracker.json5` | Processing only: `PATHS` that must exist for `SUCCESS`, and optionally `PARTICIPANT_SESSION_DIR` |
   | `zenodo.json` | Optional Zenodo metadata for upload |

3. **Validate.** Run `nipoppy pipeline validate <dir>` and fix every error.
4. **Test locally.** Run `nipoppy pipeline install --study <root> <dir>`, fill in the variables, then run `--simulate` and a single live participant-session.
5. **Upload** (only when the user asks): `nipoppy pipeline upload <dir>` with a Zenodo token file. The file must contain only the token.
   - Use the Zenodo sandbox option for trial uploads.
   - Pass the existing record ID to publish a new version of an existing record.
   - Published Zenodo records cannot be deleted, so confirm with the user first.
