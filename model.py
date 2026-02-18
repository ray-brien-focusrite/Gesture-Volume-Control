import os
from dataclasses import dataclass
import urllib.request

from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision


MODEL_PATH: str = "hand_landmarker.task"  # NOTE: str for mediapipe str expectation
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)


@dataclass
class Options:
    BaseOptions = mp_python.BaseOptions
    HandLandmarker = mp_vision.HandLandmarker
    HandLandmarkerOptions = mp_vision.HandLandmarkerOptions
    VisionRunningMode = mp_vision.RunningMode


def ensure_model(path: str = MODEL_PATH) -> str:
    """Download the hand landmark model if it is not present locally."""
    if os.path.exists(path):
        return path
    urllib.request.urlretrieve(MODEL_URL, path)
    return path


class Model:
    def __init__(self):
        self.model = ensure_model()
        self.options = Options.HandLandmarkerOptions(
            base_options=Options.BaseOptions(model_asset_path=model_path),
            running_mode=Options.VisionRunningMode.IMAGE,
            num_hands=1,
        )


model_path = ensure_model()
