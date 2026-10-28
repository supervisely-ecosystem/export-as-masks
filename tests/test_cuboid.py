import json
import os

import numpy as np
import supervisely as sly

from helpers import *  # noqa: F401,F403


def cuboid_case():
    cls = sly.ObjClass("cube", sly.Cuboid2d, color=[200, 0, 0],
                       geometry_config=Cuboid2dTemplate([200, 0, 0]).config)
    meta = sly.ProjectMeta(obj_classes=[cls])
    ann = sly.Annotation((H, W), [sly.Label(cuboid(2, 2), cls), sly.Label(cuboid(25, 25), cls)])
    return meta, ann


def test_cuboid_without_human_masks_does_not_crash(run_app):
    """Old code: UnboundLocalError on `faces_vertices` (only the human-mask branch set it)."""
    meta, ann = cuboid_case()
    project_dir, _, _ = run_app(
        meta, {10: [("img.jpg", ann)]}, [ds_info(10, "ds")], human=False, machine=True
    )
    m = machine_mask(project_dir, "ds", "img.png")
    assert m[4, 4] == 1 and m[28, 28] == 1


def test_every_cuboid_drawn_at_its_own_place(run_app):
    """Old code drew every cuboid with the vertices of the last cuboid of the human mask."""
    meta, ann = cuboid_case()
    project_dir, _, _ = run_app(
        meta, {10: [("img.jpg", ann)]}, [ds_info(10, "ds")],
        human=True, machine=True, semantic=True, instance=True,
    )
    m = machine_mask(project_dir, "ds", "img.png")
    assert m[4, 4] == 1, "first cuboid missing from the machine mask"
    assert m[28, 28] == 1
    sem = sly.image.read(os.path.join(project_dir, "ds", "masks_semantic_rgb", "img.png"))
    assert sem[4, 4].tolist() == [200, 0, 0]
    inst_dir = os.path.join(project_dir, "ds", "masks_instances", "img")
    first = read_gray(os.path.join(inst_dir, "cube.png"))
    second = read_gray(os.path.join(inst_dir, "cube_01.png"))
    assert first[4, 4] == 255 and first[28, 28] == 0
    assert second[28, 28] == 255 and second[4, 4] == 0
