#!/usr/bin/env python3
"""
Windows-specific setup script for Persian speech-to-text models
Handles encoding issues and provides alternative installation methods
"""

import requests
import json
import time
import os
import sys
from pathlib import Path

# Persian models to install
PERSIAN_MODELS = [
    "vhdm/persian-voice-v1",
    "vhdm/whisper-large-fa-v1"
]

OLLAMA_HOST = "http://127.0.0.1:11434"

def check_ollama_service():
    """Check if Ollama service is running"""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama service is running")
            return True
        else:
            print(f"❌ Ollama service returned status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ollama service is not running: {e}")
        return False

def get_installed_models():
    """Get list of installed models"""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            return models
        else:
            print(f"❌ Failed to get models list: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting models list: {e}")
        return []

def install_model_via_api(model_name):
    """Install model using Ollama API (Windows-friendly)"""
    print(f"📥 Installing model via API: {model_name}")
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/pull",
            json={"name": model_name},
            stream=True,
            timeout=600  # 10 minutes timeout for large models
        )
        
        if response.status_code == 200:
            print(f"✅ Model {model_name} installation started via API")
            
            # Monitor progress
            last_status = ""
            for line in response.iter_lines():
                if line:
                    try:
                        # Decode with error handling
                        line_str = line.decode('utf-8', errors='replace')
                        data = json.loads(line_str)
                        
                        if 'status' in data:
                            status = data['status']
                            
                            # Only print if status changed
                            if status != last_status:
                                print(f"   {status}")
                                last_status = status
                            
                            # Show progress if available
                            if 'completed' in data and 'total' in data:
                                completed = data['completed']
                                total = data['total']
                                if total > 0:
                                    percentage = (completed / total) * 100
                                    print(f"   Progress: {completed}/{total} ({percentage:.1f}%)")
                        
                        # Check for completion
                        if data.get('status') == 'success':
                            print(f"✅ Model {model_name} installed successfully!")
                            return True
                            
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        # Skip problematic lines
                        print(f"   Skipping line: {str(e)[:50]}...")
                        continue
            
            print(f"✅ Model {model_name} installation completed")
            return True
        else:
            print(f"❌ API installation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API installation error: {e}")
        return False

def test_model(model_name):
    """Test if a model works"""
    print(f"🧪 Testing model: {model_name}")
    try:
        # Try to generate a simple response
        test_prompt = "سلام"
        
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model_name,
                "prompt": test_prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'response' in data:
                print(f"✅ Model {model_name} is working")
                print(f"   Test response: {data['response'][:50]}...")
                return True
            else:
                print(f"❌ Model {model_name} returned invalid response")
                return False
        else:
            print(f"❌ Model {model_name} test failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing {model_name}: {e}")
        return False

def create_batch_install_script():
    """Create a Windows batch script for manual installation"""
    batch_content = """@echo off
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
"""
    
    batch_file = Path("install_persian_models.bat")
    with open(batch_file, 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    print(f"✅ Created batch script: {batch_file}")
    return batch_file

def create_powershell_install_script():
    """Create a PowerShell script for manual installation"""
    ps_content = """# PowerShell script to install Persian models
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
"""
    
    ps_file = Path("install_persian_models.ps1")
    with open(ps_file, 'w', encoding='utf-8') as f:
        f.write(ps_content)
    
    print(f"✅ Created PowerShell script: {ps_file}")
    return ps_file

def main():
    """Main setup function for Windows"""
    print("🚀 Persian Speech-to-Text Models Setup (Windows)")
    print("=" * 60)
    
    # Check Ollama service
    if not check_ollama_service():
        print("\n❌ Please start Ollama service first:")
        print("   1. Open Command Prompt as Administrator")
        print("   2. Run: ollama serve")
        print("   3. Keep the service running in a separate window")
        return False
    
    # Get installed models
    installed_models = get_installed_models()
    print(f"\n📋 Currently installed models: {len(installed_models)}")
    for model in installed_models:
        print(f"   - {model}")
    
    # Check which Persian models need installation
    models_to_install = []
    for model in PERSIAN_MODELS:
        if model not in installed_models:
            models_to_install.append(model)
        else:
            print(f"✅ {model} is already installed")
    
    if not models_to_install:
        print("\n✅ All Persian models are already installed!")
        # Test existing models
        print(f"\n🧪 Testing existing Persian models...")
        for model in PERSIAN_MODELS:
            test_model(model)
        return True
    
    print(f"\n📥 Installing {len(models_to_install)} Persian models...")
    
    # Try API installation for each model
    success_count = 0
    for model in models_to_install:
        print(f"\n{'='*50}")
        if install_model_via_api(model):
            success_count += 1
            # Test the model
            test_model(model)
        else:
            print(f"❌ Failed to install {model}")
    
    # Create manual installation scripts as backup
    print(f"\n📝 Creating manual installation scripts...")
    create_batch_install_script()
    create_powershell_install_script()
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed!")
    
    # Summary
    print(f"\n📋 Summary:")
    print(f"   Models installed: {success_count}/{len(models_to_install)}")
    
    if success_count == len(models_to_install):
        print("\n✅ All Persian models installed successfully!")
        print("🎯 Next steps:")
        print("   1. Start speech-to-text service: python app.py")
        print("   2. Test hybrid transcription: python test_hybrid_stt.py")
        print("   3. Use /transcribe-hybrid endpoint for best Persian accuracy")
    else:
        print(f"\n⚠️ {len(models_to_install) - success_count} models failed to install")
        print("🔧 Manual installation options:")
        print("   1. Run: install_persian_models.bat")
        print("   2. Run: install_persian_models.ps1")
        print("   3. Or manually:")
        for model in models_to_install:
            print(f"      ollama pull {model}")
    
    return success_count == len(models_to_install)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
