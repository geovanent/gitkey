@echo off
REM Windows entrypoint — Mac/Linux use ./install (bash)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
