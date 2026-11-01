from pathlib import Path


def app_root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def maps_dir() -> Path:
    return app_root_dir() / "maps"


def themes_dir() -> Path:
    return app_root_dir() / "themes"
