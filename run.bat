@echo off
cls
echo ========================================
echo     WHATSAPP EXTRACTOR V3
echo ========================================
echo.
echo 1. Processus COMPLET
echo 2. Extraction seulement
echo 3. Transcription seulement  
echo 4. Export seulement
echo.

set /p choice=Votre choix (1-4): 

if "%choice%"=="1" python main.py --full
if "%choice%"=="2" python main.py --extract-only
if "%choice%"=="3" python main.py --transcribe-only
if "%choice%"=="4" python main.py --export-only

pause
