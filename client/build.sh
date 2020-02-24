#!/bin/sh

rm -rf build dist

pyinstaller \
        --add-data assets:assets \
        --add-data tomato/migrations/*.py:tomato/migrations \
        --additional-hooks-dir . \
        --clean \
        --icon tomato.icns \
        --noconfirm \
        --noupx \
        --windowed \
    run.py

# High res mode on Retina displays
plutil -insert NSPrincipalClass -string NSApplication dist/run.app/Contents/Info.plist
mv -v dist/run.app dist/Tomato.app
