@echo off
setlocal
pushd "%~dp0" || exit /b 1
set "GRAPH_PYTHON=python"
if exist ".venv\Scripts\python.exe" set "GRAPH_PYTHON=.venv\Scripts\python.exe"
set "PYTHONPATH=%CD%\src"
set "PYTHONDONTWRITEBYTECODE=1"
if /i "%~1"=="analyze" goto analyze
if /i "%~1"=="test" goto test
if /i "%~1"=="demo" goto demo
if /i "%~1"=="live" goto live
if /i "%~1"=="compare" goto compare
echo Usage: run.bat analyze configs/simple.ini [--stage reverse]
echo        run.bat test ^| demo ^| live ^| compare
set "GRAPH_STATUS=2"
goto finish
:analyze
"%GRAPH_PYTHON%" -B src\main.py --config "%~2" %3 %4 %5 %6 %7 %8 %9
goto result
:test
"%GRAPH_PYTHON%" -B -m unittest discover -s tests -v
goto result
:demo
"%GRAPH_PYTHON%" -B src\demo.py
goto result
:live
"%GRAPH_PYTHON%" -B src\demo.py --live
goto result
:compare
"%GRAPH_PYTHON%" -B src\comparison.py
:result
set "GRAPH_STATUS=%ERRORLEVEL%"
:finish
popd
exit /b %GRAPH_STATUS%
