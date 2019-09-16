@choice /c yn /t 5 /d y /m "Is Server?"
@if ERRORLEVEL 1 python __main__.py -server True
@if ERRORLEVEL 2 python __main__.py -server False
@pause > nul