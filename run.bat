@echo off
setlocal enabledelayedexpansion
title ArthurTech (skufaddon) - one-click
cd /d "%~dp0"

echo ==================================================
echo   ArthurTech / skufaddon - one-click launcher
echo ==================================================
echo.

REM ---- Check if current java is already >= 17 ----
call :JMAJOR CURJ
if %CURJ% GEQ 17 goto :JAVAOK

REM ---- Try JAVA_HOME first ----
if defined JAVA_HOME if exist "%JAVA_HOME%\bin\java.exe" (
  set "PATH=%JAVA_HOME%\bin;%PATH%"
  call :JMAJOR CURJ
  if !CURJ! GEQ 17 goto :JAVAOK
)

REM ---- Detect current drive letter (e.g. E:\) ----
set "_DRV=%~d0"

REM ---- Search common JDK locations (21 first, then 17) ----
set "JAVA_HOME="
for /d %%D in ("!_DRV!\Program Files\Microsoft\jdk-21*") do if not defined JAVA_HOME set "JAVA_HOME=%%D"
for /d %%D in ("!_DRV!\Program Files\Eclipse Adoptium\jdk-21*") do if not defined JAVA_HOME set "JAVA_HOME=%%D"
for /d %%D in ("!_DRV!\Program Files\Java\jdk-21*") do if not defined JAVA_HOME set "JAVA_HOME=%%D"
for /d %%D in ("%ProgramFiles%\Microsoft\jdk-21*") do if not defined JAVA_HOME set "JAVA_HOME=%%D"
for /d %%D in ("%ProgramFiles%\Eclipse Adoptium\jdk-21*") do if not defined JAVA_HOME set "JAVA_HOME=%%D"
for /d %%D in ("%ProgramFiles%\Java\jdk-21*") do if not defined JAVA_HOME set "JAVA_HOME=%%D"
for /d %%D in ("!_DRV!\Program Files\Microsoft\jdk-17*") do if not defined JAVA_HOME set "JAVA_HOME=%%D"
for /d %%D in ("!_DRV!\Program Files\Eclipse Adoptium\jdk-17*") do if not defined JAVA_HOME set "JAVA_HOME=%%D"
for /d %%D in ("%ProgramFiles%\Microsoft\jdk-17*") do if not defined JAVA_HOME set "JAVA_HOME=%%D"
for /d %%D in ("%ProgramFiles%\Eclipse Adoptium\jdk-17*") do if not defined JAVA_HOME set "JAVA_HOME=%%D"
for /d %%D in ("%ProgramFiles%\Java\jdk-17*") do if not defined JAVA_HOME set "JAVA_HOME=%%D"

if defined JAVA_HOME if exist "!JAVA_HOME!\bin\java.exe" (
  set "PATH=!JAVA_HOME!\bin;!PATH!"
  call :JMAJOR CURJ
  if !CURJ! GEQ 17 goto :JAVAOK
)

echo [!] Java 17+ not found.
echo     Install JDK 17+: https://adoptium.net/temurin/releases/?version=17
echo     Or set JAVA_HOME to your JDK folder, then run again.
echo.
pause
exit /b 1

:JAVAOK
echo Java OK:
java -version
echo.
echo Choose action:
echo   [1] Play    (runClient)  - launch the game with the mod   ^(default^)
echo   [2] Build   (build)      - make build\libs\skufaddon-0.1.0.jar
echo   [3] Server  (runServer)  - dedicated server, no graphics
echo   [4] Datagen (runData)    - regenerate item models / lang
echo.
set "CHOICE="
set /p "CHOICE=Enter 1-4 and press Enter (default 1): "
if "%CHOICE%"=="" set "CHOICE=1"

set "TASK=runClient"
if "%CHOICE%"=="2" set "TASK=build"
if "%CHOICE%"=="3" set "TASK=runServer"
if "%CHOICE%"=="4" set "TASK=runData"

echo.
echo ^>^> gradlew %TASK%   (first run downloads Forge/MC/GTCEu, be patient)
echo.
call gradlew.bat %TASK% --no-daemon --console=plain
set "RC=%errorlevel%"
echo.
echo Done. exit code %RC%
pause
exit /b %RC%

:JMAJOR
REM Sets %1 to the Java major version number (e.g. 17 or 21), or 0 if not found.
set "%1=0"
for /f "tokens=3" %%v in ('java -version 2^>^&1 ^| findstr /i "version"') do set "_JV=%%v"
if not defined _JV exit /b 0
set "_JV=%_JV:"=%"
for /f "tokens=1,2 delims=." %%a in ("%_JV%") do (
  if "%%a"=="1" ( set "%1=%%b" ) else ( set "%1=%%a" )
)
exit /b 0
