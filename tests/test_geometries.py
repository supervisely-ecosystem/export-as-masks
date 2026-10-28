import json
import os

import numpy as np
import supervisely as sly

from helpers import *  # noqa: F401,F403


def test_basic_geometries_machine_and_overlap(run_app):
    big = sly.ObjClass("big", sly.Rectangle, color=[255, 0, 0])
    holed = sly.ObjClass("holed", sly.Polygon, color=[0, 255, 0])
    small = sly.ObjClass("small", sly.Bitmap, color=[0, 0, 255])
    meta = sly.ProjectMeta(obj_classes=[big, holed, small])
    ext = [sly.PointLocation(r, c) for r, c in [(20, 20), (20, 35), (35, 35), (35, 20)]]
    hole = [sly.PointLocation(r, c) for r, c in [(25, 25), (25, 30), (30, 30), (30, 25)]]
    labels = [
        sly.Label(sly.Rectangle(0, 0, 15, 15), big),
        sly.Label(sly.Bitmap(np.ones((3, 3), bool), origin=sly.PointLocation(5, 5)), small),
        sly.Label(sly.Polygon(ext, [hole]), holed),
    ]
    ann = sly.Annotation((H, W), labels)
    datasets = [ds_info(10, "ds")]
    project_dir, _, _ = run_app(meta, {10: [("img.jpg", ann)]}, datasets)
    m = machine_mask(project_dir, "ds", "img.png")
    assert m[1, 1] == 1  # big
    assert m[6, 6] == 3  # small bitmap drawn over the larger rectangle
    assert m[22, 22] == 2  # polygon
    assert m[27, 27] == 0  # its hole
    colors = json.load(open(os.path.join(project_dir, "obj_class_to_machine_color.json")))
    assert colors == {"big": [1, 1, 1], "holed": [2, 2, 2], "small": [3, 3, 3]}
