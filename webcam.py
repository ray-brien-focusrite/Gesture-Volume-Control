import cv2


class Webcam:
    def __init__(self, wCam=640, hCam=640) -> None:
        self.wCam, self.hCam = wCam, hCam
        self.cam = cv2.VideoCapture(0)

        self.cam.set(3, wCam)
        self.cam.set(4, hCam)
