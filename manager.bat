@echo off
chcp 65001 >nul
title Управление парсером вакансий

:menu
cls
echo ╔══════════════════════════════════════════╗
echo ║   🐍 Парсер Python Junior Вакансий      ║
echo ╠══════════════════════════════════════════╣
echo ║  1. 🚀 Запустить всё (веб + парсер)     ║
echo ║  2. 🌐 Только веб-интерфейс             ║
echo ║  3. 👻 Веб в скрытом режиме             ║
echo ║  4. 🔄 Только парсинг сейчас            ║
echo ║  5. ⚙️  Установить в автозагрузку       ║
echo ║  6. 🗑️  Удалить из автозагрузки         ║
echo ║  7. 📊 Открыть веб в браузере           ║
echo ║  8. ⏹️  Остановить веб-сервер           ║
echo ║  9. ❌ Выйти                             ║
echo ╚══════════════════════════════════════════╝
echo.
set /p choice="Выберите действие: "

if "%choice%"=="1" goto start_all
if "%choice%"=="2" goto start_web
if "%choice%"=="3" goto start_hidden
if "%choice%"=="4" goto start_parser
if "%choice%"=="5" goto install
if "%choice%"=="6" goto remove
if "%choice%"=="7" goto open_web
if "%choice%"=="8" goto stop_web
if "%choice%"=="9" exit
goto menu

:start_all
cls
echo 🚀 Запуск всего...
cd /d "%~dp0"
start "Web" /MIN cmd /c "python simple_web_api.py"
timeout /t 2 /nobreak >nul
python parser.py
echo ✅ Готово! Веб: http://localhost:8000
pause
goto menu

:start_web
cls
echo 🌐 Запуск веб-интерфейса...
cd /d "%~dp0"
start "VacancyWeb" /MIN cmd /c "python simple_web_api.py"
timeout /t 2 /nobreak >nul
echo ✅ Веб запущен: http://localhost:8000
start http://localhost:8000
pause
goto menu

:start_hidden
cls
echo 👻 Запуск в скрытом режиме...
cd /d "%~dp0"

set /p pages="📄 Страниц (Enter = 3): "
if "%pages%"=="" set pages=3

:: Веб-сервер через vbs (полностью скрыто)
echo Set W = CreateObject("WScript.Shell") > _tmp.vbs
echo W.Run "python simple_web_api.py", 0, False >> _tmp.vbs
cscript //nologo _tmp.vbs
del _tmp.vbs
timeout /t 3 /nobreak >nul

:: Парсер через vbs (полностью скрыто)
echo Set W = CreateObject("WScript.Shell") > _tmp.vbs
echo W.Run "python parser.py %pages%", 0, False >> _tmp.vbs
cscript //nologo _tmp.vbs
del _tmp.vbs

echo ✅ Всё в фоне. Веб: http://localhost:8000
timeout /t 2 /nobreak >nul
exit

:install
cls
echo ⚙️  Установка в автозагрузку...
cd /d "%~dp0"
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VacancyParser.lnk'); $s.TargetPath='"%~dp0run_silent.vbs"'; $s.WorkingDirectory='"%~dp0"'; $s.Save()"
echo ✅ Парсер будет запускаться при входе в Windows
echo ✅ Веб-сервер запустится автоматически
pause
goto menu

:remove
cls
echo 🗑️  Удаление из автозагрузки...
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VacancyParser.lnk" 2>nul
echo ✅ Удалено
pause
goto menu

:open_web
echo 📊 Открываю веб-интерфейс...
start http://localhost:8000
timeout /t 1 /nobreak >nul
goto menu

:stop_web
cls
echo ⏹️  Остановка веб-сервера...
taskkill /FI "WINDOWTITLE eq VacancyWeb*" /T /F 2>nul
taskkill /FI "WINDOWTITLE eq Web*" /T /F 2>nul
echo ✅ Если сервер был запущен - он остановлен
echo.
echo Остановить ВСЕ процессы Python? (Y/N)
set /p kill_all=
if /i "%kill_all%"=="Y" (
    taskkill /F /IM python.exe /T 2>nul
    echo ✅ Все процессы Python остановлены
)
pause
goto menu