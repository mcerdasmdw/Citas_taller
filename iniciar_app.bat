@echo off
cd /d "%~dp0"

echo Verificando entorno uv...
if not exist ".venv" (
    echo Creando entorno virtual e instalando dependencias...
    uv sync
) else (
    echo Sincronizando dependencias...
    uv sync
)

echo Iniciando CitasTaller en http://127.0.0.1:5000/ ...
start /b uv run flask --app app run --host 127.0.0.1 --port 5000

:: Esperar a que Flask levante y abrir el navegador
timeout /t 4 >nul
start http://127.0.0.1:5000/

pause
