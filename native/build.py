"""Create an unsigned Qt desktop preview with PyInstaller."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
subprocess.run(
    [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onedir",
        "--name",
        "Lichtspiel",
        "--distpath",
        str(ROOT / "release" / "native"),
        "--workpath",
        str(ROOT / "build" / "native"),
        "--specpath",
        str(ROOT / "build" / "native"),
        "--add-data",
        f"{ROOT / 'electron' / 'assets' / 'projection-test.png'}{os.pathsep}lichtspiel/assets",
        str(ROOT / "native" / "main.py"),
    ],
    cwd=ROOT,
    check=True,
)
