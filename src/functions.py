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
    geometry.draw(canvas, color=color, config=config, thickness=thickness)
