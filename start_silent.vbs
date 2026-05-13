Set objShell = CreateObject("Wscript.Shell")
strPath = "C:\Users\Evgeny\Documents\python\vacancy_parser"

WScript.Sleep 15000

' Веб-сервер через python (не pythonw!) — 0 = скрытое окно
objShell.Run "python """ & strPath & "\simple_web_api.py""", 0, False

WScript.Sleep 3000

' Парсер
objShell.Run "python """ & strPath & "\parser.py"" 5", 0, True