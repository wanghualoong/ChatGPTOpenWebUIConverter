#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
REQ_FILE = ROOT / "requirements.txt"


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, cwd=str(ROOT))
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def _requirements_has_packages(path: Path) -> bool:
    if not path.exists():
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if text and not text.startswith("#"):
            return True
    return False


def ensure_venv() -> Path:
    vpy = _venv_python()
    if not vpy.exists():
        print("[bootstrap] Creating virtual environment...")
        _run([sys.executable, "-m", "venv", str(VENV_DIR)])
    return vpy


def install_dependencies(vpy: Path) -> None:
    if _requirements_has_packages(REQ_FILE):
        print("[bootstrap] Installing dependencies...")
        _run([str(vpy), "-m", "pip", "install", "-r", str(REQ_FILE)])
    else:
        print("[bootstrap] No third-party dependencies to install.")


def main() -> int:
    vpy = ensure_venv()
    install_dependencies(vpy)
    cmd = [str(vpy), str(ROOT / "migrator.py"), *sys.argv[1:]]
    print("[bootstrap] Running migrator...")
    return subprocess.call(cmd, cwd=str(ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
