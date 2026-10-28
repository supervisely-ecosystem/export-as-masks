import json
import os

import numpy as np
import supervisely as sly

from helpers import *  # noqa: F401,F403


def test_class_name_with_path_separators_stays_in_item_folder(run_app):
    """Old code used the class name as a path: '../../x' wrote outside masks_instances."""
    cls = sly.ObjClass("../../evil/x", sly.Rectangle)
    meta = sly.ProjectMeta(obj_classes=[cls])
    ann = sly.Annotation((H, W), [sly.Label(sly.Rectangle(0, 0, 9, 9), cls)])
    project_dir, _, _ = run_app(
        meta, {10: [("img.jpg", ann)]}, [ds_info(10, "ds")], machine=False, instance=True
    )
    item_dir = os.path.join(project_dir, "ds", "masks_instances", "img")
    assert os.listdir(item_dir) == [".._.._evil_x.png"]
    assert not os.path.exists(os.path.join(project_dir, "ds", "evil"))
