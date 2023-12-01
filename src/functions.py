import os
import time

import supervisely as sly
from PIL import Image

import globals as g


def _download_batch_with_retry(api: sly.Api, dataset_id, image_ids):
    retry_cnt = 5
    curr_retry = 0
    while curr_retry <= retry_cnt:
        try:
            imgs_bytes = api.image.download_bytes(dataset_id, image_ids)
            if len(imgs_bytes) != len(image_ids):
                raise RuntimeError(
                    f"Downloaded {len(imgs_bytes)} images, but {len(image_ids)} expected."
                )
            return imgs_bytes
        except Exception as e:
            curr_retry += 1
            if curr_retry <= retry_cnt:
                time.sleep(2**curr_retry)
                sly.logger.warn(
                    f"Failed to download images, retry {curr_retry} of {retry_cnt}... Error: {e}"
                )
    raise RuntimeError(
        f"Failed to download images with ids {image_ids}. Check your data and try again later."
    )


def _download_project(api: sly.Api, project_id, dest_dir, dataset_ids=None, log_progress=False):
    dataset_ids = set(dataset_ids) if (dataset_ids is not None) else None
    project_fs = sly.Project(dest_dir, sly.OpenMode.CREATE)
    meta = sly.ProjectMeta.from_json(api.project.get_meta(project_id))
    project_fs.set_meta(meta)

    for dataset_info in api.dataset.get_list(project_id):
        dataset_id = dataset_info.id
        if dataset_ids is not None and dataset_id not in dataset_ids:
            continue

        dataset_fs = project_fs.create_dataset(dataset_info.name)
        images = api.image.get_list(dataset_id)

        ds_progress = None
        if log_progress:
            ds_progress = sly.Progress(
                "Downloading dataset: {!r}".format(dataset_info.name),
                total_cnt=len(images),
            )

        for batch in sly.batched(images, batch_size=10):
            image_ids = [image_info.id for image_info in batch]
            image_names = [image_info.name for image_info in batch]

            # download images
            batch_imgs_bytes = _download_batch_with_retry(api, dataset_id, image_ids)

            # download annotations in json format
            ann_infos = api.annotation.download_batch(dataset_id, image_ids)
            ann_jsons = [ann_info.annotation for ann_info in ann_infos]

            for name, img_bytes, ann in zip(image_names, batch_imgs_bytes, ann_jsons):
                dataset_fs.add_item_raw_bytes(item_name=name, item_raw_bytes=img_bytes, ann=ann)

            if log_progress:
                ds_progress.iters_done_report(len(batch))


def download_project(api, project_name, project_id):
    dataset_ids = [ds.id for ds in api.dataset.get_list(g.PROJECT_ID)]
    sly.logger.info("DOWNLOAD_PROJECT", extra={"title": project_name})
    dest_dir = os.path.join(g.STORAGE_DIR, f"{project_id}_{project_name}")
    _download_project(api, project_id, dest_dir, dataset_ids=dataset_ids, log_progress=True)
    sly.logger.info(
        "Project {!r} has been successfully downloaded. Starting to render masks.".format(
            project_name
        )
    )
    return dest_dir


def upload_result_archive(api, task_id, project_id, project_name, project_dir, app_logger):
    full_archive_name = str(project_id) + "_" + project_name + ".tar"
    result_archive = os.path.join(g.my_app.data_dir, full_archive_name)
    sly.fs.archive_directory(project_dir, result_archive)
    app_logger.info("Result directory is archived")

    upload_progress = []
    remote_archive_path = os.path.join(
        sly.team_files.RECOMMENDED_EXPORT_PATH, f"export-as-masks/{task_id}_{full_archive_name}"
    )

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
