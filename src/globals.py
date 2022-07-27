import os
import sys
from distutils.util import strtobool

import supervisely as sly


from PIL import Image
from supervisely.app.v1.app_service import AppService

app_root_directory = os.path.dirname(os.getcwd())
sys.path.append(app_root_directory)
sys.path.append(os.path.join(app_root_directory, "src"))
print(f"App root directory: {app_root_directory}")
sly.logger.info(f'PYTHONPATH={os.environ.get("PYTHONPATH", "")}')

# order matters
# from dotenv import load_dotenv
# load_dotenv(os.path.join(app_root_directory, "secret_debug.env"))
# load_dotenv(os.path.join(app_root_directory, "debug.env"))

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

STORAGE_DIR = my_app.data_dir
