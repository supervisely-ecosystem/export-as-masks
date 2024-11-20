import os

import cv2
import numpy as np
import supervisely as sly
from supervisely._utils import generate_free_name
from supervisely.io.json import dump_json_file

import functions as f
import globals as g
import workflow as w

def export_as_masks(api: sly.Api):
    project_info = api.project.get_info_by_id(g.PROJECT_ID)
    project_dir = os.path.join(g.STORAGE_DIR, f"{project_info.id}_{project_info.name}")
    sly.logger.debug(f"Project will be saved to: {project_dir}")
    sly.Project.download(api, g.PROJECT_ID, project_dir)
    sly.logger.debug("Project downloaded.")
    w.workflow_input(api, project_info.id)

    if g.MACHINE_MASKS or g.HUMAN_MASKS or g.INSTANCE_MASKS:
        sly.logger.debug("Started mask creation...")
        project = sly.Project(directory=project_dir, mode=sly.OpenMode.READ)
        sly.logger.debug(f"Readed local project: {project.name}")
        machine_colors = None
        if g.MACHINE_MASKS:
            machine_colors = {
                obj_class.name: [idx, idx, idx]
                for idx, obj_class in enumerate(project.meta.obj_classes, start=1)
            }
            dump_json_file(
                machine_colors,
                os.path.join(project_dir, "obj_class_to_machine_color.json"),
                indent=2,
            )

        for dataset in project:
            sly.logger.info(f"Working with dataset {dataset.name}...")
            ds_progress = sly.Progress(
                "Processing dataset: {!r}/{!r}".format(project.name, dataset.name),
                total_cnt=len(dataset),
            )

            human_masks_dir = None
            if g.HUMAN_MASKS:
                human_masks_dir = os.path.join(dataset.directory, "masks_human")
                sly.fs.mkdir(human_masks_dir)
            machine_masks_dir = None
            if g.MACHINE_MASKS:
                machine_masks_dir = os.path.join(dataset.directory, "masks_machine")
                sly.fs.mkdir(machine_masks_dir)
            instances_masks_dir = None
            if g.INSTANCE_MASKS:
                instances_masks_dir = os.path.join(dataset.directory, "masks_instances")
                sly.fs.mkdir(instances_masks_dir)

            for item_name in dataset:
                item_paths = dataset.get_item_paths(item_name)
                ann = sly.Annotation.load_json_file(item_paths.ann_path, project.meta)
                mask_img_name = f"{os.path.splitext(item_name)[0]}.png"

                if g.HUMAN_MASKS:
                    sly.logger.debug("Creating human masks...")
                    raw_img = sly.image.read(item_paths.img_path)
                    overlay = raw_img.copy()

                    for label in ann.labels:
                        temp_overlay = overlay.copy()
                        if isinstance(label.geometry, sly.Cuboid2d):
                            faces_vertices = f.get_cuboid_sorted_points(label.geometry.nodes)
                            for vertices in faces_vertices:
                                cv2.fillPoly(
                                    temp_overlay, pts=[vertices], color=label.obj_class.color
                                )
                        else:
                            label.geometry.draw(
                                temp_overlay,
                                color=label.obj_class.color,
                                config=label.obj_class.geometry_config,
                                thickness=g.THICKNESS,
                            )

                        overlay = (
                            (overlay.astype(np.uint16) + temp_overlay.astype(np.uint16)) / 2
                        ).astype(np.uint8)

                    array_to_write = np.concatenate([raw_img, overlay], axis=1)

                    if g.RESIZE_HUMAN_MASKS:
                        new_dimensions = (
                            int(array_to_write.shape[0] * (g.RESIZE_PERCENT / 100)),
                            int(array_to_write.shape[1] * (g.RESIZE_PERCENT / 100)),
                            overlay.shape[2],
                        )
                        array_to_write.resize(new_dimensions)

                    sly.image.write(
                        os.path.join(human_masks_dir, mask_img_name),
                        array_to_write,
                    )

                if g.MACHINE_MASKS:
                    sly.logger.debug("Creating macnhine masks...")
                    machine_mask = np.zeros(shape=ann.img_size + (3,), dtype=np.uint8)

                    sorted_labels = sorted(ann.labels, key=lambda x: x.area, reverse=True)

                    for label in sorted_labels:
                        color = machine_colors[label.obj_class.name]
                        if isinstance(label.geometry, sly.Cuboid2d):
                            vertices = f.get_cuboid_sorted_points(label.geometry.nodes)
                            for vertices in faces_vertices:
                                cv2.fillPoly(machine_mask, pts=[vertices], color=color)
                        else:
                            label.geometry.draw(
                                machine_mask,
                                color=color,
                                thickness=g.THICKNESS,
                            )
                    machine_mask_path = os.path.join(machine_masks_dir, mask_img_name)
                    f.convert2gray_and_save(machine_mask_path, machine_mask)

                if g.INSTANCE_MASKS:
                    sly.logger.debug("Creating instance masks...")
                    used_names = []
                    for label in ann.labels:
                        mask_name = generate_free_name(
                            used_names=used_names,
                            possible_name=f"{label.obj_class.name}.png",
                            with_ext=True,
                        )
                        used_names.append(mask_name)
                        instance_mask_path = os.path.join(
                            os.path.join(
                                instances_masks_dir,
                                os.path.splitext(item_name)[0],
                                mask_name,
                            )
                        )
                        instance_mask = np.zeros(shape=ann.img_size + (3,), dtype=np.uint8)
                        if isinstance(label.geometry, sly.Cuboid2d):
                            vertices = f.get_cuboid_sorted_points(label.geometry.nodes)
                            for vertices in faces_vertices:
                                cv2.fillPoly(instance_mask, pts=[vertices], color=[255, 255, 255])
                        else:
                            label.geometry.draw(
                                instance_mask, color=[255, 255, 255], thickness=g.THICKNESS
                            )
                        f.convert2gray_and_save(instance_mask_path, instance_mask)

                    ds_progress.iter_done_report()
                sly.logger.debug(f"Finished processing dataset {dataset.name}.")
        sly.logger.info(f"Finished processing project {project.name}.")

    file_info = sly.output.set_download(project_dir)
    w.workflow_output(api, file_info)
    sly.logger.debug("Application finished, output set.")


if __name__ == "__main__":
    export_as_masks(g.api)
