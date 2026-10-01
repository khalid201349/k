@echo off
chcp 65001 >nul
echo ============================================
echo   بناء ملف exe لبرنامج الإجازات
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [خطأ] Python غير مثبت أو غير موجود في PATH.
    echo حمّله من https://python.org ثم أعد المحاولة.
    pause
    exit /b 1
)

echo [1/3] تثبيت PyInstaller...
pip install --upgrade pyinstaller >nul

echo [2/3] بناء ملف exe (قد يستغرق دقيقة أو اثنتين)...
pyinstaller --onefile --windowed --name "برنامج الإجازات" leave_app_desktop.py

echo [3/3] تم!
echo الملف الجاهز موجود في: dist\برنامج الإجازات.exe
echo.
pause
