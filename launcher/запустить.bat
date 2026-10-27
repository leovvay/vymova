@echo off
chcp 65001 >nul
setlocal
title Vymova
set "IMAGE=ghcr.io/leovvay/vymova:latest"
set "DATA=%USERPROFILE%\Documents\Vymova"

echo Запускаю Vymova...
docker info >nul 2>&1 && goto dockerok
echo Docker Desktop не запущен - запускаю его...
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
set /a tries=0
:waitdocker
timeout /t 5 /nobreak >nul
docker info >nul 2>&1 && goto dockerok
set /a tries+=1
if %tries% lss 24 goto waitdocker
echo.
echo Не получилось запустить Docker Desktop.
echo Установите его с https://www.docker.com/products/docker-desktop/ , перезагрузите компьютер
echo и запустите этот файл снова.
pause
exit /b 1

:dockerok
if not exist "%DATA%" mkdir "%DATA%"
echo Проверяю обновления (в первый раз скачивается несколько гигабайт)...
docker pull %IMAGE% || echo Нет связи с интернетом - запускаю уже скачанную версию.
docker rm -f vymova >nul 2>&1
docker run -d --name vymova --restart unless-stopped -p 127.0.0.1:8765:8765 -v "%DATA%:/data" -e "HOST_DATA_DIR=%DATA%" %IMAGE% >nul
if errorlevel 1 goto runfail

echo Жду, пока программа запустится...
set /a tries=0
:waitapp
timeout /t 2 /nobreak >nul
curl -s -o nul http://127.0.0.1:8765/api/settings && goto appok
set /a tries+=1
if %tries% lss 60 goto waitapp
:runfail
echo.
echo Программа не запустилась. Попробуйте ещё раз; если не поможет - перезапустите Docker Desktop.
pause
exit /b 1

:appok
start "" http://localhost:8765
echo Готово. Окно можно закрыть - программа работает в фоне.
timeout /t 5 >nul
