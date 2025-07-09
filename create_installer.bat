@echo off
echo Membuat installer Launchpad Macro...

cd /d "%~dp0"

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Perlu hak akses Administrator untuk menginstal.
    echo Silakan jalankan sebagai Administrator.
    pause
    exit /b 1
)

if not exist "gui.py" (
    echo Error: File gui.py tidak ditemukan!
    echo Pastikan Anda menjalankan script ini dari folder yang benar.
    echo Lokasi saat ini: %CD%
    pause
    exit /b 1
)

if not exist "assets\apiunggun1.png" (
    echo Error: File assets\apiunggun1.png tidak ditemukan!
    echo Pastikan folder assets ada dan berisi file yang diperlukan.
    echo Lokasi saat ini: %CD%
    pause
    exit /b 1
)

echo.
echo Menginstal PyInstaller...
pip install pyinstaller

echo.
echo Membangun executable...
python -m PyInstaller --onefile --windowed --icon="assets\apiunggun1.png" --name="Launchpad-Macro" --add-data="assets;assets" --version-file="version.txt" --clean --noconfirm "gui.py"

if not exist "dist\Launchpad-Macro.exe" (
    echo Error: Gagal membuat executable!
    echo Silakan periksa pesan error di atas.
    pause
    exit /b 1
)

echo.
echo Menginstal ke Program Files...
set "APP_DIR=C:\Program Files\Launchpad-Macro"
if not exist "%APP_DIR%" mkdir "%APP_DIR%"

copy "dist\Launchpad-Macro.exe" "%APP_DIR%"
if errorlevel 1 (
    echo Error: Gagal menyalin executable ke Program Files!
    pause
    exit /b 1
)

copy "assets\apiunggun1.png" "%APP_DIR%"
if errorlevel 1 (
    echo Error: Gagal menyalin file icon ke Program Files!
    pause
    exit /b 1
)

set /p "ADD_STARTUP=Apakah Anda ingin Launchpad Macro berjalan saat startup? (Y/N): "
if /i "%ADD_STARTUP%"=="Y" (
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut(\"$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\Launchpad-Macro.lnk\"); $Shortcut.TargetPath = \"%APP_DIR%\\Launchpad-Macro.exe\"; $Shortcut.WorkingDirectory = \"%APP_DIR%\\\"; $Shortcut.Description = \"Launchpad Macro\"; $Shortcut.IconLocation = \"%APP_DIR%\\apiunggun1.png\\\"; $Shortcut.Save();"
    if errorlevel 0 (
        echo Shortcut startup berhasil dibuat.
    ) else (
        echo Gagal membuat shortcut startup.
    )
)

set /p "ADD_DESKTOP=Apakah Anda ingin membuat shortcut di desktop? (Y/N): "
if /i "%ADD_DESKTOP%"=="Y" (
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut(\"$env:USERPROFILE\\Desktop\\Launchpad-Macro.lnk\"); $Shortcut.TargetPath = \"%APP_DIR%\\Launchpad-Macro.exe\"; $Shortcut.WorkingDirectory = \"%APP_DIR%\\\"; $Shortcut.Description = \"Launchpad Macro\"; $Shortcut.IconLocation = \"%APP_DIR%\\apiunggun1.png\\\"; $Shortcut.Save();"
    if errorlevel 0 (
        echo Shortcut desktop berhasil dibuat.
    ) else (
        echo Gagal membuat shortcut desktop.
    )
    pause :: Pause setelah membuat shortcut desktop
)

set /p "ADD_STARTMENU=Apakah Anda ingin membuat shortcut di Start Menu? (Y/N): "
if /i "%ADD_STARTMENU%"=="Y" (
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut(\"$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\Launchpad-Macro.lnk\"); $Shortcut.TargetPath = \"%APP_DIR%\\Launchpad-Macro.exe\\\"; $Shortcut.WorkingDirectory = \"%APP_DIR%\\\"; $Shortcut.Description = \"Launchpad Macro\"; $Shortcut.IconLocation = \"%APP_DIR%\\apiunggun1.png\\\"; $Shortcut.Save();"
    if errorlevel 0 (
        echo Shortcut Start Menu berhasil dibuat.
    ) else (
        echo Gagal membuat shortcut Start Menu.
    )
    pause :: Pause setelah membuat shortcut Start Menu
)


echo.
echo Membuat uninstaller...
(
echo @echo off
echo setlocal enabledelayedexpansion
echo.
echo :: Cek hak akses admin
echo net session ^>nul 2^>^&1
echo if %%errorLevel%% neq 0 (
echo     echo Perlu hak akses Administrator untuk menghapus.
echo     echo Silakan jalankan sebagai Administrator.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo Menghapus Launchpad Macro...
echo.
echo :: Hapus shortcut
echo set "STARTUP_FOLDER=%%APPDATA%%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
echo set "DESKTOP_FOLDER=%%USERPROFILE%%\\Desktop"
echo set "START_MENU=%%APPDATA%%\\Microsoft\\Windows\\Start Menu\\Programs"
echo.
echo if exist "%%STARTUP_FOLDER%%\\Launchpad-Macro.lnk" del "%%STARTUP_FOLDER%%\\Launchpad-Macro.lnk"
echo if exist "%%DESKTOP_FOLDER%%\\Launchpad-Macro.lnk" del "%%DESKTOP_FOLDER%%\\Launchpad-Macro.lnk"
echo if exist "%%START_MENU%%\\Launchpad-Macro.lnk" del "%%START_MENU%%\\Launchpad-Macro.lnk"
echo.
echo :: Hapus folder aplikasi
echo set "APP_DIR=C:\Program Files\Launchpad-Macro"
echo if exist "%%APP_DIR%%" rmdir /s /q "%%APP_DIR%%"
echo.
echo :: Hapus folder konfigurasi
echo set "CONFIG_DIR=%%APPDATA%%\\Launchpad-Macro"
echo if exist "%%CONFIG_DIR%%" rmdir /s /q "%%CONFIG_DIR%%"
echo.
echo echo.
echo echo Uninstall selesai!
echo echo.
echo pause
) > "%APP_DIR%\uninstall.bat"

echo.
echo Instalasi selesai!
echo Launchpad Macro telah diinstal di: %APP_DIR%
echo.
pause