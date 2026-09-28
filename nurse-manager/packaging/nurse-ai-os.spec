# PyInstaller build for the Nurse AI OS local app (ADR 0003).
#
#   pyinstaller --noconfirm --clean nurse-manager/packaging/nurse-ai-os.spec
#
# Produces, per platform:
#   Windows  dist/nurse-ai-os.exe          one windowed executable (no console)
#   macOS    dist/Nurse AI OS.app          an application bundle
#   Linux    dist/nurse-ai-os              one executable
# The Python runtime and every file the core reads are inside the build;
# the manager's records are not (they live in the user-data folder).
# Builds are unsigned until signing identities exist: for testing only.

import sys
from pathlib import Path

REPO = Path(SPECPATH).resolve().parents[1]  # noqa: F821 — provided by PyInstaller
MANAGER = REPO / "nurse-manager"
NAIO = REPO / "naio-integrations"

datas = [
    (str(MANAGER / "renderer"), "nurse-manager/renderer"),
    (str(MANAGER / "config"), "nurse-manager/config"),
    (str(MANAGER / "samples"), "nurse-manager/samples"),
    (str(MANAGER / "src" / "nurse_manager" / "migrations"), "nurse-manager/src/nurse_manager/migrations"),
    (str(NAIO / "config"), "naio-integrations/config"),
]

a = Analysis(  # noqa: F821
    [str(MANAGER / "packaging" / "launch.py")],
    pathex=[str(MANAGER / "src"), str(NAIO / "src")],
    datas=datas,
    hiddenimports=["naio_integrations.contract", "naio_integrations.policy",
                   "naio_integrations.privacy", "naio_integrations.deliverables"],
    excludes=["tkinter", "unittest", "pydoc", "test"],
    noarchive=False,
)
pyz = PYZ(a.pure)  # noqa: F821

if sys.platform == "darwin":
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="nurse-ai-os",  # noqa: F821
              console=False, upx=False)
    coll = COLLECT(exe, a.binaries, a.datas, name="nurse-ai-os", upx=False)  # noqa: F821
    app = BUNDLE(  # noqa: F821
        coll,
        name="Nurse AI OS.app",
        bundle_identifier="org.nurse-ai-os.manager",
        info_plist={"CFBundleShortVersionString": "0.1.0", "LSUIElement": False},
    )
else:
    exe = EXE(  # noqa: F821
        pyz, a.scripts, a.binaries, a.datas, [],
        name="nurse-ai-os",
        console=False,
        upx=False,
        runtime_tmpdir=None,
    )
