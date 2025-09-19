# PowerShell script to install Persian models
Write-Host "Installing Persian models for Ollama..." -ForegroundColor Green
Write-Host ""

Write-Host "Installing vhdm/persian-voice-v1..." -ForegroundColor Yellow
ollama pull vhdm/persian-voice-v1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error installing persian-voice-v1" -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host ""
Write-Host "Installing vhdm/whisper-large-fa-v1..." -ForegroundColor Yellow
ollama pull vhdm/whisper-large-fa-v1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error installing whisper-large-fa-v1" -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host ""
Write-Host "All models installed successfully!" -ForegroundColor Green
Write-Host "You can now use the hybrid Persian speech-to-text service." -ForegroundColor Green
Read-Host "Press Enter to continue"
