@echo off
REM Windows CLI for gitkey (Mac/Linux use the bash script named "gitkey")
setlocal
set "PY=%USERPROFILE%\.ssh\gitkey\lib\switch_profile.py"
if not exist "%PY%" set "PY=%~dp0lib\switch_profile.py"
if not exist "%PY%" (
  echo Error: gitkey is not installed. Run install.ps1 >&2
  exit /b 1
)
python "%PY%" %*
