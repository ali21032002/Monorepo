#!/usr/bin/env python3
"""
Test script to check if FFmpeg is properly installed
"""

import subprocess
import sys
import os

def test_ffmpeg():
    """Test if FFmpeg is available and working"""
    print("🔍 Testing FFmpeg installation...")
    
    try:
        # Test FFmpeg command
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg is working: {version_line}")
            return True
        else:
            print(f"❌ FFmpeg command failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ FFmpeg not found in PATH")
        print("   Please install FFmpeg and add it to your PATH environment variable")
        return False
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg command timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing FFmpeg: {e}")
        return False

def test_whisper_ffmpeg():
    """Test if Whisper can use FFmpeg"""
    print("\n🎤 Testing Whisper with FFmpeg...")
    
    try:
        import whisper
        print("✅ Whisper imported successfully")
        
        # Test with a simple model
        model = whisper.load_model("tiny")
        print("✅ Whisper model loaded successfully")
        
        # Test FFmpeg availability through Whisper
        import tempfile
        import numpy as np
        
        # Create a simple test audio file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            # Create a minimal WAV file (1 second of silence)
            sample_rate = 16000
            duration = 1
            samples = np.zeros(int(sample_rate * duration), dtype=np.float32)
            
            # Write WAV file
            import wave
            with wave.open(temp_file.name, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes((samples * 32767).astype(np.int16).tobytes())
            
            # Test transcription
            result = model.transcribe(temp_file.name)
            print("✅ Whisper transcription test successful")
            print(f"   Transcribed text: '{result['text']}'")
            
            # Clean up
            os.unlink(temp_file.name)
            
        return True
        
    except Exception as e:
        print(f"❌ Whisper test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing FFmpeg and Whisper Integration")
    print("=" * 50)
    
    ffmpeg_ok = test_ffmpeg()
    whisper_ok = test_whisper_ffmpeg()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   FFmpeg: {'✅' if ffmpeg_ok else '❌'}")
    print(f"   Whisper: {'✅' if whisper_ok else '❌'}")
    
    if ffmpeg_ok and whisper_ok:
        print("\n🎉 All tests passed! Your system is ready for speech-to-text.")
    else:
        print("\n⚠️  Some tests failed. Please check the installation.")
        
        if not ffmpeg_ok:
            print("\n🔧 To fix FFmpeg issues:")
            print("1. Run: .\install_ffmpeg_windows.ps1 (as Administrator)")
            print("2. Or download from: https://ffmpeg.org/download.html")
            print("3. Add FFmpeg to your PATH environment variable")
            print("4. Restart your terminal")

if __name__ == "__main__":
    main()
