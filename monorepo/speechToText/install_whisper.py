#!/usr/bin/env python3
"""
Installation script for Whisper and dependencies
Handles common installation issues on Windows
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def main():
    print("🚀 Installing Whisper and dependencies...")
    print("=" * 50)
    
    # Upgrade pip first
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"):
        print("⚠️  Pip upgrade failed, continuing anyway...")
    
    # Install setuptools and wheel
    if not run_command(f"{sys.executable} -m pip install --upgrade setuptools wheel", "Installing build tools"):
        print("⚠️  Build tools installation failed, continuing anyway...")
    
    # Install PyTorch first (CPU version for compatibility)
    if not run_command(f"{sys.executable} -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu", "Installing PyTorch (CPU version)"):
        print("⚠️  PyTorch installation failed, trying alternative...")
        if not run_command(f"{sys.executable} -m pip install torch torchaudio", "Installing PyTorch (alternative)"):
            print("❌ PyTorch installation failed completely")
            return False
    
    # Install other dependencies
    dependencies = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0", 
        "python-multipart==0.0.6",
        "pydantic==2.5.0",
        "numpy",
        "ffmpeg-python"
    ]
    
    for dep in dependencies:
        if not run_command(f"{sys.executable} -m pip install {dep}", f"Installing {dep}"):
            print(f"⚠️  Failed to install {dep}, continuing...")
    
    # Install Whisper last
    print("\n🎤 Installing Whisper...")
    whisper_commands = [
        f"{sys.executable} -m pip install openai-whisper",
        f"{sys.executable} -m pip install git+https://github.com/openai/whisper.git",
        f"{sys.executable} -m pip install --no-deps openai-whisper"
    ]
    
    whisper_installed = False
    for cmd in whisper_commands:
        if run_command(cmd, "Installing Whisper"):
            whisper_installed = True
            break
    
    if not whisper_installed:
        print("❌ All Whisper installation methods failed")
        print("\n🔧 Manual installation steps:")
        print("1. Install FFmpeg: https://ffmpeg.org/download.html")
        print("2. Add FFmpeg to your PATH")
        print("3. Try: pip install openai-whisper")
        return False
    
    # Test installation
    print("\n🧪 Testing installation...")
    try:
        import whisper
        import torch
        print("✅ Whisper and PyTorch imported successfully")
        
        # Test model loading
        print("🔍 Testing model loading...")
        model = whisper.load_model("tiny")  # Use tiny model for testing
        print("✅ Model loading test successful")
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False
    
    print("\n🎉 Installation completed successfully!")
    print("You can now run: python app.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
