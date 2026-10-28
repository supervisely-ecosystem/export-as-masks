import json
import os

import numpy as np
import supervisely as sly

from helpers import *  # noqa: F401,F403


def test_alpha_mask_keeps_class_value(run_app):
    """Old code: AlphaMask.draw blends color by alpha, so class 2 at alpha 128 became 1."""
    other = sly.ObjClass("other", sly.Rectangle, color=[1, 2, 3])
    soft = sly.ObjClass("soft", sly.AlphaMask, color=[200, 100, 50])
    meta = sly.ProjectMeta(obj_classes=[other, soft])
    data = np.zeros((10, 10), np.uint8)
    data[2:8, 2:8] = 128
    ann = sly.Annotation((H, W), [sly.Label(sly.AlphaMask(data, origin=sly.PointLocation(10, 10)), soft)])
    project_dir, _, _ = run_app(
        meta, {10: [("img.jpg", ann)]}, [ds_info(10, "ds")],
        machine=True, semantic=True, instance=True,
    )
    assert machine_mask(project_dir, "ds", "img.png")[14, 14] == 2
    sem = sly.image.read(os.path.join(project_dir, "ds", "masks_semantic_rgb", "img.png"))
    assert sem[14, 14].tolist() == [200, 100, 50]
    inst = read_gray(os.path.join(project_dir, "ds", "masks_instances", "img", "soft.png"))
    assert inst[14, 14] == 255
