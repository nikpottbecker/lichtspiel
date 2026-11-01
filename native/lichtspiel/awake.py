"""Keep the machine and display awake during a show or armed start."""

import ctypes
import os
import subprocess
import sys


class WakeGuard:
    def __init__(self):
        self.active = False
        self.process = None

    def set_active(self, active: bool):
        if active == self.active:
            return
        self.active = active
        if sys.platform == "darwin":
            if active:
                try:
                    self.process = subprocess.Popen(
                        [
                            "/usr/bin/caffeinate",
                            "-d",
                            "-i",
                            "-m",
                            "-w",
                            str(os.getpid()),
                        ],
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except OSError:
                    self.process = None
            elif self.process is not None:
                self.process.terminate()
                self.process = None
        elif sys.platform == "win32":
            continuous = 0x80000000
            system_required = 0x00000001
            display_required = 0x00000002
            ctypes.windll.kernel32.SetThreadExecutionState(
                continuous | system_required | display_required
                if active
                else continuous
            )

    def close(self):
        self.set_active(False)
