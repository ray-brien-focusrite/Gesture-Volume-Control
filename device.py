from typing import Optional

try:
    import adapy as ada

    logging.basicConfig(level=logging.DEBUG)
    ada.enable_logging()
    ADAPY_AVAILABLE = True
except ImportError:
    print("Warning: adapy not available. Running in demo mode.")
    ADAPY_AVAILABLE = False


class AudioDevice:
    def __init__(self):
        self.max_vol = 0  # dB
        self.min_vol = -100  # dB
        self.channel_gains: dict[int, float] = {}
        self.device: Optional["ada.Device"] = None
        self.input_channels = []
        self.last_active_channels = set()

        self.init_device()

    def init_device(self):
        """Initialise connection to Scarlett device"""
        if not ADAPY_AVAILABLE:
            print("Running in demo mode - no Scarlett device")
            return

        try:
            devices = ada.get_connected_devices()
            if devices:
                self.device = devices[0]
                self.input_channels = self.device.get_inputs()
                print(f"Connected to: {self.device.get_product_name()}")
                print(f"Found {len(self.input_channels)} input channels")

                # Initialize gain tracking for all channels
                for channel in self.input_channels:
                    try:
                        gain = self.device.get_preamp_gain_for_channel(channel.id)
                        gain_db = gain.to_decibels()
                        self.channel_gains[channel.id] = gain_db
                        print(f"  {channel.name} (ID: {channel.id}): {gain_db:.1f} dB")
                    except Exception as e:
                        # Skip channels that don't support preamp gain (USB, Mixer, DSP, etc.)
                        if "not supported" not in str(e):
                            print(f"  Error reading {channel.name}: {e}")
            else:
                print("No Scarlett devices found")
        except Exception as e:
            print(f"Error initialising device: {e}")

    # TODO: revise for receiving stream of OpenCV data
    def change_gains(self):
        """Poll normalised stream within window, send to preamp gains on device if changed"""
        if not self.device:
            return

        # Only poll channels that we successfully read gains from initially
        for channel_id in list(self.channel_gains.keys()):
            try:
                gain = self.device.get_preamp_gain_for_channel(channel_id)
                new_gain = gain.to_decibels()
                old_gain = self.channel_gains.get(channel_id, new_gain)

                # Check if input data significantly changed
                if abs(new_gain - old_gain) > 0.2:  # More than 20% change
                    ch = next(
                        (c for c in self.input_channels if c.id == channel_id), None
                    )
                    ch_name = ch.name if ch else str(channel_id)
                    print(
                        f"Gain change detected on {ch_name}: {old_gain:.1f} -> {new_gain:.1f} dB"
                    )

                self.channel_gains[channel_id] = new_gain
            except Exception as e:
                if "not supported" not in str(e):
                    ch = next(
                        (c for c in self.input_channels if c.id == channel_id), None
                    )
                    ch_name = ch.name if ch else str(channel_id)
                    print(f"Error polling {ch_name}: {e}")

    #
    #
    # @property
    # def name(self):
    #     return self._name
    #
    # @name.setter
    # def name(self, name: str | None):
    #     print(f"Validing {name if name else 'if device available'}")
    #     devices: list[ada.Device] = ada.get_connected_devices()
    #     self._name = name if name in list(devices) else devices[0] if devices is not None
    #     print(f"{self._name}")
    #
    # def factory_default(self):
    #     """Use ada cli to reset the device to factory default"""
    #     # try:
    #     #     subprocess.run(
    #     #         ["ada", "device", "factory-default"], capture_output=True, text=True
    #     #     )
    #     # except Exception as e:
    #     #     raise Exception from e
    #
    #     # ada.factory_default...
    #

    # def set_routing(self):
    #     """Route usb input one to monitor 1"""
    #     command = "ada router set -s 'USB1' -d 'Monitor 1'"
    #     try:
    #         subprocess.run(command.split())
    #     except Exception as e:
    #         raise Exception from e
    #
    # def setup(self):
    #     self.factory_default()
    #     self.set_routing()
