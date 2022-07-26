import os

import supervisely as sly
from PIL import Image

import globals as g


def download_project(api, project_name, project_id):
    dataset_ids = [ds.id for ds in api.dataset.get_list(g.PROJECT_ID)]
    sly.logger.info("DOWNLOAD_PROJECT", extra={"title": project_name})
    dest_dir = os.path.join(g.STORAGE_DIR, f"{project_id}_{project_name}")
    sly.download_project(
        api, project_id, dest_dir, dataset_ids=dataset_ids, log_progress=True
    )
    sly.logger.info(
        "Project {!r} has been successfully downloaded. Starting to render masks.".format(
            project_name
        )
    )
    return dest_dir


def upload_result_archive(
    api, task_id, project_id, project_name, project_dir, app_logger
):
    full_archive_name = str(project_id) + "_" + project_name + ".tar"
    result_archive = os.path.join(g.my_app.data_dir, full_archive_name)
    sly.fs.archive_directory(project_dir, result_archive)
    app_logger.info("Result directory is archived")

    upload_progress = []
    remote_archive_path = f"/Export-as-masks/{task_id}_{full_archive_name}"

    def _print_progress(monitor, upload_progress):
        if len(upload_progress) == 0:
            upload_progress.append(
                sly.Progress(
                    message="Upload {!r}".format(full_archive_name),
                    total_cnt=monitor.len,
                    ext_logger=app_logger,
                    is_size=True,
                )
            )
        upload_progress[0].set_current_value(monitor.bytes_read)

    file_info = api.file.upload(
        g.TEAM_ID,
        result_archive,
        remote_archive_path,
        lambda m: _print_progress(m, upload_progress),
    )
    app_logger.info("Uploaded to Team-Files: {!r}".format(file_info.storage_path))
    api.task.set_output_archive(
        task_id=task_id,
        file_id=file_info.id,
        file_name=full_archive_name,
        file_url=file_info.storage_path,
    )


def convert2gray_and_save(mask_path, mask):
    sly.image.write(mask_path, mask)
    img = Image.open(mask_path).convert("L")
    img.save(mask_path)
