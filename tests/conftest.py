"""Offline test harness: runs src/main.py against a small in-memory fake of sly.Api.

No Supervisely server is contacted. The project "download" is replaced by a fake that
writes a local Supervisely project built from in-memory annotations. Run from the repo root:
    python -m pytest tests
with the SDK version from dev_requirements.txt installed (plus pytest).
"""

import importlib
import os
import sys
from types import SimpleNamespace

import numpy as np
import pytest

SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
APP_MODULES = ("globals", "functions", "main", "workflow")


def ds_info(id, name, parent_id=None, project_id=1):
    return SimpleNamespace(id=id, name=name, parent_id=parent_id, project_id=project_id)


class FakeApi:
    """Only the calls export_as_masks makes outside the (faked) project download."""

    def __init__(self, datasets, project_id=1, project_name="proj"):
        self.datasets = {d.id: d for d in datasets}
        self.project_info = SimpleNamespace(id=project_id, name=project_name)
        self.workflow_inputs = []
        self.project = SimpleNamespace(get_info_by_id=lambda id: self.project_info)
        self.dataset = SimpleNamespace(
            get_info_by_id=lambda id: self.datasets[id],
            get_list=self._get_list,
        )
        self.app = SimpleNamespace(
            workflow=SimpleNamespace(
                add_input_project=lambda id: self.workflow_inputs.append(("project", id)),
                add_input_dataset=lambda id: self.workflow_inputs.append(("dataset", id)),
                add_output_file=lambda *a, **k: None,
            )
        )

    def _get_list(self, project_id, filters=None, recursive=False, parent_id=None, **kwargs):
        if recursive:
            return list(self.datasets.values())
        return [d for d in self.datasets.values() if d.parent_id == parent_id]


def make_downloader(meta, items_by_ds, datasets):
    """Fake download_async_or_sync: writes the given items as a local sly.Project.

    items_by_ds: {dataset_id: [(item_name, ann)]}; images are black, ann.img_size sized.
    """
    import supervisely as sly

    calls = []
    by_id = {d.id: d for d in datasets}

    def parents_of(ds):
        chain = []
        while ds.parent_id is not None:
            ds = by_id[ds.parent_id]
            chain.insert(0, ds.name)
        return chain

    def download(api, project_id, dest_dir, project_info=None, dataset_ids=None, **kwargs):
        calls.append(dataset_ids)
        project = sly.Project(dest_dir, sly.OpenMode.CREATE)
        project.set_meta(meta)
        for ds in datasets:
            if dataset_ids is not None and ds.id not in dataset_ids:
                continue
            path = sly.Dataset._get_dataset_path(ds.name, parents_of(ds))
            dataset = project.create_dataset(ds.name, path)
            for item_name, ann in items_by_ds.get(ds.id, []):
                img = np.zeros(ann.img_size + (3,), dtype=np.uint8)
                dataset.add_item_np(item_name, img, ann=ann)

    download.calls = calls
    return download


@pytest.fixture
def run_app(tmp_path, monkeypatch):
    """Run export_as_masks; returns (project_dir, api, download) after the run."""
    import supervisely as sly

    def _run(
        meta,
        items_by_ds,
        datasets,
        project_id=1,
        dataset_id=None,
        human=False,
        machine=True,
        semantic=False,
        instance=False,
        thickness=2,
    ):
        api = FakeApi(datasets, project_id=project_id)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("TASK_ID", "1")
        monkeypatch.setenv("SERVER_ADDRESS", "http://sly.test")
        monkeypatch.setenv("API_TOKEN", "fake-token")
        monkeypatch.setenv("context.teamId", "8")
        monkeypatch.setenv("context.workspaceId", "9")
        for name in ("context.projectId", "modal.state.slyProjectId",
                     "context.datasetId", "modal.state.slyDatasetId"):
            monkeypatch.delenv(name, raising=False)
        if dataset_id is None:
            monkeypatch.setenv("context.projectId", str(project_id))
        else:
            monkeypatch.setenv("context.datasetId", str(dataset_id))
        flags = {
            "humanMasks": human,
            "resizeHumanMasks": False,
            "machineMasks": machine,
            "semanticRgbMasks": semantic,
            "instanceMasks": instance,
        }
        for key, value in flags.items():
            monkeypatch.setenv(f"modal.state.{key}", "true" if value else "false")
        monkeypatch.setenv("modal.state.resizePercent", "50")
        monkeypatch.setenv("modal.state.thickness", str(thickness))
        monkeypatch.setattr(sly.Api, "from_env", classmethod(lambda cls, *a, **k: api))
        result = {}

        def set_download(path, *args, **kwargs):
            result["dir"] = path
            return SimpleNamespace(id=1, name="x.tar", team_id=8)

        monkeypatch.setattr(sly.output, "set_download", set_download)
        monkeypatch.syspath_prepend(SRC_DIR)
        for mod in APP_MODULES:
            sys.modules.pop(mod, None)
        main = importlib.import_module("main")
        download = make_downloader(meta, items_by_ds, datasets)
        monkeypatch.setattr(main, "download_async_or_sync", download)
        main.export_as_masks(api)
        return result["dir"], api, download

    yield _run
    for mod in APP_MODULES:
        sys.modules.pop(mod, None)
