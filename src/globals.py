import os
import sys
from distutils.util import strtobool
from pathlib import Path

import supervisely as sly
from PIL import Image

# from supervisely.app.v1.app_service import AppService
from dotenv import load_dotenv


if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))


api = sly.Api.from_env()
task_id = sly.env.task_id()
team_id = sly.env.team_id()
workspace_id = sly.env.workspace_id()

root_source_dir = str(Path(sys.argv[0]).parents[1])
sly.logger.info(f"Root source directory: {root_source_dir}")
sys.path.append(root_source_dir)

# app_root_directory = os.path.dirname(os.getcwd())
# sys.path.append(app_root_directory)
# sys.path.append(os.path.join(app_root_directory, "src"))
# print(f"App root directory: {app_root_directory}")
# sly.logger.info(f'PYTHONPATH={os.environ.get("PYTHONPATH", "")}')

# order matters
# from dotenv import load_dotenv
# load_dotenv(os.path.join(app_root_directory, "secret_debug.env"))
# load_dotenv(os.path.join(app_root_directory, "debug.env"))

# TASK_ID = os.environ["TASK_ID"]
TEAM_ID = int(os.environ["context.teamId"])
WORKSPACE_ID = int(os.environ["context.workspaceId"])
PROJECT_ID = int(os.environ["modal.state.slyProjectId"])

# my_app = AppService()

Image.MAX_IMAGE_PIXELS = None
HUMAN_MASKS = bool(strtobool(os.environ["modal.state.humanMasks"]))
MACHINE_MASKS = bool(strtobool(os.environ["modal.state.machineMasks"]))
INSTANCE_MASKS = bool(strtobool(os.environ["modal.state.instanceMasks"]))
THICKNESS = int(os.environ["modal.state.thickness"])

# STORAGE_DIR = my_app.data_dir
STORAGE_DIR = sly.app.get_data_dir()
