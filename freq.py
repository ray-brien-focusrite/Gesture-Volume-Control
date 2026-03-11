import threading
import numpy as np
import sounddevice as sd


DEFAULT_PITCH: float = 440.0


class SineWavePlayer:
    """Generate a continuous sine whose frequency is controlled by volPer."""

    def __init__(
        self,
        samplerate: int = 44100,
        amplitude: float = 0.2,
        freq_min: float = 200.0,
        freq_max: float = 880.0,
    ):
        self.samplerate = samplerate
        self.amplitude = amplitude
        self.freq_min = freq_min
        self.freq_max = freq_max
        self.vol_per = 50.0
        self.phase = 0.0
        self._lock = threading.Lock()
        self.stream = sd.OutputStream(
            samplerate=self.samplerate,
            channels=1,
            dtype="float32",
            callback=self._callback,
        )
        self.stream_out

    def _callback(self, outdata, frames, time, status):
        if status:
            # Ignore status flags; they are mainly underflows/overflows.
            pass
        with self._lock:
            pct = max(0.0, min(100.0, float(self.vol_per)))
            freq = self.freq_min + (self.freq_max - self.freq_min) * (pct / 100.0)
        t = (np.arange(frames, dtype=np.float32) + self.phase) / self.samplerate
        outdata[:, 0] = self.amplitude * np.sin(2 * np.pi * freq * t)
        self.phase = (self.phase + frames) % self.samplerate

    def set_vol_per(self, value: float) -> None:
        with self._lock:
            self.vol_per = value

    def start(self):
        self.stream.start()

    def stop(self):
        self.stream.stop()
        self.stream.close()
