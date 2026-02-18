import cv2
import mediapipe as mp
import math
import numpy as np
import os
import subprocess
import sys
import urllib.request

from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

BaseOptions = mp_python.BaseOptions
HandLandmarker = mp_vision.HandLandmarker
HandLandmarkerOptions = mp_vision.HandLandmarkerOptions
VisionRunningMode = mp_vision.RunningMode

MODEL_PATH = "hand_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)

IS_MAC = sys.platform == "darwin"

# macOS volume accepts 0–100 via AppleScript; other platforms no-op for now
minVol, maxVol = 0, 100


def set_system_volume(level: float, percent: float) -> None:
    """Platform-specific volume setter."""
    if IS_MAC:
        pct = max(0, min(100, percent))
        subprocess.run(
            ["osascript", "-e", f"set volume output volume {pct}"],
            check=False,
            capture_output=True,
            text=True,
        )
    else:
        raise NotImplementedError("Windows isn't supported atm")


def ensure_model(path: str = MODEL_PATH) -> str:
    """Download the hand landmark model if it is not present locally."""
    if os.path.exists(path):
        return path
    urllib.request.urlretrieve(MODEL_URL, path)
    return path


volBar, volPer = 400, 0

# Webcam Setup
wCam, hCam = 640, 480
cam = cv2.VideoCapture(0)
cam.set(3, wCam)
cam.set(4, hCam)

model_path = ensure_model()
options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.IMAGE,
    num_hands=1,
)


def start(show: bool = True):
    # Mediapipe Hand Landmarker Model
    with HandLandmarker.create_from_options(options) as landmarker:
        while cam.isOpened():
            success, image = cam.read()
            if not success:
                continue

            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
            result = landmarker.detect(mp_image)

            lmList = []
            if result.hand_landmarks:
                hand_landmarks = result.hand_landmarks[0]
                h, w, _ = image.shape
                for id, lm in enumerate(hand_landmarks):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lmList.append([id, cx, cy])

            # Assigning variables for Thumb and Index finger position
            if len(lmList) != 0:
                x1, y1 = lmList[4][1], lmList[4][2]
                x2, y2 = lmList[8][1], lmList[8][2]

                # Marking Thumb and Index finger
                cv2.circle(image, (x1, y1), 15, (255, 255, 255))
                cv2.circle(image, (x2, y2), 15, (255, 255, 255))
                cv2.line(image, (x1, y1), (x2, y2), (0, 255, 0), 3)
                length = math.hypot(x2 - x1, y2 - y1)
                if length < 50:
                    cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 3)

                vol = np.interp(length, [50, 220], [minVol, maxVol])
                volPer = np.interp(length, [50, 220], [0, 100])
                set_system_volume(vol, volPer)
                volBar = np.interp(length, [50, 220], [400, 150])

                # Volume Bar
                cv2.rectangle(image, (50, 150), (85, 400), (0, 0, 0), 3)
                cv2.rectangle(
                    image, (50, int(volBar)), (85, 400), (0, 0, 0), cv2.FILLED
                )
                cv2.putText(
                    image,
                    f"{int(volPer)} %",
                    (40, 450),
                    cv2.FONT_HERSHEY_COMPLEX,
                    1,
                    (0, 0, 0),
                    3,
                )
            if show:
                cv2.imshow("handDetector", image)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    cam.release()


if __name__ == "__main__":
    start(show=True)
