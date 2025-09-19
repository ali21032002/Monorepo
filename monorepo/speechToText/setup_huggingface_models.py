#!/usr/bin/env python3
"""
Setup script for Hugging Face Persian speech-to-text models
Downloads and configures Persian models from Hugging Face Hub
"""

import os
import sys
import time
from pathlib import Path

# Persian models from Hugging Face
PERSIAN_MODELS = {
    "whisper_fa": "vhdm/whisper-large-fa-v1",
    # Note: vhdm/persian-voice-v1 might be a dataset, not a model
    # We'll check this during setup
}

def check_dependencies():
    """Check if required packages are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        "transformers",
        "torch",
        "torchaudio",
        "datasets",
        "accelerate"
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
        print("✅ All dependencies are installed")
        return True

def test_model_availability():
    """Test if Persian models are available on Hugging Face"""
    print("\n🔍 Testing model availability...")
    
    try:
        from transformers import pipeline, AutoProcessor, AutoModelForSpeechSeq2Seq
        import torch
        
        available_models = {}
        
        for model_key, model_name in PERSIAN_MODELS.items():
            print(f"Testing {model_name}...")
            try:
                # Try to create a pipeline to test model availability
                pipe = pipeline(
                    "automatic-speech-recognition",
                    model=model_name,
                    torch_dtype=torch.float32,
                    device=-1  # CPU only for testing
                )
                available_models[model_key] = {
                    "name": model_name,
                    "status": "available",
                    "type": "speech_recognition"
                }
                print(f"✅ {model_name} is available")
                
                # Clean up
                del pipe
                torch.cuda.empty_cache() if torch.cuda.is_available() else None
                
            except Exception as e:
                error_msg = str(e)
                if "not found" in error_msg.lower():
                    available_models[model_key] = {
                        "name": model_name,
                        "status": "not_found",
                        "error": error_msg
                    }
                    print(f"❌ {model_name} not found on Hugging Face")
                elif "not a model" in error_msg.lower() or "dataset" in error_msg.lower():
                    available_models[model_key] = {
                        "name": model_name,
                        "status": "not_a_model",
                        "error": error_msg
                    }
                    print(f"⚠️ {model_name} might be a dataset, not a model")
                else:
                    available_models[model_key] = {
                        "name": model_name,
                        "status": "error",
                        "error": error_msg
                    }
                    print(f"❌ {model_name} error: {error_msg[:100]}...")
        
        return available_models
        
    except ImportError as e:
        print(f"❌ Transformers not available: {e}")
        return {}

def download_model(model_name: str):
    """Download a model from Hugging Face"""
    print(f"📥 Downloading model: {model_name}")
    
    try:
        from transformers import pipeline
        import torch
        
        # Download and cache the model
        pipe = pipeline(
            "automatic-speech-recognition",
            model=model_name,
            torch_dtype=torch.float32,
            device=-1  # CPU for download
        )
        
        print(f"✅ Model {model_name} downloaded and cached")
        
        # Clean up
        del pipe
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to download {model_name}: {e}")
        return False

def test_speech_to_text_service():
    """Test the speech-to-text service"""
    print("\n🧪 Testing speech-to-text service...")
    
    try:
        import requests
        response = requests.get("http://localhost:8001/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Speech-to-text service is running")
            print(f"   Whisper available: {data.get('whisper_available', False)}")
            print(f"   Hugging Face available: {data.get('huggingface_available', False)}")
            print(f"   Hybrid mode: {data.get('hybrid_mode', 'unknown')}")
            
            persian_models = data.get('persian_models', {})
            for model_key, status in persian_models.items():
                print(f"   {model_key}: {status}")
            
            return True
        else:
            print(f"❌ Speech-to-text service returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Speech-to-text service is not running: {e}")
        print("   Start it with: python app.py")
        return False

def create_test_script():
    """Create a test script for Persian models"""
    test_script_content = '''#!/usr/bin/env python3
"""
Test script for Hugging Face Persian models
"""

import requests
import json

def test_persian_model(model_name):
    """Test a Persian model"""
    print(f"🧪 Testing {model_name}...")
    
    try:
        # Test with a simple Persian text
        test_data = {
            "text": "سلام، این یک تست است",
            "language": "fa"
        }
        
        response = requests.post(
            "http://localhost:8001/transcribe-hybrid",
            files={"audio_file": open("test_persian.wav", "rb")},
            data={"language": "fa", "model_preference": "auto"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {model_name} test successful")
            print(f"   Text: {result.get('text', '')[:50]}...")
            print(f"   Confidence: {result.get('confidence', 0.0)}")
            return True
        else:
            print(f"❌ {model_name} test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ {model_name} test error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Persian models...")
    test_persian_model("vhdm/whisper-large-fa-v1")
'''
    
    test_file = Path("test_persian_models.py")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_script_content)
    
    print(f"✅ Created test script: {test_file}")

def main():
    """Main setup function"""
    print("🚀 Hugging Face Persian Models Setup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first")
        return False
    
    # Test model availability
    available_models = test_model_availability()
    
    if not available_models:
        print("\n❌ No models could be tested")
        return False
    
    # Summary of model status
    print(f"\n📋 Model Status Summary:")
    available_count = 0
    for model_key, info in available_models.items():
        status = info["status"]
        print(f"   {model_key}: {status}")
        if status == "available":
            available_count += 1
    
    # Download available models
    if available_count > 0:
        print(f"\n📥 Downloading {available_count} available models...")
        for model_key, info in available_models.items():
            if info["status"] == "available":
                download_model(info["name"])
    else:
        print("\n⚠️ No models are available for download")
    
    # Create test script
    create_test_script()
    
    # Test speech-to-text service
    test_speech_to_text_service()
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed!")
    
    # Summary
    print(f"\n📋 Summary:")
    print(f"   Available models: {available_count}/{len(PERSIAN_MODELS)}")
    
    if available_count > 0:
        print("\n✅ Persian models are ready!")
        print("🎯 Next steps:")
        print("   1. Start speech-to-text service: python app.py")
        print("   2. Test Persian models: python test_persian_models.py")
        print("   3. Use /transcribe-hybrid endpoint for best Persian accuracy")
    else:
        print("\n⚠️ No Persian models are available")
        print("🔧 Alternative options:")
        print("   1. Use Whisper Large model (supports Persian)")
        print("   2. Check Hugging Face for other Persian models")
        print("   3. Train your own Persian model")
    
    return available_count > 0

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
