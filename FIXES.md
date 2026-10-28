# export-as-masks: fixes on `ecosystem-fixes-2026-10` (2026-10-28)

Lifecycle `maintained` (46,402 runs): targeted fixes only, no rewrite. Base: `origin/master`
b41ea3f (v3.3.3). Offline tests: `python -m pytest tests` (fake `sly.Api`, fake project download
that writes a local project; Python 3.14, SDK from `dev_requirements.txt`).

## Behaviour contract

- **Launch:** "Download as" on an images project or dataset (`context.projectId` /
  `context.datasetId`); headless, `src/main.py`.
- **Options (`modal.state`):** `humanMasks` (bool), `resizeHumanMasks` (bool), `resizePercent`
  (int), `machineMasks` (bool), `semanticRgbMasks` (bool), `instanceMasks` (bool), `thickness`
  (int, for lines/points/graphs).
- **Output:** the project in Supervisely format plus, per dataset folder:
  - `masks_human/<name>.png`: image and the overlay side by side;
  - `masks_machine/<name>.png`: gray, value = class index (1-based, meta order), larger objects
    first;
  - `masks_semantic_rgb/<name>.png`: class colors, in annotation order;
  - `masks_instances/<name>/<class>.png`: one 0/255 mask per object.
  - Project root: `obj_class_to_machine_color.json`, `obj_class_to_semantic_color.json`.

  Delivered as a download archive (`sly.output.set_download`). Workflow: input
  project/dataset, output file. Nested datasets keep the `parent/datasets/child` layout.

## Fixed (one commit each; old -> new tests)

| Commit | Bug | Tests old -> new |
|---|---|---|
| 9d95afe | Cuboid2d in machine/semantic/instance masks used `faces_vertices` of the human branch: crash (UnboundLocalError) with human masks off, wrong cuboid position with them on | 0/2 -> 2/2 |
| ca7c780 | AlphaMask drawn alpha-blended: class value 2 at alpha 128 written as 1; instance 128 not 255; dimmed semantic colors | 0/1 -> 1/1 |
| 0e21b7f | Keypoints in semantic RGB masks drawn in template node/edge colors, not the class color | 0/1 -> 1/1 |
| b4cdfb8 | Started from a dataset: nested datasets not exported. A parent with no own images failed with "Project is empty" (reproduced on Fruits Nested, dataset Tropical) | 0/1 -> 1/1 |
| 6f0f8da | Items with the same stem (a.jpg, a.png) overwrote each other's masks | 0/1 -> 1/1 |
| 13c2831 | Class name used as a path in instance masks: "/" creates folders, "../" writes outside `masks_instances` (path traversal) | 0/1 -> 1/1 |
| abb014a | Dataset progress reported only with instance masks on; the default run showed no progress | 0/1 -> 1/1 |
| 77cd2ac | SDK 6.73.564 cannot read projects with a Multipolygon class: every such export failed (reproduced on ccs-synthetic-source) | 0/1 -> 1/1 |

Whole suite: old code 1/10 (the baseline geometry test), branch 10/10 on SDK 6.74.10 (9/9 of the
non-Multipolygon tests also pass on 6.73.564).

## Intentional changes

- Machine/semantic/instance masks of Cuboid2d, AlphaMask and keypoints change as above (they were
  wrong).
- Dataset launch now exports the nested datasets of the selection.
- Mask names: only items whose stem repeats in a dataset get `<full name>.png`
  (`a.jpg.png`) and instance folder `<full name>/`; all other names are unchanged.
- Instance mask file names: `/` and `\` in class names become `_`.
- `instance_version` 6.15.60 -> 6.17.8 (see Image). **Product decision**: drop commit 77cd2ac to
  keep 6.15.60; then Multipolygon projects keep failing.

## Image

`supervisely/base-py-sdk-hardened:6.73.564` -> `supervisely/base-py-sdk-hardened:6.74.10` (bare
hardened base, no extra deps; Python 3.14.6; tag exists on Docker Hub). `dev_requirements.txt`
`supervisely==6.74.10`. 6.74.10 is the first SDK with Multipolygon and the lowest that fixes the
crash; newer SDKs need a higher `instance_version` (6.74.34 -> 6.17.22, 6.74.52 -> 6.18.3).
`release.yml` builds no image (unchanged). `distutils.util.strtobool` still imports on this base
(setuptools ships in it); it would break on a template-built image, which strips setuptools.

## Found, not fixed

- More than 255 classes: machine mask values are uint8, classes from the 255th on all become 255
  (no warning).
- An annotation that fails to load is logged as a warning and skipped; the task still succeeds.
- Machine and instance masks draw keypoints as nodes only (no edges); human and semantic masks
  draw the skeleton.
- Machine masks are drawn larger-first, semantic masks in annotation order: overlaps resolve
  differently between the two.
- A class colored `[0,0,0]` is invisible in semantic masks (same as background), e.g. `kp` in
  ccs-synthetic-source.
- `resizePercent` is not validated (0 or tiny values make `cv2.resize` fail).
- Code still has import-time globals (`globals.py`, module-level `api`), `print(project.meta)`.

## Dev-check plan

Run each case on the branch and on the published version (drop `--version ... --branch`).
`fleet.py run` is from the workapps root. Fruits Nested (1317) is in workspace 3 (team 4), not 733.

1. Every geometry, all mask types:
   `uv run ecosystem-fleet/fleet.py run export-as-masks --workspace 733 --project 9390 --state humanMasks=true --state machineMasks=true --state semanticRgbMasks=true --state instanceMasks=true --version ecosystem-fixes-2026-10 --branch`
   - Expected: success; archive with `root/` and `root/datasets/child/`, each with
     `masks_human`, `masks_machine`, `masks_semantic_rgb`, `masks_instances/<img>/` (parcel,
     parcel_01, kp, pin, road, ...).
   - Published v3.3.3: fails, "Unknown shape: 'multipolygon'".
2. Parent dataset with nested children:
   `uv run ecosystem-fleet/fleet.py run export-as-masks --workspace 3 --project 1317 --dataset 10122 --version ecosystem-fixes-2026-10 --branch`
   - Expected: success; 16 machine and 16 human masks under `Tropical/datasets/{Banana,Lemon,Mango,Orange,Pineapple}`.
   - Published: fails, "Project is empty".
3. Whole nested project, default options (regression):
   `uv run ecosystem-fleet/fleet.py run export-as-masks --workspace 3 --project 1317 --version ecosystem-fixes-2026-10 --branch`
   - Expected: same file list and same machine/human masks as the published version (22 images,
     rectangles only); the progress bar now moves.
4. Human masks off, machine + instance (the Cuboid2d crash path; there is no cuboid in the dev
   projects, so this only checks the branch runs):
   `uv run ecosystem-fleet/fleet.py run export-as-masks --workspace 733 --project 9390 --state humanMasks=false --state instanceMasks=true --version ecosystem-fixes-2026-10 --branch`
   - Expected: success, no `masks_human`.
   - Published: fails (Multipolygon, case 1).
