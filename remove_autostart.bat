@echo off
echo 🗑️ Удаление из автозагрузки...
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VacancyParser.lnk" 2>nul
echo ✅ Удалено
pause