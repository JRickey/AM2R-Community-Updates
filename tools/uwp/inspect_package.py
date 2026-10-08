#!/usr/bin/env python3
"""Inspect an AM2R UWP package without extracting or executing it."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
import zipfile


def pe_machine(data):
    if len(data) < 64 or data[:2] != b"MZ":
        raise ValueError("Not a PE executable")
    offset = struct.unpack_from("<I", data, 60)[0]
    if offset + 6 > len(data) or data[offset:offset + 4] != b"PE\0\0":
        raise ValueError("Invalid PE header")
    machine = struct.unpack_from("<H", data, offset + 4)[0]
    return {0x8664: "x64", 0x14c: "x86", 0xaa64: "arm64"}.get(machine, hex(machine))


def game_chunks(data):
    if len(data) < 8 or data[:4] != b"FORM":
        raise ValueError("Not a GameMaker FORM data file")
    end = 8 + struct.unpack_from("<I", data, 4)[0]
    if end != len(data):
        raise ValueError("GameMaker FORM length does not match file size")
    chunks = []
    offset = 8
    while offset < end:
        if offset + 8 > end:
            raise ValueError("Truncated GameMaker chunk header")
        name = data[offset:offset + 4].decode("ascii")
        size = struct.unpack_from("<I", data, offset + 4)[0]
        if offset + 8 + size > end:
            raise ValueError("GameMaker chunk extends beyond FORM")
        chunks.append({"name": name, "size": size})
        offset += 8 + size
    return chunks


def inspect(path):
    ns = {"p": "http://schemas.microsoft.com/appx/manifest/foundation/windows10"}
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError("ZIP CRC failed: " + bad)
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP entries")
        manifest = ET.fromstring(archive.read("AppxManifest.xml"))
        identity = manifest.find("p:Identity", ns)
        if identity is None:
            raise ValueError("Missing package identity")
        applications = [dict(a.attrib) for a in manifest.findall("p:Applications/p:Application", ns)]
        binaries = {}
        for name in names:
            if name.lower().endswith((".exe", ".dll")):
                binaries[name] = pe_machine(archive.read(name))
        gamefiles = {}
        for name in names:
            if name.lower().endswith(("game.win", "data.win")):
                data = archive.read(name)
                chunks = game_chunks(data)
                gamefiles[name] = {
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "chunks": chunks,
                    "has_bytecode": any(c["name"] == "CODE" and c["size"] > 4 for c in chunks),
                }
        problems = []
        if identity.get("ProcessorArchitecture") != "x64":
            problems.append("Xbox package must target x64")
        for name, machine in binaries.items():
            if machine != "x64":
                problems.append(name + " is not x64")
        for app in applications:
            executable = app.get("Executable", "").replace("\\", "/")
            if executable not in binaries:
                problems.append("Missing application executable: " + executable)
        families = [dict(a.attrib) for a in manifest.findall("p:Dependencies/p:TargetDeviceFamily", ns)]
        if not any(f.get("Name") in ("Windows.Universal", "Windows.Xbox") for f in families):
            problems.append("No Xbox-compatible target device family")
        if not applications:
            problems.append("No applications in manifest")
        if not gamefiles:
            problems.append("No GameMaker data file")
        return {
            "file": Path(path).name,
            "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            "identity": dict(identity.attrib),
            "target_device_families": families,
            "dependencies": [dict(a.attrib) for a in manifest.findall("p:Dependencies/p:PackageDependency", ns)],
            "applications": applications,
            "binaries": binaries,
            "gamefiles": gamefiles,
            "signature_present": "AppxSignature.p7x" in names,
            "signature_verified": False,
            "structural_problems": problems,
            "note": "Structural inspection only; does not establish signature trust, safety, or runtime compatibility.",
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    try:
        report = inspect(args.package)
    except (ValueError, OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as error:
        parser.exit(1, str(error) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(bool(report["structural_problems"]))
