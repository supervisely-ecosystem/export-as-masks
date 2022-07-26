import os

import numpy as np
import supervisely as sly
from supervisely._utils import generate_free_name
from supervisely.io.json import dump_json_file

import functions as f
import globals as g


@g.my_app.callback("export_as_masks")
@sly.timeit
def export_as_masks(api: sly.Api, task_id, context, state, app_logger):
    project_info = api.project.get_info_by_id(g.PROJECT_ID)
    project_dir = f.download_project(api, project_info.name, project_info.id)

    if g.MACHINE_MASKS or g.HUMAN_MASKS or g.INSTANCE_MASKS:
        project = sly.Project(directory=project_dir, mode=sly.OpenMode.READ)
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

                raw_img = sly.image.read(item_paths.img_path)
                raw_img_rendered = raw_img.copy()
                if g.HUMAN_MASKS:
                    for label in ann.labels:
                        label.geometry.draw(
                            raw_img_rendered,
                            color=label.obj_class.color,
                            config=label.obj_class.geometry_config,
                            thickness=g.THICKNESS,
                        )
                    raw_img_rendered = (
                        (raw_img_rendered.astype(np.uint16) + raw_img.astype(np.uint16))
                        / 2
                    ).astype(np.uint8)
                    sly.image.write(
                        os.path.join(human_masks_dir, mask_img_name),
                        np.concatenate([raw_img, raw_img_rendered], axis=1),
                    )

                if g.MACHINE_MASKS:
                    machine_mask = np.zeros(shape=ann.img_size + (3,), dtype=np.uint8)
                    for label in ann.labels:
                        label.geometry.draw(
                            machine_mask,
                            color=machine_colors[label.obj_class.name],
                            thickness=g.THICKNESS,
                        )
                    sly.image.write(
                        os.path.join(machine_masks_dir, mask_img_name), machine_mask
                    )

                if g.INSTANCE_MASKS:
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
                        instance_mask = np.zeros(
                            shape=ann.img_size + (3,), dtype=np.uint8
                        )
                        label.geometry.draw(
                            instance_mask, color=[255, 255, 255], thickness=g.THICKNESS
                        )
                        sly.image.write(instance_mask_path, instance_mask)

                    ds_progress.iter_done_report()
        sly.logger.info("Finished masks rendering.".format(project_info.name))

    f.upload_result_archive(
        api=api,
        task_id=task_id,
        project_id=project_info.id,
        project_name=project_info.name,
        project_dir=project_dir,
        app_logger=app_logger,
    )

    g.my_app.stop()


def main():
    sly.logger.info(
        "Input arguments",
        extra={
            "TASK_ID": g.TASK_ID,
            "context.teamId": g.TEAM_ID,
            "context.workspaceId": g.WORKSPACE_ID,
            "modal.state.slyProjectId": g.PROJECT_ID,
        },
    )

    g.my_app.run(initial_events=[{"command": "export_as_masks"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main)
