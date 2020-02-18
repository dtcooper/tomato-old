rd /s /q build dist

pyinstaller ^
        --add-data assets;assets ^
        --add-data tomato\migrations\*.py;tomato\migrations ^
        --additional-hooks-dir . ^
        --clean ^
        --noconfirm ^
        --noupx ^
        --windowed ^
        --icon tomato.ico ^
        --win-no-prefer-redirects ^
        --win-private-assemblies ^
    run.py
