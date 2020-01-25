pyinstaller ^
        --add-data assets;assets ^
        --add-data tomato\migrations\*.py;tomato\migrations ^
        --additional-hooks-dir . ^
        --clean ^
        --noconfirm ^
        --upx-exclude msvcp140.dll ^
        --upx-exclude vcruntime140.dll ^
        --win-no-prefer-redirects ^
        --win-private-assemblies ^
    run.py
