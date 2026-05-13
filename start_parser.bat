@echo off
chcp 65001 >nul
title Парсер вакансий Python

echo ============================================
echo    🐍 Автозапуск парсера вакансий
echo ============================================
echo.

:: Переход в папку скрипта
cd /d "%~dp0"

:: Запуск веб-сервера в скрытом режиме
echo 🌐 Запуск веб-интерфейса...
start "VacancyWebServer" /MIN cmd /c "python simple_web_api.py"

:: Ждем пока сервер запустится
timeout /t 2 /nobreak >nul

:: Запуск парсера
echo 🔄 Запуск первого парсинга...
python parser.py

echo.
echo ============================================
echo    ✅ Всё готово!
echo    📊 Веб-интерфейс: http://localhost:8000
echo    📡 API: http://localhost:8000/api/vacancies
echo ============================================
echo.
echo Окно можно закрыть, сервер работает в фоне
pause