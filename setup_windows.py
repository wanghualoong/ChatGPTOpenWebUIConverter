from __future__ import annotations

import sys
from cx_Freeze import Executable, setup

base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="ChatGPTOpenWebUIConverter",
    version="1.0.0",
    description="Convert ChatGPT export for OpenWebUI manual import",
    options={
        "build_exe": {
            "includes": ["tkinter"],
            "include_msvcr": True,
        },
        "bdist_msi": {
            "summary_data": {
                "author": "Your Team",
                "comments": "ChatGPT to OpenWebUI converter",
            }
        },
    },
    executables=[
        Executable(
            script="gui_app.py",
            base=base,
            target_name="ChatGPTOpenWebUIConverter.exe",
            shortcut_name="ChatGPT OpenWebUI Converter",
            shortcut_dir="ProgramMenuFolder",
        )
    ],
)
