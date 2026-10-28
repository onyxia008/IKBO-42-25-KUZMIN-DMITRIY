@echo off
rem Запуск эмулятора: run.bat [--vfs FILE.xml] [--script FILE]
set PYTHONPATH=%~dp0src
python -m emulator %*
