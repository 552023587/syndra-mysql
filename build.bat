@echo off
echo Building Syndra MySQL Client with PyInstaller...

REM Clean previous build
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM Build with PyInstaller
pyinstaller Syndra-MySQL.spec

echo.
echo Build complete! Output in dist\Syndra-MySQL\Syndra-MySQL.exe
pause
