@echo off
chcp 65001 >nul

echo 📦 Установка в автозагрузку...

set "SCRIPT_DIR=%~dp0"
set "VBS_FILE=%SCRIPT_DIR%run_silent.vbs"

:: Создаем ярлык в автозагрузке
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VacancyParser.lnk'); $s.TargetPath='%VBS_FILE%'; $s.Save()"

echo ✅ Добавлено в автозагрузку
echo Теперь парсер будет запускаться при входе в систему
pause