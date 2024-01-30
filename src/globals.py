import os
import sys
from distutils.util import strtobool

import supervisely as sly
from dotenv import load_dotenv


from PIL import Image
from supervisely.app.v1.app_service import AppService

app_root_directory = os.path.dirname(os.getcwd())
sys.path.append(app_root_directory)
sys.path.append(os.path.join(app_root_directory, "src"))
print(f"App root directory: {app_root_directory}")
sly.logger.info(f'PYTHONPATH={os.environ.get("PYTHONPATH", "")}')

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

TASK_ID = os.environ["TASK_ID"]
TEAM_ID = int(os.environ["context.teamId"])
WORKSPACE_ID = int(os.environ["context.workspaceId"])
PROJECT_ID = int(os.environ["modal.state.slyProjectId"])

my_app = AppService()

Image.MAX_IMAGE_PIXELS = None
HUMAN_MASKS = bool(strtobool(os.environ["modal.state.humanMasks"]))
MACHINE_MASKS = bool(strtobool(os.environ["modal.state.machineMasks"]))
INSTANCE_MASKS = bool(strtobool(os.environ["modal.state.instanceMasks"]))
THICKNESS = int(os.environ["modal.state.thickness"])

SIZE_LIMIT = 10 # ! for tests if sly.is_community() else 100
SIZE_LIMIT_BYTES = SIZE_LIMIT * 1024 * 1024 * 1024
SPLIT_MODE = "MB"
SPLIT_SIZE = 500 # do not increase this value (memory issues)
# SPLIT_SIZE_BYTES = SPLIT_SIZE * 1024 * 1024 * 1024

STORAGE_DIR = sly.app.get_data_dir()
if sly.fs.dir_exists(STORAGE_DIR):
    sly.fs.clean_dir(STORAGE_DIR)
