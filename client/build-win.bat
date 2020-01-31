rd /s /q build dist

pyinstaller ^
        --add-data assets;assets ^
        --add-data tomato\migrations\*.py;tomato\migrations ^
        --additional-hooks-dir . ^
        --clean ^
        --noconfirm ^
        --noupx ^
        --win-no-prefer-redirects ^
        --win-private-assemblies ^
    run.py
