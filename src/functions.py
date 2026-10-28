import os
from copy import deepcopy
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import supervisely as sly
from PIL import Image


def convert2gray_and_save(mask_path, mask):
    sly.image.write(mask_path, mask)
    img = Image.open(mask_path).convert("L")
    img.save(mask_path)


def get_cuboid_sorted_points(vertices: Dict) -> Tuple[np.array, np.array, np.array]:
    visible_faces = [
        # front face
        ["face1-topleft", "face1-topright", "face1-bottomright", "face1-bottomleft"],
        # top face
        ["face1-topleft", "face2-topleft", "face2-topright", "face1-topright"],
        # right face
        ["face1-topright", "face2-topright", "face2-bottomright", "face1-bottomright"],
        # bottom face
        ["face1-bottomright", "face2-bottomright", "face2-bottomleft", "face1-bottomleft"],
        # left face
        ["face1-bottomleft", "face2-bottomleft", "face2-topleft", "face1-topleft"],
    ]
    faces_vertices = []
    for face in visible_faces:
        face_vertices = [[vertices[p].location.col, vertices[p].location.row] for p in face]
        faces_vertices.append(face_vertices)
    return np.array(faces_vertices)


def draw_solid(
    label: sly.Label,
    canvas: np.ndarray,
    color: List[int],
    thickness: int,
    config: Optional[Dict] = None,
) -> None:
    """Draws one label in a single color (machine, semantic RGB and instance masks)."""
    geometry = label.geometry
    if isinstance(geometry, sly.Cuboid2d):
        for vertices in get_cuboid_sorted_points(geometry.nodes):
            cv2.fillPoly(canvas, pts=[vertices], color=color)
        return
    if isinstance(geometry, sly.AlphaMask):
        # AlphaMask.draw blends the color by alpha (class value 2 at alpha 128 -> 1);
        # a mask needs the exact value wherever the object is present.
        geometry = sly.Bitmap(geometry.data > 0, origin=geometry.origin)
    if config and isinstance(geometry, sly.GraphNodes):
        # The class config carries per-node/edge template colors; keep its edges, use `color`.
        config = recolor_graph_config(config, color, geometry.items_json_field)
    geometry.draw(canvas, color=color, config=config, thickness=thickness)


def recolor_graph_config(config: Dict, color: List[int], nodes_field: str = "nodes") -> Dict:
    """Copy of a GraphNodes class config with every node and edge color set to `color`."""
    config = deepcopy(config)
    for node in (config.get(nodes_field) or {}).values():
        node["color"] = list(color)
    for edge in config.get("edges") or []:
        edge["color"] = list(color)
    return config


def dataset_with_descendants(api: sly.Api, project_id: int, dataset_id: int) -> List[int]:
    """The selected dataset id followed by the ids of all its nested datasets."""
    children = {}
    for ds in api.dataset.get_list(project_id, recursive=True):
        children.setdefault(ds.parent_id, []).append(ds.id)
    ids, queue = [], [dataset_id]
    while queue:
        current = queue.pop(0)
        ids.append(current)
        queue.extend(children.get(current, []))
    return ids


def mask_base_names(item_names: List[str]) -> Dict[str, str]:
    """Item name -> mask file name without ".png".

    The name without extension, unless another item of the dataset has the same one
    (a.jpg and a.png): then the full item name, so neither mask overwrites the other.
    """
    stems = [os.path.splitext(name)[0] for name in item_names]
    repeated = {stem for stem in stems if stems.count(stem) > 1}
    return {
        name: (name if stem in repeated else stem) for name, stem in zip(item_names, stems)
    }


def safe_file_name(name: str) -> str:
    """A class name usable as one file name: path separators replaced with "_"."""
    for sep in ("/", "\\"):
        name = name.replace(sep, "_")
    return name
