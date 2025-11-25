import os
import sys
from distutils.util import strtobool

import supervisely as sly
from dotenv import load_dotenv
from PIL import Image

cwd = os.getcwd()
app_root_directory = os.path.dirname(cwd)
sys.path.append(app_root_directory)
sys.path.append(os.path.join(app_root_directory, "src"))
print(f"App root directory: {app_root_directory}")
sly.logger.info(f'PYTHONPATH={os.environ.get("PYTHONPATH", "")}')

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

TEAM_ID = sly.env.team_id()
WORKSPACE_ID = sly.env.workspace_id()
PROJECT_ID = sly.env.project_id(raise_not_found=False)
DATASET_ID = sly.env.dataset_id(raise_not_found=False)

sly.logger.info(
    f"Team ID: {TEAM_ID}, Workspace ID: {WORKSPACE_ID}, Project ID: {PROJECT_ID}, DATASET_ID: {DATASET_ID}"
)

api = sly.Api.from_env()

Image.MAX_IMAGE_PIXELS = None
HUMAN_MASKS = bool(strtobool(os.environ["modal.state.humanMasks"]))
RESIZE_HUMAN_MASKS = bool(strtobool(os.environ["modal.state.resizeHumanMasks"]))
RESIZE_PERCENT = int(os.environ["modal.state.resizePercent"])
MACHINE_MASKS = bool(strtobool(os.environ["modal.state.machineMasks"]))
INSTANCE_MASKS = bool(strtobool(os.environ["modal.state.instanceMasks"]))
THICKNESS = int(os.environ["modal.state.thickness"])

sly.logger.info(
    f"Export human masks: {HUMAN_MASKS}, machine masks: {MACHINE_MASKS}, "
    f"instance masks: {INSTANCE_MASKS}, thickness: {THICKNESS}"
)

SIZE_LIMIT = 10 if sly.is_community() else 100
SIZE_LIMIT_BYTES = SIZE_LIMIT * 1024 * 1024 * 1024
SPLIT_MODE = "MB"
SPLIT_SIZE = 500  # do not increase this value (memory issues)
# SPLIT_SIZE_BYTES = SPLIT_SIZE * 1024 * 1024 * 1024

STORAGE_DIR = os.path.join(cwd, "storage")
sly.fs.mkdir(STORAGE_DIR, remove_content_if_exists=True)
sly.logger.debug(f"Storage directory: {STORAGE_DIR}")
