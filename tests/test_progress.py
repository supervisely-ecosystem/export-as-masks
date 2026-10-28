import json
import os

import numpy as np
import supervisely as sly

from helpers import *  # noqa: F401,F403


def test_progress_reported_for_every_item_without_instance_masks(run_app, monkeypatch):
    """Old code reported dataset progress only inside the instance-mask branch."""
    done = []
    monkeypatch.setattr(sly.Progress, "iter_done_report", lambda self: done.append(self.message))
    cls = sly.ObjClass("box", sly.Rectangle)
    meta = sly.ProjectMeta(obj_classes=[cls])
    ann = sly.Annotation((H, W), [sly.Label(sly.Rectangle(1, 1, 5, 5), cls)])
    run_app(meta, {10: [("a.jpg", ann), ("b.jpg", ann)]}, [ds_info(10, "ds")], machine=True)
    assert len([m for m in done if "ds" in m]) == 2
