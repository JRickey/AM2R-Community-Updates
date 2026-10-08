# AM2R Xbox UWP bring-up

Status: source preparation and package investigation, **not a newly compiled or
tested Xbox port**. Branch: `xbox-uwp`. Upstream base: `e500c5e`.

## What is available

- Public AM2R Community Updates GM:S 1.4 source, with 1.5.3 in its Windows version
  settings. The upstream GitHub repository was archived in February 2026.
- A downloaded original 1.1 release for reference and patcher input.
- An independently archived 1.5.2 UWP package for baseline testing. This is someone
  else's build, not a build of this branch. Its publisher label is
  `Idiot Ports Ltd.` and its identity is `AM2R`, `CN=Sandbox`, version `1.5.2.0`.
- Windows SSH build host with Visual Studio 2022 Community, MSVC 14.44.35207,
  Windows SDK 10.0.26100.0, MakeAppx and SignTool.

The archived package contains x64 `WinUAPRunner.exe`, `game.dll`, and
`cpprest140_uwp_2_9.dll`. It targets Windows.Universal, minimum 10.0.14393.0,
and depends on Microsoft.VCLibs.140.00 version 14.0.24123.0 or newer.
Its `Assets/game.win` has no CODE chunk; together with `game.dll`, this indicates
a native/YYC build. Swapping in modified GML or a VM data.win is not a supported
way to update this package.

Windows SignTool `/pa /v` rejected its certificate chain because the Sandbox
self-signed root is not trusted on the build host. No certificate was imported
and the package was not installed. ZIP CRC, manifest, PE architecture and FORM
chunk checks passed; those checks do not establish signing trust or playability.

## Changes in this branch

The desktop/UWP input path now keeps the current gamepad while it is connected
and searches available slots when that controller disappears. Previously the
active global index was initialized to zero and never reassigned in that path.
The existing scanner is now registered at the end of the GMX script list and
uses the runtime's device-slot count instead of a hard-coded twelve slots.
Existing asset ordering is preserved.

These GML changes require compiler and runtime testing. They do not yet implement
suspend/resume, console user association, or a controller-disconnected overlay.

## Reproducible checks

From the repository root, with Python 3:

```sh
python3 -m unittest discover -s tools/uwp -p 'test_*.py' -v
python3 tools/uwp/audit_source.py > source-audit.json
python3 tools/uwp/inspect_package.py /path/to/AM2R-V1.5.2-UWP.appx
```

The source audit intentionally exits 1 when assets are missing. The clean source
checkout lacks 7,420 sprite images, 329 background images, 386 audio files,
8 font images, 2 palette-swap scripts, 2 shaders, and 55 datafiles. These are the
upstream asset exclusions, not proof of a broken download. The audit checks
presence, not whether asset versions or IDs match.

On the Windows build machine:

```powershell
powershell -NoProfile -File tools\uwp\windows-preflight.ps1
# Optional explicit location for a nonstandard GameMaker installation:
powershell -NoProfile -File tools\uwp\windows-preflight.ps1 -GameMakerPath C:\Tools\GameMaker
```

Preflight reads installation locations only. Exit 1 means a prerequisite was not
found; exit 2 means exporter/version/entitlement still requires a compile probe.
It never installs software, reads license contents, or contacts the Xbox.
The package inspector checks ZIP CRCs, manifest architecture/device family,
PE architectures, and GameMaker chunk bounds. It does not authenticate signatures
or claim the game runs.

## Next build gate

1. Establish a usable GameMaker compiler and Xbox-capable UWP exporter. No
   installation was found in the inspected common locations on the Windows host.
   The GMX `option_winUAP_*` fields alone do not establish Xbox support.
2. Populate an isolated working copy using a **matching** Community Updates build
   and GMXDataSync, following the upstream README. Do not mix the archived console
   1.5.2 assets with the 1.5.3 source by asset ID. Supply the excluded shaders or
   upstream-recommended default replacements and the palette-swap scripts before
   opening the project in GameMaker.
3. Prove a desktop build first. Export an x64 UWP build with a distinct development
   package identity, so it does not replace the archived baseline or its saves.
4. Validate the generated package, controller reconnects, writable save paths,
   audio, and suspend/resume on Windows before Xbox testing.
5. Ask the user to switch the Xbox to developer mode, then test fresh boot, a new
   save/load cycle, gameplay, pause/map, controller disconnect/reconnect, and
   suspend/resume. Do not reset or overwrite existing saves.

GameMaker's official older-SDK guidance says UWP was removed starting with
2022.8. A pre-2022.8 installation with the appropriate export entitlement is a
candidate migration route; newer desktop-only GameMaker is not a drop-in UWP
compiler. Versions 2.3.4 and newer in that guidance require VS 2019, which was not
found here. The available VS 2022/SDK tools support package work but do not prove
compatibility with a legacy exporter.

OpenGM is an alternative research route, not an immediate fallback: the inspected
project targets .NET 10 and uses OpenTK/NAudio/OpenAL. It would require a separate
runtime and graphics/audio platform port and AM2R compatibility work.

## Provenance

Downloaded archives and packages stay local; they are not committed to this fork.
SHA-256 hashes identify the downloads; they do not authenticate their authors.

| Input | Source | SHA-256 |
| --- | --- | --- |
| AM2R_11.zip | [Original releases archive](https://archive.org/details/project-am2r-another-metroid-2-remake), `Full Releases/1.1/AM2R_11.zip` | `fa3d0931baf8b218b6a8b4ce9eb8e18ca11e142c34f0b404d405d8300ef0fa4c` |
| XBOX Port.zip | [Archived launcher and ports](https://archive.org/details/am-2-rlauncher-2.2.0-win-android) | `f9e9b8a7ed2df6670ac2c8a7e96e28c60cd9c18d9150d6be4da5935587c3d9a7` |
| AM2R-V1.5.2-UWP.appx | Extracted from XBOX Port.zip | `b3a3675bd58c1a22041f75de3a33cc5124b244eaf499980a48022a7739b8de1f` |

References: [upstream source and restoration instructions](https://github.com/AM2R-Community-Developers/AM2R-Community-Updates),
[GameMaker legacy SDK requirements](https://gamemaker.io/en/help/articles/required-sdks-for-old-gms2-versions),
[GM:S 1.4 import guidance](https://gamemaker.io/en/help/articles/porting-a-gms-1-4-game-to-gamemaker),
[OpenGM project](https://github.com/misternebula/OpenGM).
