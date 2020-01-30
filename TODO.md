# TODO List

- [x] Minimum window dimensions and full screen on all three platforms.
- [ ] Prevent hibernation, ie using `caffeinate` cmd on macOS and on Windows,
      `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)`
- [ ] Implement `STRIP_UPLOADED_AUDIO`.
- [ ] Write client unit tests.
- [ ] Client standalone mode, ie run Django in a separate process. (Will need to
      build an additional Django executable with PyInstaller, however will need to
      work around
      [`PyInstaller:MERGE(...)` being broken](https://pyinstaller.readthedocs.io/en/latest/spec-files.html#multipackage-bundles).)
- [ ] Build Windows with high res manifest file:
      [link](https://github.com/cztomczak/cefpython/issues/530#issuecomment-505066492)
- [ ] Build macOS with a high DPI plist file `NSPrincipalClass = NSApplication`,
      [example here.](https://pyinstaller.readthedocs.io/en/stable/spec-files.html#spec-file-options-for-a-mac-os-x-bundle)
- [ ] Make sure server has the same DB migration version as client via the ping
      and/or auth endpoints.
- [ ] For linux PyInstaller example, need to move files to `dist/cefpython3` folder
      _or_ configure cefpython.Initialize(...) to use appropriate path settings.
      Can comment on bug [here](https://github.com/cztomczak/cefpython/issues/135).
