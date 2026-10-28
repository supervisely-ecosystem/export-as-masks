import json
import os

import numpy as np
import supervisely as sly

from helpers import *  # noqa: F401,F403


def test_items_with_same_stem_keep_their_own_masks(run_app):
    """Old code wrote both a.jpg and a.png to masks_machine/a.png; the second overwrote the first."""
    c1 = sly.ObjClass("one", sly.Rectangle)
    c2 = sly.ObjClass("two", sly.Rectangle)
    meta = sly.ProjectMeta(obj_classes=[c1, c2])
    ann1 = sly.Annotation((H, W), [sly.Label(sly.Rectangle(0, 0, 9, 9), c1)])
    ann2 = sly.Annotation((H, W), [sly.Label(sly.Rectangle(0, 0, 9, 9), c2)])
    project_dir, _, _ = run_app(
        meta, {10: [("a.jpg", ann1), ("a.png", ann2), ("b.jpg", ann1)]}, [ds_info(10, "ds")],
        machine=True, instance=True,
    )
    mdir = os.path.join(project_dir, "ds", "masks_machine")
    assert sorted(os.listdir(mdir)) == ["a.jpg.png", "a.png.png", "b.png"]
    assert read_gray(os.path.join(mdir, "a.jpg.png"))[5, 5] == 1
    assert read_gray(os.path.join(mdir, "a.png.png"))[5, 5] == 2
    idir = os.path.join(project_dir, "ds", "masks_instances")
    assert sorted(os.listdir(idir)) == ["a.jpg", "a.png", "b"]
