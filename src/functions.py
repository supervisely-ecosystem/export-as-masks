from typing import Dict, Tuple

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
