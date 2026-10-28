import json
import os

import numpy as np
import supervisely as sly

from helpers import *  # noqa: F401,F403


def test_dataset_context_includes_nested_datasets(run_app):
    """Old code downloaded only the selected dataset, not its children."""
    cls = sly.ObjClass("box", sly.Rectangle)
    meta = sly.ProjectMeta(obj_classes=[cls])
    ann = sly.Annotation((H, W), [sly.Label(sly.Rectangle(1, 1, 5, 5), cls)])
    datasets = [
        ds_info(10, "parent"),
        ds_info(11, "child", parent_id=10),
        ds_info(12, "grandchild", parent_id=11),
        ds_info(20, "other"),
    ]
    items = {10: [("p.jpg", ann)], 11: [("c.jpg", ann)], 12: [("g.jpg", ann)], 20: [("o.jpg", ann)]}
    project_dir, api, download = run_app(meta, items, datasets, dataset_id=10)
    assert sorted(download.calls[0]) == [10, 11, 12]
    child = os.path.join(project_dir, "parent", "datasets", "child")
    grandchild = os.path.join(child, "datasets", "grandchild")
    assert os.path.isfile(os.path.join(project_dir, "parent", "masks_machine", "p.png"))
    assert os.path.isfile(os.path.join(child, "masks_machine", "c.png"))
    assert os.path.isfile(os.path.join(grandchild, "masks_machine", "g.png"))
    assert not os.path.exists(os.path.join(project_dir, "other"))
    assert api.workflow_inputs == [("dataset", 10)]
