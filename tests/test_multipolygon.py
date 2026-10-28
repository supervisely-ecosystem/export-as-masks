import os

import numpy as np
import supervisely as sly

from helpers import *  # noqa: F401,F403


def test_multipolygon_project_is_exported(run_app):
    """SDK 6.73.564 has no Multipolygon: the project meta of any project with a multipolygon
    class fails to load ("Unknown shape: 'multipolygon'") and the export crashes."""
    parcel = sly.ObjClass("parcel", sly.Multipolygon, color=[50, 50, 200])
    meta = sly.ProjectMeta(obj_classes=[parcel])

    def square(t, l, s):
        return sly.Polygon([sly.PointLocation(r, c) for r, c in [(t, l), (t, l + s), (t + s, l + s), (t + s, l)]])

    meta = sly.ProjectMeta.from_json(meta.to_json())  # what the app gets from the server
    ann = sly.Annotation((H, W), [sly.Label(sly.Multipolygon([square(2, 2, 6), square(20, 20, 8)]), parcel)])
    project_dir, _, _ = run_app(
        meta, {10: [("img.jpg", ann)]}, [ds_info(10, "ds")], machine=True, semantic=True, instance=True
    )
    m = read_gray(os.path.join(project_dir, "ds", "masks_machine", "img.png"))
    assert m[4, 4] == 1 and m[24, 24] == 1 and m[14, 14] == 0
    sem = sly.image.read(os.path.join(project_dir, "ds", "masks_semantic_rgb", "img.png"))
    assert sem[24, 24].tolist() == [50, 50, 200]
    inst = read_gray(os.path.join(project_dir, "ds", "masks_instances", "img", "parcel.png"))
    assert inst[4, 4] == 255 and inst[24, 24] == 255
