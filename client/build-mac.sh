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
rm -rf dist/run

# If we have create-dmg
if which create-dmg > /dev/null
then
    create-dmg \
            --app-drop-link 200 0 \
            --icon Tomato.app 0 0 \
            --icon-size 100  \
            --volicon tomato.icns \
            --volname Tomato \
            --window-pos 200 120 \
            --window-size 450 100 \
        Tomato.dmg dist
    mv -v Tomato.dmg dist
else
    cd dist
    zip -9r tomato.zip Tomato.app
fi
