@echo off
echo Installing Persian models for Ollama...
echo.

echo Installing vhdm/persian-voice-v1...
ollama pull vhdm/persian-voice-v1
if %errorlevel% neq 0 (
    echo Error installing persian-voice-v1
    pause
    exit /b 1
)

echo.
echo Installing vhdm/whisper-large-fa-v1...
ollama pull vhdm/whisper-large-fa-v1
if %errorlevel% neq 0 (
    echo Error installing whisper-large-fa-v1
    pause
    exit /b 1
)

echo.
echo All models installed successfully!
echo You can now use the hybrid Persian speech-to-text service.
pause
