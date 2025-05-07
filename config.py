import json
import os

CONFIG_FILE = "config.json"

default_config = {
    "EXCEL_PATH": "cases_review_ashraf.xlsx",
    "PDF_FOLDER": "./pdfs",
    "TXT_FOLDER": "./txts",
    "unsaved_warning": True,
    "default_theme": "clam",
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            cfg = json.load(f)
    else:
        cfg = default_config
        save_config(cfg)
    return cfg


def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)


cfg = load_config()

EXCEL_PATH = cfg.get("EXCEL_PATH", default_config["EXCEL_PATH"])
PDF_FOLDER = cfg.get("PDF_FOLDER", default_config["PDF_FOLDER"])
TXT_FOLDER = cfg.get("TXT_FOLDER", default_config["TXT_FOLDER"])
unsaved_warning = cfg.get("unsaved_warning", default_config["unsaved_warning"])
default_theme = cfg.get("default_theme", default_config["default_theme"])
