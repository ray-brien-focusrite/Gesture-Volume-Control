import adapy
import numpy as np
import threading
import queue

ID = ...  # TODO:
#
# device = adapy.wait_for_device(ID, timeout=10)
#
# # TODO: stream data into here live
# device.set_main_output_level(adapy.Level.from_decibels)


class VisionVolumeController:
    """
    Bridges a numpy data stream from a computer vision module to adapy monitor volume.

    Normalises incoming data to a configurable dB range and sends it to
    set_main_output_level on a background thread, always using the most recent value
    (stale frames are dropped, so the device is never flooded).
    """

    def __init__(
        self,
        device: adapy.Ada.Device,
        db_min: float = -1000.0,  # silence threshold — adjust to taste
        db_max: float = 0.0,  # maximum output level
        data_min: float = 0.0,  # expected minimum of your CV scalar
        data_max: float = 1.0,  # expected maximum of your CV scalar
        aggregation: str = "rms",  # "rms" | "mean" | "max"
    ):
        self.device = device
        self.db_min = db_min
        self.db_max = db_max
        self.data_min = data_min
        self.data_max = data_max
        self._aggregation = aggregation

        # Size-1 queue — push always replaces the stale value so the
        # worker thread only ever acts on the latest frame.
        self._queue: queue.Queue[float] = queue.Queue(maxsize=1)
        self._thread = threading.Thread(
            target=self._worker, daemon=True, name="adapy-volume"
        )
        self._running = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def start(self) -> None:
        self._running = True
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        self._thread.join(timeout=2.0)
        adapy.shutdown()

    def push(self, data: np.ndarray) -> None:
        """
        Call this from your CV callback with each new numpy frame.
        Aggregates the array to a scalar, normalises it, and enqueues the dB value.
        """
        scalar = self._aggregate(data)
        db = self._normalise(scalar)
        self._put_latest(db)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _aggregate(self, data: np.ndarray) -> float:
        flat = np.abs(data.astype(np.float64)).ravel()
        if self._aggregation == "rms":
            return float(np.sqrt(np.mean(flat**2)))
        elif self._aggregation == "max":
            return float(np.max(flat))
        else:  # mean
            return float(np.mean(flat))

    def _normalise(self, scalar: float) -> float:
        """Linearly maps [data_min, data_max] → [db_min, db_max], clamped."""
        t = (scalar - self.data_min) / max(self.data_max - self.data_min, 1e-9)
        t = max(0.0, min(1.0, t))
        return self.db_min + t * (self.db_max - self.db_min)

    def _put_latest(self, value: float) -> None:
        """Replace stale queue value with the latest one."""
        try:
            self._queue.put_nowait(value)
        except queue.Full:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            self._queue.put_nowait(value)

    def _worker(self) -> None:
        """Dedicated thread: dequeues dB values and forwards them to adapy."""
        while self._running:
            try:
                db = self._queue.get(timeout=0.05)
                self.device.set_main_output_level(adapy.Level.from_decibels(db))
            except queue.Empty:
                continue
            except Exception as exc:
                print(f"[VisionVolumeController] adapy error: {exc}")


# Usage — wiring it into your existing CV/sounddevice loop:
#
#  import adapy
#
#  # Connect to the Focusrite device (use get_connected_devices() to find product_id)
#  device = adapy.wait_for_device(product_id=YOUR_PRODUCT_ID, timeout=10)
#
#  controller = VisionVolumeController(
#      device,
#      db_min=-60.0,   # tune: maps to data_min (e.g. no motion)
#      db_max=0.0,     # tune: maps to data_max (e.g. full motion)
#      data_min=0.0,   # min value your CV scalar can produce
#      data_max=1.0,   # max value your CV scalar can produce
#      aggregation="rms",
#  )
#  controller.start()
#
#  # Replace your sounddevice callback with this:
#  def cv_callback(numpy_frame: np.ndarray):
#      controller.push(numpy_frame)

# On shutdown:
# controller.stop()
#
# To discover your product_id at runtime:
#
#  for d in adapy.get_connected_devices():
#      print(d.get_product_name(), d.get_product_id())
#
# --------------------------------------------------------------------------------------
#
# Key design decisions:
#
#  - Size-1 queue with replacement ensures the worker never lags behind a fast CV stream
# — it always acts on the most recent frame, not a backlog
#  - Worker thread keeps adapy calls off your CV/main thread (since each call blocks for
# a round-trip device ack)
#  - Normaliser is linear; if your CV data is perceptually non-linear (e.g. pixel
# brightness), consider replacing _normalise with a log mapping
