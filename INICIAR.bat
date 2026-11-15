@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Instale Python 3.11 ou 3.12 de 64 bits de https://www.python.org/downloads/windows/
  echo Inclua o Python Launcher durante a instalacao.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 goto failed
)
if not exist ".venv\installed.ok" (
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 goto failed
  .venv\Scripts\python.exe -c "from pathlib import Path; Path('.venv/installed.ok').write_text('ok')"
)
.venv\Scripts\python.exe app.py %*
if errorlevel 1 goto failed
exit /b 0
:failed
echo Falha. Leia o erro acima e data\app.log, caso exista.
pause
exit /b 1
