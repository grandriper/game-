#!/usr/bin/env python3
"""
Build a Windows .exe for Steam distribution.

Before building for release:
  1. Deploy server (see render.yaml) and get your HTTPS URL
  2. Edit server_config.json → "server_url": "https://your-server.onrender.com"
  3. Run: python build_steam.py

Output:
  dist/CrownOfExternality.exe
  dist/server_config.json  (edit without rebuilding if URL changes)
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def collect_add_data():
    """Bundle assets that exist next to game.py."""
    pairs = []

    if os.path.isfile(os.path.join(ROOT, "server_config.json")):
        pairs.append(f"server_config.json{os.pathsep}.")

    for folder in ("music", "assets"):
        path = os.path.join(ROOT, folder)
        if os.path.isdir(path):
            pairs.append(f"{folder}{os.pathsep}{folder}")

    return pairs


def main():
    os.chdir(ROOT)
    args = [
        sys.executable, "-m", "PyInstaller",
        "game.py",
        "--onefile",
        "--windowed",
        "--name=CrownOfExternality",
        "--hidden-import=config",
        "--hidden-import=display",
        "--hidden-import=requests",
        "--hidden-import=pygame",
        "--collect-all=pygame",
    ]

    icon = os.path.join(ROOT, "icon.ico")
    if os.path.isfile(icon):
        args.append(f"--icon={icon}")

    for item in collect_add_data():
        args.append(f"--add-data={item}")

    print("Building Steam executable...")
    print(" ".join(args))
    subprocess.check_call(args)

    dist = os.path.join(ROOT, "dist")
    config_src = os.path.join(ROOT, "server_config.json")
    config_dst = os.path.join(dist, "server_config.json")
    if os.path.isfile(config_src):
        shutil.copy2(config_src, config_dst)

    print("\nBuild complete:")
    print(f"  {os.path.join(dist, 'CrownOfExternality.exe')}")
    print(f"  {config_dst}")
    print("\nFor Steam: ship both files. Players connect via server_config.json HTTPS URL.\n")


if __name__ == "__main__":
    main()
