import subprocess


class AudioDevice:
    def factory_default(self):
        """Use ada cli to reset the device to factory default"""
        try:
            subprocess.run(
                ["ada", "devicefactory-default"], capture_output=True, text=True
            )
        except Exception as e:
            raise Exception from e

    def set_routing(self):
        """Route usb input one to monitor 1"""
        command = "ada router set -s 'USB1' -d 'Monitor 1'"
        try:
            subprocess.run(command.split())
        except Exception as e:
            raise Exception from e

    def setup(self):
        self.factory_default()
        self.set_routing()
