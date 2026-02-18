import cv2
import mediapipe as mp
import math
import numpy as np
import subprocess

from freq import SineWavePlayer
from model import Options, Model

from vol import MIN_VOL, MAX_VOL
from webcam import Webcam
from device import AudioDevice


# def audio_callback(indata, outdata, frames, time, status):
#     if status:
#         print(status)
#     outdata[:] = indata
#


def start(show: bool = True, sine: bool = True, audio_interface: bool = True):
    model = Model()
    cam = Webcam()

    # prep interface first
    if audio_interface:
        d = AudioDevice()
        d.setup()

    # test tone
    tone = SineWavePlayer() if sine else None
    if tone:
        tone.start()

    # camera data stream
    try:
        # Mediapipe Hand Landmarker Model
        with Options.HandLandmarker.create_from_options(model.options) as landmarker:
            while cam.cam.isOpened():
                success, image = cam.cam.read()  # TODO: refine interface
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

                    length = math.hypot(x2 - x1, y2 - y1)

                    vol = np.interp(length, [50, 220], [MIN_VOL, MAX_VOL])
                    volPer = np.interp(length, [50, 220], [0, 100])
                    # TODO: where do 50, 220 values come from ^^ ?
                    if tone:
                        tone.set_vol_per(volPer)

                    if show:
                        # Marking Thumb and Index finger
                        cv2.circle(image, (x1, y1), 15, (255, 255, 255))
                        cv2.circle(image, (x2, y2), 15, (255, 255, 255))
                        cv2.line(image, (x1, y1), (x2, y2), (0, 255, 0), 3)
                        if length < 50:
                            cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 3)
                        volBar = np.interp(length, [50, 220], [400, 150])

                        # Volume Bar
                        cv2.rectangle(image, (50, 150), (85, 400), (0, 0, 0), 3)
                        cv2.rectangle(
                            image, (50, int(volBar)), (85, 400), (0, 0, 0), cv2.FILLED
                        )
                        cv2.putText(
                            image,
                            # f"{int(volPer)} %
                            "vol value: {int(vol)} ",
                            (40, 450),
                            cv2.FONT_HERSHEY_COMPLEX,
                            1,
                            (0, 255, 255),  # yellow
                            3,
                        )

                        cv2.imshow("handDetector", image)
                else:
                    continue
                # change output vol
                # set_system_volume(vol, volPer)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        cam.cam.release()
        if tone:
            tone.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    start(show=True, sine=True, audio_interface=False)
