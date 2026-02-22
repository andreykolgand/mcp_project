@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Сборка и запуск контейнера бота...
docker-compose up --build

pause
