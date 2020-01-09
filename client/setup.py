from distutils.core import setup
import sys
import os

import py2exe  # noqa
from py2exe.hooks import windows_excludes

import cefpython3 as cefpython

windows_excludes.remove('clr')

RUNTIME_DLL = 'Python.Runtime.dll'
CEF_PATH = f'{os.path.dirname(cefpython.__file__)}{os.sep}'


def dir_files(dirname):
    return (dirname, sorted(f'{dirname}\\{file}' for file in os.listdir(dirname)))


for path in sys.path:
    runtime_dll_path = os.path.join(path, RUNTIME_DLL)
    if os.path.exists(runtime_dll_path):
        break
else:
    print(f'{RUNTIME_DLL} not found!')
    sys.exit(1)

setup(
    data_files=[
        ('assets', ['assets\\app.html']),
        dir_files('assets\\css'),
        dir_files('assets\\js'),
        dir_files('assets\\fonts\\candidates'),
        dir_files('assets\\images'),
        ('', [
            runtime_dll_path,
            f'{CEF_PATH}\\cef.pak',
            f'{CEF_PATH}\\cef_100_percent.pak',
            f'{CEF_PATH}\\cef_200_percent.pak',
            f'{CEF_PATH}\\cef_extensions.pak',
            f'{CEF_PATH}\\cefpython_py37.pyd',
            f'{CEF_PATH}\\chrome_elf.dll',
            f'{CEF_PATH}\\d3dcompiler_43.dll',
            f'{CEF_PATH}\\d3dcompiler_47.dll',
            f'{CEF_PATH}\\devtools_resources.pak',
            f'{CEF_PATH}\\icudtl.dat',
            f'{CEF_PATH}\\libEGL.dll',
            f'{CEF_PATH}\\libGLESv2.dll',
            f'{CEF_PATH}\\libcef.dll',
            f'{CEF_PATH}\\msvcp100.dll',
            f'{CEF_PATH}\\msvcp140.dll',
            f'{CEF_PATH}\\msvcp90.dll',
            f'{CEF_PATH}\\natives_blob.bin',
            f'{CEF_PATH}\\snapshot_blob.bin',
            f'{CEF_PATH}\\subprocess.exe',
            f'{CEF_PATH}\\v8_context_snapshot.bin',
            f'{CEF_PATH}\\widevinecdmadapter.dll',
        ]),
        ('locales', [f'{CEF_PATH}\\locales\\en-US.pak']),
        ('swiftshader', [
            f'{CEF_PATH}\\swiftshader\\libGLESv2.dll',
            f'{CEF_PATH}\\swiftshader\\libEGL.dll',
        ])
    ],
    options={"py2exe": {"includes": ["clr"]}},
    console=[{
        "script": "run.py",
        "dest_base": "run",
    }]
)
