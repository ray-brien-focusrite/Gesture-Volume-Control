import subprocess
import sys

IS_MAC = sys.platform == "darwin"
MIN_VOL, MAX_VOL = 0, 100  # percentage

VOLBAR, VOLPER = 400, 0


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
