#!/usr/bin/env python3
"""
Test script for WebM to WAV conversion functionality
"""

import os
import tempfile
from pydub import AudioSegment

def test_webm_to_wav_conversion():
    """Test WebM to WAV conversion using pydub"""
    print("Testing WebM to WAV conversion...")
    
    try:
        # Create a simple test audio file (1 second of silence)
        print("Creating test audio...")
        test_audio = AudioSegment.silent(duration=1000)  # 1 second of silence
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_webm:
            webm_path = temp_webm.name
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
            wav_path = temp_wav.name
        
        try:
            # Export as WebM
            print(f"Exporting to WebM: {webm_path}")
            test_audio.export(webm_path, format="webm")
            
            # Check if WebM file was created
            if os.path.exists(webm_path):
                webm_size = os.path.getsize(webm_path)
                print(f"✓ WebM file created successfully (size: {webm_size} bytes)")
            else:
                print("✗ WebM file creation failed")
                return False
            
            # Convert WebM to WAV
            print(f"Converting WebM to WAV: {wav_path}")
            audio = AudioSegment.from_file(webm_path, format="webm")
            
            # Convert to WAV format with optimal settings for Whisper
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            audio.export(wav_path, format="wav")
            
            # Check if WAV file was created
            if os.path.exists(wav_path):
                wav_size = os.path.getsize(wav_path)
                print(f"✓ WAV file created successfully (size: {wav_size} bytes)")
                print("✓ WebM to WAV conversion test passed!")
                return True
            else:
                print("✗ WAV file creation failed")
                return False
                
        finally:
            # Clean up temporary files
            for file_path in [webm_path, wav_path]:
                if os.path.exists(file_path):
                    try:
                        os.unlink(file_path)
                        print(f"Cleaned up: {file_path}")
                    except Exception as e:
                        print(f"Warning: Could not clean up {file_path}: {e}")
    
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False

def test_whisper_model_loading():
    """Test if Whisper large model can be loaded"""
    print("\nTesting Whisper model loading...")
    
    try:
        import whisper
        print("Loading Whisper large model...")
        model = whisper.load_model("large")
        print("✓ Whisper large model loaded successfully!")
        return True
    except Exception as e:
        print(f"✗ Whisper model loading failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Speech-to-Text Service Test ===")
    print()
    
    # Test WebM to WAV conversion
    conversion_success = test_webm_to_wav_conversion()
    
    # Test Whisper model loading
    model_success = test_whisper_model_loading()
    
    print("\n=== Test Results ===")
    print(f"WebM to WAV conversion: {'✓ PASS' if conversion_success else '✗ FAIL'}")
    print(f"Whisper model loading: {'✓ PASS' if model_success else '✗ FAIL'}")
    
    if conversion_success and model_success:
        print("\n🎉 All tests passed! The service is ready to use.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
