#!/usr/bin/env python3
"""
Test script for the speech-to-text microservice
"""

import requests
import time
import os

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_transcription():
    """Test transcription with a sample audio file"""
    print("\n🎤 Testing transcription...")
    
    # Create a simple test audio file (silence)
    # In a real test, you would use an actual audio file
    test_audio_path = "test_audio.wav"
    
    # For this test, we'll create a minimal WAV file
    # This is just for testing the endpoint, not actual transcription
    try:
        # Create a minimal WAV file header (44 bytes)
        wav_header = b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
        with open(test_audio_path, 'wb') as f:
            f.write(wav_header)
        
        # Test the transcription endpoint
        with open(test_audio_path, 'rb') as f:
            files = {'audio_file': (test_audio_path, f, 'audio/wav')}
            data = {'language': 'fa', 'model_size': 'base'}
            
            response = requests.post(
                "http://localhost:8001/transcribe-chat",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Transcription test passed")
                print(f"   Text: {result['text']}")
                print(f"   Language: {result['language']}")
                print(f"   Confidence: {result.get('confidence', 'N/A')}")
                return True
            else:
                print(f"❌ Transcription test failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Transcription test error: {e}")
        return False
    finally:
        # Clean up test file
        if os.path.exists(test_audio_path):
            os.unlink(test_audio_path)

def test_main_backend_integration():
    """Test the main backend integration"""
    print("\n🔧 Testing main backend integration...")
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Main backend is running")
            
            # Test speech-to-text endpoint
            test_audio_path = "test_audio.wav"
            wav_header = b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
            with open(test_audio_path, 'wb') as f:
                f.write(wav_header)
            
            with open(test_audio_path, 'rb') as f:
                files = {'audio_file': (test_audio_path, f, 'audio/wav')}
                data = {'language': 'fa', 'model_size': 'base'}
                
                response = requests.post(
                    "http://localhost:8000/api/speech-to-text",
                    files=files,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ Main backend integration test passed")
                    print(f"   Text: {result['text']}")
                    return True
                else:
                    print(f"❌ Main backend integration test failed: {response.status_code}")
                    print(f"   Error: {response.text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Main backend integration test error: {e}")
        return False
    finally:
        if os.path.exists(test_audio_path):
            os.unlink(test_audio_path)

def main():
    """Run all tests"""
    print("🧪 Testing Speech-to-Text Integration")
    print("=" * 50)
    
    # Test speech-to-text service
    health_ok = test_health()
    if not health_ok:
        print("\n❌ Speech-to-Text service is not running!")
        print("   Please start it with: cd monorepo/speechToText && python app.py")
        return
    
    # Test transcription
    transcription_ok = test_transcription()
    
    # Test main backend integration
    backend_ok = test_main_backend_integration()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Health Check: {'✅' if health_ok else '❌'}")
    print(f"   Transcription: {'✅' if transcription_ok else '❌'}")
    print(f"   Backend Integration: {'✅' if backend_ok else '❌'}")
    
    if health_ok and transcription_ok and backend_ok:
        print("\n🎉 All tests passed! Speech-to-text integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the service status and configuration.")

if __name__ == "__main__":
    main()
