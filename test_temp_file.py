#!/usr/bin/env python3
"""
Test script to check temporary file creation and access
"""

import tempfile
import os
import time

def test_temp_file_creation():
    """Test temporary file creation and access"""
    print("🧪 Testing temporary file creation...")
    
    try:
        # Test 1: Create temp file with mkstemp
        print("\n1. Testing mkstemp method:")
        temp_fd, temp_path = tempfile.mkstemp(suffix=".wav")
        print(f"   Created: {temp_path}")
        print(f"   File exists: {os.path.exists(temp_path)}")
        
        # Write some test data
        with os.fdopen(temp_fd, 'wb') as f:
            f.write(b"test audio data")
        
        print(f"   After write - File exists: {os.path.exists(temp_path)}")
        print(f"   File size: {os.path.getsize(temp_path)}")
        
        # Test reading
        with open(temp_path, 'rb') as f:
            data = f.read()
            print(f"   Read data: {data}")
        
        # Clean up
        os.unlink(temp_path)
        print(f"   After cleanup - File exists: {os.path.exists(temp_path)}")
        
        # Test 2: Create temp file with NamedTemporaryFile
        print("\n2. Testing NamedTemporaryFile method:")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test audio data 2")
            print(f"   Created: {temp_path}")
            print(f"   File exists: {os.path.exists(temp_path)}")
        
        print(f"   After context - File exists: {os.path.exists(temp_path)}")
        print(f"   File size: {os.path.getsize(temp_path)}")
        
        # Clean up
        os.unlink(temp_path)
        print(f"   After cleanup - File exists: {os.path.exists(temp_path)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing temp files: {e}")
        return False

def test_whisper_with_temp_file():
    """Test Whisper with temporary file"""
    print("\n🎤 Testing Whisper with temporary file...")
    
    try:
        import whisper
        import numpy as np
        
        # Load tiny model for testing
        model = whisper.load_model("tiny")
        print("✅ Whisper model loaded")
        
        # Create a test audio file
        temp_fd, temp_path = tempfile.mkstemp(suffix=".wav")
        
        try:
            # Create a simple WAV file
            sample_rate = 16000
            duration = 1
            samples = np.zeros(int(sample_rate * duration), dtype=np.float32)
            
            # Write WAV file
            import wave
            with wave.open(temp_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes((samples * 32767).astype(np.int16).tobytes())
            
            print(f"✅ Test audio file created: {temp_path}")
            print(f"   File exists: {os.path.exists(temp_path)}")
            print(f"   File size: {os.path.getsize(temp_path)}")
            
            # Test transcription
            result = model.transcribe(temp_path)
            print(f"✅ Transcription successful: '{result['text']}'")
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                print(f"✅ Temp file cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Whisper test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Temporary File Handling")
    print("=" * 50)
    
    temp_ok = test_temp_file_creation()
    whisper_ok = test_whisper_with_temp_file()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Temp File Creation: {'✅' if temp_ok else '❌'}")
    print(f"   Whisper with Temp File: {'✅' if whisper_ok else '❌'}")
    
    if temp_ok and whisper_ok:
        print("\n🎉 All tests passed! Temporary file handling is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
