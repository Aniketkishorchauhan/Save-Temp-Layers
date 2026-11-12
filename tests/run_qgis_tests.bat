@echo off
setlocal
if not defined OSGEO4W_ROOT set "OSGEO4W_ROOT=C:\OSGeo4W"
set "QT_QPA_PLATFORM=offscreen"
call "%OSGEO4W_ROOT%\bin\python-qgis-ltr.bat" -m unittest discover -s tests -v
exit /b %ERRORLEVEL%
