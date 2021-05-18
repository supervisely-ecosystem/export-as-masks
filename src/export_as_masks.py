import os
import numpy as np
import supervisely_lib as sly
from supervisely_lib.io.json import dump_json_file
from PIL import Image

from distutils.util import strtobool

task_id = os.environ["TASK_ID"]
TEAM_ID = int(os.environ['context.teamId'])
WORKSPACE_ID = int(os.environ['context.workspaceId'])
PROJECT_ID = int(os.environ['modal.state.slyProjectId'])

my_app = sly.AppService()

Image.MAX_IMAGE_PIXELS = None
HUMAN_MASKS = bool(strtobool(os.environ['modal.state.humanMasks']))
MACHINE_MASKS = bool(strtobool(os.environ['modal.state.machineMasks']))
THICKNESS = int(os.environ['modal.state.thickness'])


@my_app.callback("export_as_masks")
@sly.timeit
def export_as_masks(api: sly.Api, task_id, context, state, app_logger):
    project_info = api.project.get_info_by_id(PROJECT_ID)
    dataset_ids = [ds.id for ds in api.dataset.get_list(PROJECT_ID)]
    sly.logger.info('DOWNLOAD_PROJECT', extra={'title': project_info.name})
    dest_dir = os.path.join(my_app.data_dir, f'{project_info.id}_{project_info.name}')
    sly.download_project(api, project_info.id, dest_dir, dataset_ids=dataset_ids, log_progress=True)
    sly.logger.info('Project {!r} has been successfully downloaded. Starting to render masks.'.format(project_info.name))

    if MACHINE_MASKS is True or HUMAN_MASKS is True:
        project = sly.Project(directory=dest_dir, mode=sly.OpenMode.READ)
        if MACHINE_MASKS:
            machine_colors = {obj_class.name: [idx, idx, idx] for idx, obj_class in
                              enumerate(project.meta.obj_classes, start=1)}
            dump_json_file(machine_colors, os.path.join(dest_dir, 'obj_class_to_machine_color.json'), indent=2)

        for dataset in project:
            ds_progress = sly.Progress(
                'Processing dataset: {!r}/{!r}'.format(project.name, dataset.name), total_cnt=len(dataset))

            if HUMAN_MASKS is True:
                human_masks_dir = os.path.join(dataset.directory, 'masks_human')
                sly.fs.mkdir(human_masks_dir)
            if MACHINE_MASKS is True:
                machine_masks_dir = os.path.join(dataset.directory, 'masks_machine')
                sly.fs.mkdir(machine_masks_dir)

            for item_name in dataset:
                item_paths = dataset.get_item_paths(item_name)
                ann = sly.Annotation.load_json_file(item_paths.ann_path, project.meta)
                mask_img_name = os.path.splitext(item_name)[0] + '.png'

                raw_img = sly.image.read(item_paths.img_path)
                raw_img_rendered = raw_img.copy()
                if HUMAN_MASKS is True:
                    for label in ann.labels:
                        label.geometry.draw(raw_img_rendered,
                                            color=label.obj_class.color,
                                            config=label.obj_class.geometry_config,
                                            thickness=THICKNESS)
                    raw_img_rendered = ((raw_img_rendered.astype(np.uint16) + raw_img.astype(np.uint16)) / 2).astype(np.uint8)
                    sly.image.write(os.path.join(human_masks_dir, mask_img_name),
                                    np.concatenate([raw_img, raw_img_rendered], axis=1))

                if MACHINE_MASKS is True:
                    machine_mask = np.zeros(shape=ann.img_size + (3,), dtype=np.uint8)
                    for label in ann.labels:
                        label.geometry.draw(machine_mask, color=machine_colors[label.obj_class.name], thickness=THICKNESS)
                    sly.image.write(os.path.join(machine_masks_dir, mask_img_name), machine_mask)

                    ds_progress.iter_done_report()
        sly.logger.info('Finished masks rendering.'.format(project_info.name))

    full_archive_name = str(project_info.id) + '_' + project_info.name + '.tar'
    result_archive = os.path.join(my_app.data_dir, full_archive_name)
    sly.fs.archive_directory(dest_dir, result_archive)
    app_logger.info("Result directory is archived")

    upload_progress = []
    remote_archive_path = "/Export-as-masks/{}/{}".format(task_id, full_archive_name)


    def _print_progress(monitor, upload_progress):
        if len(upload_progress) == 0:
            upload_progress.append(sly.Progress(message="Upload {!r}".format(full_archive_name),
                                                total_cnt=monitor.len,
                                                ext_logger=app_logger,
                                                is_size=True))
        upload_progress[0].set_current_value(monitor.bytes_read)

    file_info = api.file.upload(TEAM_ID, result_archive, remote_archive_path,
                                lambda m: _print_progress(m, upload_progress))
    app_logger.info("Uploaded to Team-Files: {!r}".format(file_info.full_storage_url))
    api.task.set_output_archive(task_id, file_info.id, full_archive_name, file_url=file_info.full_storage_url)

    my_app.stop()


def main():
    sly.logger.info("Input arguments", extra={
        "TASK_ID": task_id,
        "context.teamId": TEAM_ID,
        "context.workspaceId": WORKSPACE_ID
    })

    # Run application service
    my_app.run(initial_events=[{"command": "export_as_masks"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main)
