#!/usr/bin/env python3
"""
Script to download Vosk models for offline speech recognition
"""

import os
import urllib.request
import zipfile
import shutil

def download_file(url, filename):
    """Download a file from URL"""
    print(f"Downloading {filename}...")
    urllib.request.urlretrieve(url, filename)
    print(f"Downloaded {filename}")

def extract_zip(zip_path, extract_to):
    """Extract zip file"""
    print(f"Extracting {zip_path}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"Extracted to {extract_to}")

def download_vosk_models():
    """Download Vosk models"""
    
    # Persian model (small)
    persian_model_url = "https://alphacephei.com/vosk/models/vosk-model-small-fa-0.22.zip"
    persian_model_zip = "vosk-model-small-fa-0.22.zip"
    persian_model_dir = "vosk-model-small-fa-0.22"
    
    # English model (small) - fallback
    english_model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    english_model_zip = "vosk-model-small-en-us-0.15.zip"
    english_model_dir = "vosk-model-small-en-us-0.15"
    
    # Download Persian model
    if not os.path.exists(persian_model_dir):
        try:
            download_file(persian_model_url, persian_model_zip)
            extract_zip(persian_model_zip, ".")
            os.remove(persian_model_zip)
            print("✅ Persian model downloaded successfully!")
        except Exception as e:
            print(f"❌ Failed to download Persian model: {e}")
    else:
        print("✅ Persian model already exists!")
    
    # Download English model (fallback)
    if not os.path.exists(english_model_dir):
        try:
            download_file(english_model_url, english_model_zip)
            extract_zip(english_model_zip, ".")
            os.remove(english_model_zip)
            print("✅ English model downloaded successfully!")
        except Exception as e:
            print(f"❌ Failed to download English model: {e}")
    else:
        print("✅ English model already exists!")

if __name__ == "__main__":
    print("🚀 Downloading Vosk models for offline speech recognition...")
    download_vosk_models()
    print("🎉 Model download complete!")
    print("\n📝 Note: Models are large (100MB+ each) and will be downloaded to the current directory.")
    print("🔧 You can now run the speech-to-text service offline!")
