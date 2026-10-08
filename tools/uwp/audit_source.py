#!/usr/bin/env python3
"""List the source/assets needed to compile the GMX project. No files are modified."""
import argparse
from collections import Counter
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def audit(root):
    project = ET.parse(root / "AM2R.project.gmx").getroot()
    counts = Counter()
    missing = []

    def require(path, kind):
        if not path.is_file():
            missing.append({"kind": kind, "path": str(path.relative_to(root))})
            return False
        return True

    for kind in ("sprite", "background", "sound", "font", "object", "room", "timeline", "script", "shader"):
        for entry in project.iter(kind):
            if not entry.text:
                continue
            counts[kind] += 1
            path = root / entry.text.replace("\\", "/")
            if kind not in ("script", "shader"):
                path = Path(str(path) + "." + kind + ".gmx")
            if not require(path, kind):
                continue
            if kind in ("script", "shader"):
                continue
            asset = ET.parse(path).getroot()
            if kind == "sprite":
                for frame in asset.findall("frames/frame"):
                    require(path.parent / frame.text.replace("\\", "/"), "sprite_image")
            elif kind in ("background", "font"):
                image = asset.findtext("data") or asset.findtext("image")
                if image:
                    require(path.parent / image.replace("\\", "/"), kind + "_image")
            elif kind == "sound":
                audio = asset.findtext("data")
                if audio:
                    require(path.parent / "audio" / audio.replace("\\", "/"), "audio")

    def datafiles(group, folder):
        for entry in group:
            if entry.tag == "datafiles":
                datafiles(entry, folder / entry.get("name", ""))
            elif entry.tag == "datafile":
                filename = entry.findtext("filename")
                if filename:
                    require(folder / filename.replace("\\", "/"), "datafile")

    for group in project.findall("datafiles"):
        datafiles(group, root / "datafiles")
    return {"resources": dict(counts), "missing_counts": dict(Counter(x["kind"] for x in missing)),
            "missing": missing, "assets_complete": not missing,
            "note": "Asset presence only; version/asset-ID compatibility and compilation require separate validation."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    report = audit(args.root)
    print(json.dumps(report, indent=2))
    raise SystemExit(not report["assets_complete"])
