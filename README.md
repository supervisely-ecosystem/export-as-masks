<div align="center" markdown>
<img src="https://user-images.githubusercontent.com/106374579/186664538-21e06509-7372-44db-9f0e-512be05cad91.png"/>

# Export As Masks

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#How-To-Use">How To Use</a>
</p>

[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/export-as-masks)
[![views](https://app.supervise.ly/img/badges/views/supervisely-ecosystem/export-as-masks.png)](https://supervise.ly)
[![runs](https://app.supervise.ly/img/badges/runs/supervisely-ecosystem/export-as-masks.png)](https://supervise.ly)

</div>

## Overview

Export prepares downloadable `.tar` archive, that contains:

- original images
- annotations in [Supervisely JSON format](https://docs.supervise.ly/data-organization/00_ann_format_navi)
- human masks - RGB masks where every pixel has the color of the corresponding class (semantic segmentation)
- machine masks. Notice: if you open machine mask image in standard image viewer, it will look like completely black image, but it is not. Class colors for machine mask are generated automatically as indices of classes. `(0, 0, 0)` - is always a background (unlabeled area), (1, 1, 1) - for class #1, (2, 2, 2) - for class #2, etc ... Mapping between machine colors and classes in machine mask is saved in `obj_class_to_machine_color.json` file.
- instance masks - BW masks for every object on the image (instance segmentation)

🏋️ Starting from version v2.1.11 application supports split archives. If the archive file size is too big, it will be split into several parts. Learn more on how to extract split archives [below](#how-to-extract-split-archives).

For example:

```json
{
  "kiwi": [1, 1, 1],
  "lemon": [2, 2, 2]
}
```

Output example:

```text
<id_project_name>.tar
├── cat
│   ├── ann
│   │   ├── cats_1.jpg.json
│   │   ├── ...
│   │   └── cats_9.jpg.json
│   ├── img
│   │   ├── cats_1.jpg
│   │   ├── ...
│   │   └── cats_9.jpg
│   ├── masks_human
│   │   ├── cats_1.png
│   │   ├── ...
│   │   └── cats_9.png
│   ├── masks_instances
│   │   ├── cats_1
│   │   │   ├── cats_1.png
│   │   │   ├── ...
│   │   │   └── cats_9.png
│   │   ├── ...
│   │   └── cats_9
│   │       ├── cats_1.png
│   │       ├── ...
│   │       └── cats_9.png
│   └── masks_machine
│       ├── cats_1.png
│       ├── ...
│       └── cats_9.png
└── dog
    ├── ann
    │   ├── dogs_1.jpg.json
    │   ├── ...
    │   └── dogs_9.jpg.json
    ├── img
    │   ├── dogs_1.jpg
    │   ├── ...
    │   └── dogs_9.jpg
    ├── masks_human
    │   ├── dogs_1.png
    │   ├── ...
    │   └── dogs_9.png
    ├── masks_instances
    │   ├── dogs_1
    │   │   ├── dogs_1.png
    │   │   ├── ...
    │   │   └── dogs_9.png
    │   ├── ...
    │   └── dogs_9
    │       ├── dogs_1.png
    │       ├── ...
    │       └── dogs_9.png
    └── masks_machine
        ├── dogs_1.png
        ├── ...
        └── dogs_9.png
```

## How To Run

**Step 1**: Add app to your team from [Ecosystem](https://app.supervise.ly/apps/ecosystem/export-as-masks) if it is not there

**Step 2**: Open context menu of images project -> `Download via App` -> `Export as masks`

<img src="https://i.imgur.com/IcceeId.png" width="500"/>

**Step 3**: Define export settings in modal window

<img src="https://user-images.githubusercontent.com/48913536/181037292-4e88f6af-c4e7-4575-9f29-ac8984a70cd0.png" width="400"/>

**Step 4**: Result archive will be available for download:

- single archive: in the **Tasks list** (image below) or from **Team Files**
  - `Team Files`->`Export-as-masks`->`task_id`->`<projectId>_<projectName>.tar`
- split archive: all parts will be stored in the **Team Files** directory
  - `Team Files`->`Export-as-masks`->`<task_id>`->`<projectId>_<projectName>_part_<part_number>.tar`

<img src="https://i.imgur.com/hibPn9b.png"/>

### How to extract split archives

In the case of a split archive:

1. download all parts from `Team Files` directory (`Team Files`->`Export-as-masks`->`<task_id>`->`<projectId>_<projectName>_part_<part_number>.tar`)
2. After downloading all archive parts, you can extract them:

- for Windows:
  use the following freeware to unpack Multi-Tar files: [7-zip](https://www.7-zip.org/) and click on the first file (with extension `.tar.001`)

- for MacOS:
  replace `<path_to_folder_with_archive_parts>`, `<projectId>` and `<projectName>` with your values and run the following commands in the terminal:

```bash
cd <path_to_folder_with_archive_parts>
cat <projectId>_<projectName>.tar* | tar --options read_concatenated_archives -xvf -
```

- for Linux (Ubuntu):
  replace `<path_to_folder_with_archive_parts>`, `<projectId>` and `<projectName>` with your values and run the following commands in the terminal:

```bash
cd <path_to_folder_with_archive_parts>
cat '<projectId>_<projectName>.tar'* > result_archives.tar | tar -xvf concatenated_archives.tar
```
