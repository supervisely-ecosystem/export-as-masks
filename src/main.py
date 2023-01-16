import os

import numpy as np
import supervisely as sly
from supervisely._utils import generate_free_name
from supervisely.io.json import dump_json_file
from distutils.util import strtobool
from PIL import Image

from dotenv import load_dotenv


if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))


api = sly.Api.from_env()

Image.MAX_IMAGE_PIXELS = None
HUMAN_MASKS = bool(strtobool(os.environ["modal.state.humanMasks"]))
MACHINE_MASKS = bool(strtobool(os.environ["modal.state.machineMasks"]))
INSTANCE_MASKS = bool(strtobool(os.environ["modal.state.instanceMasks"]))
THICKNESS = int(os.environ["modal.state.thickness"])

STORAGE_DIR = sly.app.get_data_dir()
app_name = "export-as-masks"


def download_project(api, project_name, project_id):
    dataset_ids = [ds.id for ds in api.dataset.get_list(project_id)]
    sly.logger.info("DOWNLOAD_PROJECT", extra={"title": project_name})
    dest_dir = os.path.join(STORAGE_DIR, f"{project_id}_{project_name}")
    sly.download_project(api, project_id, dest_dir, dataset_ids=dataset_ids, log_progress=True)
    sly.logger.info(
        "Project {!r} has been successfully downloaded. Starting to render masks.".format(
            project_name
        )
    )
    return dest_dir


def convert2gray_and_save(mask_path, mask):
    sly.image.write(mask_path, mask)
    img = Image.open(mask_path).convert("L")
    img.save(mask_path)


class MyExport(sly.app.Export):
    def process(self, context: sly.app.Export.Context):

        project_info = context.project
        project_dir = download_project(api, project_info.name, project_info.id)

        if MACHINE_MASKS or HUMAN_MASKS or INSTANCE_MASKS:
            project = sly.Project(directory=project_dir, mode=sly.OpenMode.READ)
            machine_colors = None
            if MACHINE_MASKS:
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
                if HUMAN_MASKS:
                    human_masks_dir = os.path.join(dataset.directory, "masks_human")
                    sly.fs.mkdir(human_masks_dir)
                machine_masks_dir = None
                if MACHINE_MASKS:
                    machine_masks_dir = os.path.join(dataset.directory, "masks_machine")
                    sly.fs.mkdir(machine_masks_dir)
                instances_masks_dir = None
                if INSTANCE_MASKS:
                    instances_masks_dir = os.path.join(dataset.directory, "masks_instances")
                    sly.fs.mkdir(instances_masks_dir)

                for item_name in dataset:
                    item_paths = dataset.get_item_paths(item_name)
                    ann = sly.Annotation.load_json_file(item_paths.ann_path, project.meta)
                    mask_img_name = f"{os.path.splitext(item_name)[0]}.png"

                    raw_img = sly.image.read(item_paths.img_path)
                    raw_img_rendered = raw_img.copy()
                    if HUMAN_MASKS:
                        for label in ann.labels:
                            label.geometry.draw(
                                raw_img_rendered,
                                color=label.obj_class.color,
                                config=label.obj_class.geometry_config,
                                thickness=THICKNESS,
                            )
                        raw_img_rendered = (
                            (raw_img_rendered.astype(np.uint16) + raw_img.astype(np.uint16)) / 2
                        ).astype(np.uint8)
                        sly.image.write(
                            os.path.join(human_masks_dir, mask_img_name),
                            np.concatenate([raw_img, raw_img_rendered], axis=1),
                        )

                    if MACHINE_MASKS:
                        machine_mask = np.zeros(shape=ann.img_size + (3,), dtype=np.uint8)
                        for label in ann.labels:
                            label.geometry.draw(
                                machine_mask,
                                color=machine_colors[label.obj_class.name],
                                thickness=THICKNESS,
                            )
                        machine_mask_path = os.path.join(machine_masks_dir, mask_img_name)
                        convert2gray_and_save(machine_mask_path, machine_mask)

                    if INSTANCE_MASKS:
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
                            label.geometry.draw(
                                instance_mask, color=[255, 255, 255], thickness=THICKNESS
                            )
                            convert2gray_and_save(instance_mask_path, instance_mask)

                        ds_progress.iter_done_report()
            sly.logger.info("Finished masks rendering.".format(project_info.name))

        full_archive_name = str(project_info.id) + "_" + project_info.name + ".tar"
        result_archive = os.path.join(STORAGE_DIR, full_archive_name)
        sly.fs.archive_directory(project_dir, result_archive)
        sly.logger.info("Result directory is archived")

        return result_archive, app_name


app = MyExport()
app.run()
