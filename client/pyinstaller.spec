# -*- mode: python -*-
# -*- coding: utf-8 -*-

"""
This is a PyInstaller spec file.
"""

import os
import platform
from PyInstaller.building.api import PYZ, EXE, COLLECT
from PyInstaller.building.build_main import Analysis

# Constants
DEBUG = os.environ.get("CEFPYTHON_PYINSTALLER_DEBUG", False)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

a = Analysis(
    ["run.py"],
    hookspath=["."],  # To find "hook-cefpython3.py"
    datas=[
      ('assets', 'assets'),
      # Make sure migartions get included
      (os.path.join('tomato', 'migrations/*.py'), os.path.join('tomato', 'migrations')),
    ],
    win_private_assemblies=True,
    win_no_prefer_redirects=True,
)

if not os.environ.get("PYINSTALLER_CEFPYTHON3_HOOK_SUCCEEDED", None):
    raise SystemExit("Error: Pyinstaller hook-cefpython3.py script was "
                     "not executed or it failed")

pyz = PYZ(a.pure,
          a.zipped_data)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name="run",
          debug=DEBUG,
          strip=False,
          upx=False,
          console=False,
          windowed=True)

args = (exe, a.binaries, a.zipfiles, a.datas)
kwargs = {'strip': False, 'upx': False, 'name': 'run'}
cmd = COLLECT

if platform.system() == 'Darwin':
    from PyInstaller.building.osx import BUNDLE

    cmd = BUNDLE
    kwargs['name'] += '.app'
    kwargs['info_plist'] = {'NSHighResolutionCapable': 'True'}

cmd(*args, **kwargs)