@echo off
REM ------------------------------------------------------------
REM Abre la interfaz del analizador (doble clic en este archivo).
REM La primera vez crea el entorno virtual e instala las dependencias.
REM ------------------------------------------------------------
setlocal
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo Creando el entorno virtual por primera vez...
    py -3 -m venv venv 2>nul || python -m venv venv
    if errorlevel 1 (
        echo No se encontro Python. Instale Python 3.10 o superior desde https://www.python.org
        pause
        exit /b 1
    )
)

"venv\Scripts\python.exe" -c "import ply" 2>nul
if errorlevel 1 (
    echo Instalando dependencias ^(requirements.txt^)...
    "venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo No se pudieron instalar las dependencias.
        pause
        exit /b 1
    )
)

start "" "venv\Scripts\pythonw.exe" interfaz.py %*
