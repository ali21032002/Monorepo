# PowerShell script to install FFmpeg on Windows
# Run this script as Administrator

Write-Host "🎬 Installing FFmpeg for Windows..." -ForegroundColor Green

# Check if Chocolatey is installed
if (Get-Command choco -ErrorAction SilentlyContinue) {
    Write-Host "✅ Chocolatey found, installing FFmpeg..." -ForegroundColor Green
    choco install ffmpeg -y
    Write-Host "✅ FFmpeg installed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Chocolatey not found. Installing Chocolatey first..." -ForegroundColor Yellow
    
    # Install Chocolatey
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    # Install FFmpeg
    choco install ffmpeg -y
    Write-Host "✅ FFmpeg installed successfully!" -ForegroundColor Green
}

# Verify installation
Write-Host "🔍 Verifying FFmpeg installation..." -ForegroundColor Blue
try {
    $ffmpegVersion = ffmpeg -version 2>&1 | Select-String "ffmpeg version"
    if ($ffmpegVersion) {
        Write-Host "✅ FFmpeg is working: $($ffmpegVersion.Line)" -ForegroundColor Green
    } else {
        Write-Host "⚠️  FFmpeg installed but may need PATH refresh. Please restart your terminal." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  FFmpeg may need to be added to PATH manually." -ForegroundColor Yellow
    Write-Host "   Please restart your terminal and try again." -ForegroundColor Yellow
}

Write-Host "🎉 Installation complete! Please restart your terminal and try running the speech-to-text service again." -ForegroundColor Green
