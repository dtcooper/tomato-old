rd /s /q build dist

pyinstaller ^
        --add-data assets;assets ^
        --add-data tomato\migrations\*.py;tomato\migrations ^
        --additional-hooks-dir . ^
        --clean ^
        --icon tomato.ico ^
        --noconfirm ^
        --noupx ^
        --win-no-prefer-redirects ^
        --win-private-assemblies ^
        --windowed ^
    run.py

rename dist\run\run.exe Tomato.exe
rename dist\run Tomato
