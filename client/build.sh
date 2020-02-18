#!/bin/sh

rm -rf build dist

pyinstaller \
        --add-data assets:assets \
        --add-data tomato/migrations/*.py:tomato/migrations \
        --additional-hooks-dir . \
        --clean \
        --noconfirm \
        --noupx \
        --windowed \
        --icon tomato.icns \
    run.py
