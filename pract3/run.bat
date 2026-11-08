@echo off
rem Запуск: run.bat [файл_конфигурации]
cd /d "%~dp0"
python -m src.main %*
