import json
import os

import numpy as np
import supervisely as sly

from helpers import *  # noqa: F401,F403


def test_keypoints_semantic_mask_uses_class_color(run_app):
    """Old code drew keypoints in the template's node/edge colors, not the class color."""
    tpl = KeypointsTemplate()
    tpl.add_point("a", 5, 5, color=[0, 255, 0])
    tpl.add_point("b", 30, 30, color=[0, 255, 0])
    tpl.add_edge("a", "b", color=[0, 0, 255])
    kp = sly.ObjClass("pose", sly.GraphNodes, color=[255, 0, 0], geometry_config=tpl)
    meta = sly.ProjectMeta(obj_classes=[kp])
    graph = sly.GraphNodes({"a": Node(sly.PointLocation(5, 5)), "b": Node(sly.PointLocation(30, 30))})
    ann = sly.Annotation((H, W), [sly.Label(graph, kp)])
    project_dir, _, _ = run_app(
        meta, {10: [("img.jpg", ann)]}, [ds_info(10, "ds")], machine=False, semantic=True
    )
    sem = sly.image.read(os.path.join(project_dir, "ds", "masks_semantic_rgb", "img.png"))
    assert sem[5, 5].tolist() == [255, 0, 0]  # node
    assert sem[17, 17].tolist() == [255, 0, 0]  # edge keeps being drawn
    colors = json.load(open(os.path.join(project_dir, "obj_class_to_semantic_color.json")))
    assert colors == {"pose": [255, 0, 0]}
