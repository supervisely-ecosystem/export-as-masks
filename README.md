<div align="center" markdown>
<img src="https://i.imgur.com/4etyw66.png"/>


# Export only labeled items

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#How-To-Use">How To Use</a>
</p>

[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/export-as-masks)
[![views](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/export-as-masks&counter=views&label=views)](https://supervise.ly)
[![used by teams](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/export-as-masks&counter=downloads&label=used%20by%20teams)](https://supervise.ly)
[![runs](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/export-as-masks&counter=runs&label=runs&123)](https://supervise.ly)

</div>

## Overview

Application exports images, annotations, human and machine masks from [Supervisely](https://app.supervise.ly) project and prepares downloadable `.tar` archive. Human mask is an RGB mask with classes colors (semantic segementation). Classes colors for machine mask are generated automatically for class indices as pixel colors, 
e.g:
```text
{
  "kiwi": [
    1,
    1,
    1
  ],
  "lemon": [
    2,
    2,
    2
  ]
}
```
Color map for machine masks is saved to `obj_class_to_machine_color.json` file.

## How To Run 
**Step 1**: Add app to your team from [Ecosystem](https://app.supervise.ly/apps/ecosystem/export-as-masks) if it is not there.

**Step 2**: Open context menu of project -> `Download via App` -> `Export as masks` 

<img src="https://i.imgur.com/IcceeId.png" width="500"/>

**Step 3**: Select the project export options.

<img src="https://i.imgur.com/ep9i3Xb.png" width="400"/>

## How to use

After running the application, you will be redirected to the `Tasks` page. Once application processing has finished, your link for downloading will be available. Click on the `file name` to download it.

<img src="https://i.imgur.com/hibPn9b.png"/>

**Note** You can also find your converted project in: `Team Files`->`Export-as-masks`->`<appId>`->`<projectId>_<projectName>.tar`
