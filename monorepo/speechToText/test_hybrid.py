#!/usr/bin/env python3
"""
تست عملکرد تبدیل ترکیبی صدا به متن فارسی
"""

import requests
import json
import time
import os
from pathlib import Path

# تنظیمات
BASE_URL = "http://localhost:8001"
TEST_AUDIO_FILE = "test_persian.wav"  # فایل صوتی تست

def test_health():
    """تست سلامت سرویس"""
    print("🔍 تست سلامت سرویس...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ سرویس فعال")
            print(f"   Whisper: {data.get('whisper_available', False)}")
            print(f"   Ollama: {data.get('ollama_available', False)}")
            print(f"   حالت ترکیبی: {data.get('hybrid_mode', 'نامشخص')}")
            
            # بررسی مدل‌های فارسی
            persian_models = data.get('persian_models', {})
            for model_name, status in persian_models.items():
                print(f"   {model_name}: {status}")
            
            return True
        else:
            print(f"❌ خطا در سلامت سرویس: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ خطا در اتصال: {e}")
        return False

def test_models():
    """تست مدل‌های موجود"""
    print("\n🔍 تست مدل‌های موجود...")
    try:
        response = requests.get(f"{BASE_URL}/models")
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', {})
            
            print("📋 مدل‌های موجود:")
            for model_key, model_info in models.items():
                status_icon = "✅" if model_info.get('status') == 'available' else "❌"
                print(f"   {status_icon} {model_key}: {model_info.get('name', 'نامشخص')} ({model_info.get('status', 'نامشخص')})")
            
            print(f"\n🎯 حالت ترکیبی: {data.get('hybrid_mode', 'نامشخص')}")
            print(f"💡 توصیه برای فارسی: {data.get('recommended_for_persian', 'نامشخص')}")
            
            return True
        else:
            print(f"❌ خطا در دریافت مدل‌ها: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ خطا در اتصال: {e}")
        return False

def create_test_audio():
    """ایجاد فایل صوتی تست"""
    print("\n🎵 ایجاد فایل صوتی تست...")
    
    # بررسی وجود فایل تست
    if os.path.exists(TEST_AUDIO_FILE):
        print(f"✅ فایل تست موجود: {TEST_AUDIO_FILE}")
        return True
    
    try:
        # ایجاد فایل صوتی ساده با pydub
        from pydub import AudioSegment
        from pydub.generators import Sine
        
        # ایجاد یک تون ساده
        tone = Sine(440).to_audio_segment(duration=2000)  # 2 ثانیه
        tone = tone.set_frame_rate(16000).set_channels(1)
        
        # ذخیره فایل
        tone.export(TEST_AUDIO_FILE, format="wav")
        print(f"✅ فایل تست ایجاد شد: {TEST_AUDIO_FILE}")
        return True
        
    except ImportError:
        print("❌ pydub نصب نشده - نصب کنید: pip install pydub")
        return False
    except Exception as e:
        print(f"❌ خطا در ایجاد فایل تست: {e}")
        return False

def test_simple_transcription():
    """تست تبدیل ساده"""
    print("\n🎤 تست تبدیل ساده (Whisper)...")
    
    if not os.path.exists(TEST_AUDIO_FILE):
        print("❌ فایل تست موجود نیست")
        return False
    
    try:
        with open(TEST_AUDIO_FILE, 'rb') as f:
            files = {'audio_file': f}
            data = {'language': 'fa'}
            
            response = requests.post(f"{BASE_URL}/transcribe-chat", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ تبدیل موفق")
                print(f"   متن: {result.get('text', 'خالی')}")
                print(f"   زبان: {result.get('language', 'نامشخص')}")
                print(f"   اعتماد: {result.get('confidence', 0):.2f}")
                return True
            else:
                print(f"❌ خطا در تبدیل: {response.status_code}")
                print(f"   پاسخ: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ خطا در تست تبدیل: {e}")
        return False

def test_hybrid_transcription():
    """تست تبدیل ترکیبی"""
    print("\n🎯 تست تبدیل ترکیبی...")
    
    if not os.path.exists(TEST_AUDIO_FILE):
        print("❌ فایل تست موجود نیست")
        return False
    
    try:
        with open(TEST_AUDIO_FILE, 'rb') as f:
            files = {'audio_file': f}
            data = {
                'language': 'fa',
                'model_preference': 'auto'
            }
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/transcribe-hybrid", files=files, data=data)
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ تبدیل ترکیبی موفق")
                print(f"   زمان پردازش: {end_time - start_time:.2f} ثانیه")
                print(f"   متن: {result.get('text', 'خالی')}")
                print(f"   زبان: {result.get('language', 'نامشخص')}")
                print(f"   اعتماد: {result.get('confidence', 0):.2f}")
                print(f"   مدل استفاده شده: {result.get('model_used', 'نامشخص')}")
                
                # نمایش نتایج ترکیبی
                hybrid_results = result.get('hybrid_results', {})
                if hybrid_results:
                    print(f"   شباهت نتایج: {hybrid_results.get('similarity', 0):.2f}")
                    print(f"   مدل‌های مقایسه شده: {hybrid_results.get('models_compared', 0)}")
                    if hybrid_results.get('alternative'):
                        print(f"   نتیجه جایگزین: {hybrid_results.get('alternative', 'ندارد')}")
                
                return True
            else:
                print(f"❌ خطا در تبدیل ترکیبی: {response.status_code}")
                print(f"   پاسخ: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ خطا در تست تبدیل ترکیبی: {e}")
        return False

def cleanup():
    """پاکسازی فایل‌های تست"""
    print("\n🧹 پاکسازی...")
    try:
        if os.path.exists(TEST_AUDIO_FILE):
            os.remove(TEST_AUDIO_FILE)
            print(f"✅ فایل تست حذف شد: {TEST_AUDIO_FILE}")
    except Exception as e:
        print(f"❌ خطا در پاکسازی: {e}")

def main():
    """تابع اصلی تست"""
    print("🚀 شروع تست تبدیل ترکیبی صدا به متن فارسی")
    print("=" * 50)
    
    # تست‌های اولیه
    if not test_health():
        print("❌ سرویس در دسترس نیست. لطفاً ابتدا سرویس را راه‌اندازی کنید.")
        return
    
    test_models()
    
    # ایجاد فایل تست
    if not create_test_audio():
        print("❌ نمی‌توان فایل تست ایجاد کرد")
        return
    
    # تست تبدیل‌ها
    test_simple_transcription()
    test_hybrid_transcription()
    
    # پاکسازی
    cleanup()
    
    print("\n✅ تست کامل شد!")
    print("\n💡 نکات:")
    print("   - برای تست واقعی، فایل صوتی فارسی با کیفیت بالا استفاده کنید")
    print("   - مدل‌های فارسی باید در Ollama نصب باشند")
    print("   - برای بهترین نتایج، از فایل‌های صوتی واضح استفاده کنید")

if __name__ == "__main__":
    main()
