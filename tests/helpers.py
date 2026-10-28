import json
import os

import numpy as np
import pytest
import supervisely as sly
from PIL import Image
from supervisely.geometry.cuboid_2d import CUBOID2D_VERTICES_NAMES, Cuboid2dTemplate
from supervisely.geometry.graph import KeypointsTemplate, Node

from conftest import ds_info  # noqa: F401

H, W = 40, 40


def read_gray(path):
    return np.array(Image.open(path))


def cuboid(top, left, size=6, shift=2):
    t, l, s, d = top, left, size, shift
    corners = [(t, l), (t, l + s), (t + s, l + s), (t + s, l)]
    corners += [(r + d, c + d) for r, c in corners]
    nodes = {n: Node(sly.PointLocation(r, c)) for n, (r, c) in zip(CUBOID2D_VERTICES_NAMES, corners)}
    return sly.Cuboid2d(nodes)



def machine_mask(project_dir, ds, item):
    return read_gray(os.path.join(project_dir, ds, "masks_machine", item))
