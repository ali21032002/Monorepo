#!/usr/bin/env python3
"""
Setup script for Persian speech-to-text models
Automatically downloads and configures Persian models for hybrid transcription
"""

import subprocess
import sys
import time
import requests
import json
from pathlib import Path

# Persian models to install
PERSIAN_MODELS = [
    "vhdm/persian-voice-v1",
    "vhdm/whisper-large-fa-v1"
]

OLLAMA_HOST = "http://127.0.0.1:11434"

def check_ollama_installed():
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(["ollama", "--version"], 
                             capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Ollama is installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Ollama is not properly installed")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Ollama is not installed or not in PATH")
        return False

def check_ollama_running():
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

def start_ollama_service():
    """Try to start Ollama service"""
    print("🚀 Attempting to start Ollama service...")
    try:
        # Try to start Ollama in background
        subprocess.Popen(["ollama", "serve"], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        
        # Wait for service to start
        for i in range(10):
            time.sleep(2)
            if check_ollama_running():
                print("✅ Ollama service started successfully")
                return True
            print(f"⏳ Waiting for Ollama service... ({i+1}/10)")
        
        print("❌ Failed to start Ollama service")
        return False
    except Exception as e:
        print(f"❌ Error starting Ollama service: {e}")
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

def install_model_api(model_name):
    """Install model using Ollama API (Windows-friendly)"""
    print(f"📥 Installing model via API: {model_name}")
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/pull",
            json={"name": model_name},
            stream=True,
            timeout=300  # 5 minutes timeout
        )
        
        if response.status_code == 200:
            print(f"✅ Model {model_name} installation started via API")
            
            # Monitor progress
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if 'status' in data:
                            status = data['status']
                            if 'completed' in data:
                                completed = data['completed']
                                total = data.get('total', 1)
                                percentage = (completed / total) * 100 if total > 0 else 0
                                print(f"   {status}: {completed}/{total} ({percentage:.1f}%)")
                            else:
                                print(f"   {status}")
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # Skip lines that can't be decoded
                        continue
            
            print(f"✅ Model {model_name} installed successfully via API")
            return True
        else:
            print(f"❌ API installation failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API installation error: {e}")
        return False

def install_model(model_name):
    """Install a specific model with fallback methods"""
    print(f"📥 Installing model: {model_name}")
    
    # Try API method first (Windows-friendly)
    if install_model_api(model_name):
        return True
    
    # Fallback to subprocess method
    print(f"🔄 Trying subprocess method for {model_name}...")
    try:
        # Start the pull process with proper encoding for Windows
        process = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace'  # Replace problematic characters instead of failing
        )
        
        # Monitor progress
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                # Clean output for display
                clean_output = output.strip().encode('ascii', 'replace').decode('ascii')
                print(f"   {clean_output}")
        
        # Check result
        return_code = process.poll()
        if return_code == 0:
            print(f"✅ Model {model_name} installed successfully")
            return True
        else:
            stderr = process.stderr.read()
            # Clean stderr for display
            clean_stderr = stderr.encode('ascii', 'replace').decode('ascii')
            print(f"❌ Failed to install {model_name}: {clean_stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error installing {model_name}: {e}")
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

def check_python_dependencies():
    """Check if required Python packages are installed"""
    print("🔍 Checking Python dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "ollama",
        "whisper",
        "torch",
        "pydub"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    else:
        print("✅ All Python dependencies are installed")
        return True

def test_speech_to_text_service():
    """Test the speech-to-text service"""
    print("🧪 Testing speech-to-text service...")
    
    try:
        response = requests.get("http://localhost:8001/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Speech-to-text service is running")
            print(f"   Whisper available: {data.get('whisper_available', False)}")
            print(f"   Ollama available: {data.get('ollama_available', False)}")
            print(f"   Hybrid mode: {data.get('hybrid_mode', 'unknown')}")
            
            persian_models = data.get('persian_models', {})
            for model_key, status in persian_models.items():
                print(f"   {model_key}: {status}")
            
            return True
        else:
            print(f"❌ Speech-to-text service returned: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Speech-to-text service is not running: {e}")
        print("   Start it with: python app.py")
        return False

def main():
    """Main setup function"""
    print("🚀 Persian Speech-to-Text Models Setup")
    print("=" * 50)
    
    # Check Python dependencies
    if not check_python_dependencies():
        print("\n❌ Please install missing Python dependencies first")
        return False
    
    # Check Ollama installation
    if not check_ollama_installed():
        print("\n❌ Please install Ollama first:")
        print("   Windows: winget install Ollama.Ollama")
        print("   macOS: brew install ollama")
        print("   Linux: curl -fsSL https://ollama.ai/install.sh | sh")
        return False
    
    # Check Ollama service
    if not check_ollama_running():
        if not start_ollama_service():
            print("\n❌ Please start Ollama service manually:")
            print("   ollama serve")
            return False
    
    # Get installed models
    installed_models = get_installed_models()
    print(f"\n📋 Currently installed models: {len(installed_models)}")
    for model in installed_models:
        print(f"   - {model}")
    
    # Install missing Persian models
    models_to_install = []
    for model in PERSIAN_MODELS:
        if model not in installed_models:
            models_to_install.append(model)
        else:
            print(f"✅ {model} is already installed")
    
    if models_to_install:
        print(f"\n📥 Installing {len(models_to_install)} Persian models...")
        for model in models_to_install:
            if not install_model(model):
                print(f"❌ Failed to install {model}")
                return False
    else:
        print("\n✅ All Persian models are already installed")
    
    # Test installed models
    print(f"\n🧪 Testing Persian models...")
    for model in PERSIAN_MODELS:
        if not test_model(model):
            print(f"⚠️ Model {model} may not be working properly")
    
    # Test speech-to-text service
    print(f"\n🧪 Testing speech-to-text service...")
    if not test_speech_to_text_service():
        print("\n⚠️ Speech-to-text service is not running")
        print("   Start it with: python app.py")
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed!")
    
    # Summary
    print("\n📋 Summary:")
    print(f"   Ollama installed: ✅")
    print(f"   Ollama service: ✅")
    print(f"   Persian models: {len([m for m in PERSIAN_MODELS if m in get_installed_models()])}/{len(PERSIAN_MODELS)}")
    
    print("\n🎯 Next steps:")
    print("   1. Start speech-to-text service: python app.py")
    print("   2. Test hybrid transcription: python test_hybrid_stt.py")
    print("   3. Use /transcribe-hybrid endpoint for best Persian accuracy")
    
    return True

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