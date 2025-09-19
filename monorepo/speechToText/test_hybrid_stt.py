#!/usr/bin/env python3
"""
Test script for hybrid Persian speech-to-text functionality
Tests both individual models and hybrid combination
"""

import asyncio
import requests
import json
import os
import time
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8001"
TEST_AUDIO_FILE = "test_persian_audio.wav"  # You need to provide this file

def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check successful")
            print(f"   Whisper available: {data.get('whisper_available', False)}")
            print(f"   Ollama available: {data.get('ollama_available', False)}")
            print(f"   Persian models: {data.get('persian_models', {})}")
            print(f"   Hybrid mode: {data.get('hybrid_mode', 'unknown')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_models_endpoint():
    """Test models endpoint"""
    print("\n🔍 Testing models endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/models")
        if response.status_code == 200:
            data = response.json()
            print("✅ Models endpoint successful")
            print(f"   Available models: {list(data.get('models', {}).keys())}")
            print(f"   Hybrid mode: {data.get('hybrid_mode', 'unknown')}")
            print(f"   Recommended for Persian: {data.get('recommended_for_persian', 'unknown')}")
            
            # Print model details
            for model_key, model_info in data.get('models', {}).items():
                print(f"   {model_key}: {model_info.get('name')} ({model_info.get('status')})")
            return True
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Models endpoint error: {e}")
        return False

def test_whisper_only():
    """Test Whisper-only transcription"""
    print("\n🔍 Testing Whisper-only transcription...")
    if not os.path.exists(TEST_AUDIO_FILE):
        print(f"⚠️ Test audio file not found: {TEST_AUDIO_FILE}")
        print("   Please provide a Persian audio file for testing")
        return False
    
    try:
        with open(TEST_AUDIO_FILE, 'rb') as f:
            files = {'audio_file': f}
            data = {'language': 'fa', 'model_size': 'large'}
            
            response = requests.post(f"{BASE_URL}/transcribe", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Whisper transcription successful")
                print(f"   Text: {result.get('text', '')[:100]}...")
                print(f"   Language: {result.get('language', 'unknown')}")
                print(f"   Confidence: {result.get('confidence', 0.0)}")
                return result
            else:
                print(f"❌ Whisper transcription failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Whisper transcription error: {e}")
        return False

def test_hybrid_transcription():
    """Test hybrid transcription"""
    print("\n🔍 Testing hybrid transcription...")
    if not os.path.exists(TEST_AUDIO_FILE):
        print(f"⚠️ Test audio file not found: {TEST_AUDIO_FILE}")
        print("   Please provide a Persian audio file for testing")
        return False
    
    try:
        with open(TEST_AUDIO_FILE, 'rb') as f:
            files = {'audio_file': f}
            data = {'language': 'fa', 'model_preference': 'auto'}
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/transcribe-hybrid", files=files, data=data)
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Hybrid transcription successful")
                print(f"   Text: {result.get('text', '')[:100]}...")
                print(f"   Language: {result.get('language', 'unknown')}")
                print(f"   Confidence: {result.get('confidence', 0.0)}")
                print(f"   Model used: {result.get('model_used', 'unknown')}")
                print(f"   Processing time: {end_time - start_time:.2f} seconds")
                
                # Show hybrid results
                hybrid_results = result.get('hybrid_results', {})
                if hybrid_results:
                    print("   Hybrid analysis:")
                    if 'similarity' in hybrid_results:
                        print(f"     Similarity: {hybrid_results['similarity']:.2f}")
                    if 'models_compared' in hybrid_results:
                        print(f"     Models compared: {hybrid_results['models_compared']}")
                    if 'alternative' in hybrid_results:
                        print(f"     Alternative: {hybrid_results['alternative'][:50]}...")
                
                return result
            else:
                print(f"❌ Hybrid transcription failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Hybrid transcription error: {e}")
        return False

def compare_results(whisper_result, hybrid_result):
    """Compare Whisper and hybrid results"""
    print("\n📊 Comparing results...")
    
    if not whisper_result or not hybrid_result:
        print("⚠️ Cannot compare - missing results")
        return
    
    whisper_text = whisper_result.get('text', '')
    hybrid_text = hybrid_result.get('text', '')
    
    print(f"Whisper result: {whisper_text[:100]}...")
    print(f"Hybrid result:  {hybrid_text[:100]}...")
    
    # Calculate similarity
    from difflib import SequenceMatcher
    similarity = SequenceMatcher(None, whisper_text.lower(), hybrid_text.lower()).ratio()
    print(f"Text similarity: {similarity:.2f}")
    
    # Compare confidence
    whisper_conf = whisper_result.get('confidence', 0.0)
    hybrid_conf = hybrid_result.get('confidence', 0.0)
    print(f"Whisper confidence: {whisper_conf:.2f}")
    print(f"Hybrid confidence:  {hybrid_conf:.2f}")
    
    if hybrid_conf > whisper_conf:
        print("✅ Hybrid approach shows higher confidence")
    elif whisper_conf > hybrid_conf:
        print("⚠️ Whisper shows higher confidence")
    else:
        print("➖ Similar confidence levels")

def create_sample_audio():
    """Create a sample audio file for testing (if none exists)"""
    print("\n🎵 Creating sample audio for testing...")
    
    try:
        from pydub import AudioSegment
        from pydub.generators import Sine
        
        # Create a simple tone
        tone = Sine(440).to_audio_segment(duration=2000)  # 2 seconds
        
        # Add some silence
        silence = AudioSegment.silent(duration=500)
        
        # Combine
        audio = tone + silence + tone
        
        # Export as WAV
        audio.export(TEST_AUDIO_FILE, format="wav")
        print(f"✅ Sample audio created: {TEST_AUDIO_FILE}")
        print("   Note: This is just a test tone. For real Persian speech testing,")
        print("   please provide an actual Persian audio file.")
        return True
    except Exception as e:
        print(f"❌ Failed to create sample audio: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Hybrid Persian Speech-to-Text Tests")
    print("=" * 50)
    
    # Check if test audio exists, create if not
    if not os.path.exists(TEST_AUDIO_FILE):
        print(f"📁 Test audio file not found: {TEST_AUDIO_FILE}")
        create_sample_audio()
    
    # Run tests
    health_ok = test_health_check()
    models_ok = test_models_endpoint()
    
    if not health_ok:
        print("\n❌ Health check failed. Please ensure the service is running:")
        print("   python app.py")
        return
    
    # Test transcriptions
    whisper_result = test_whisper_only()
    hybrid_result = test_hybrid_transcription()
    
    # Compare results
    if whisper_result and hybrid_result:
        compare_results(whisper_result, hybrid_result)
    
    print("\n" + "=" * 50)
    print("🏁 Tests completed!")
    
    # Summary
    print("\n📋 Summary:")
    print(f"   Health check: {'✅' if health_ok else '❌'}")
    print(f"   Models endpoint: {'✅' if models_ok else '❌'}")
    print(f"   Whisper transcription: {'✅' if whisper_result else '❌'}")
    print(f"   Hybrid transcription: {'✅' if hybrid_result else '❌'}")
    
    if hybrid_result:
        print("\n🎯 Hybrid approach is working!")
        print("   You can now use both Persian models for improved accuracy.")
    else:
        print("\n⚠️ Hybrid approach needs setup:")
        print("   1. Install Ollama: https://ollama.ai/")
        print("   2. Pull Persian models:")
        print("      ollama pull vhdm/persian-voice-v1")
        print("      ollama pull vhdm/whisper-large-fa-v1")
        print("   3. Start Ollama service: ollama serve")

if __name__ == "__main__":
    main()
