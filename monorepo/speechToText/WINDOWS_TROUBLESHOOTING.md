# راهنمای عیب‌یابی Windows - مدل‌های فارسی

## 🚨 مشکل: خطای Encoding

### خطا:
```
❌ Error installing vhdm/persian-voice-v1: 'charmap' codec can't decode byte 0x8f in position 541: character maps to <undefined>
```

### راه‌حل‌ها:

#### 1. استفاده از اسکریپت Windows مخصوص
```bash
python setup_persian_models_windows.py
```

#### 2. نصب دستی با Batch Script
```bash
# اجرای فایل batch
install_persian_models.bat
```

#### 3. نصب دستی با PowerShell
```powershell
# اجرای فایل PowerShell
.\install_persian_models.ps1
```

#### 4. نصب مستقیم در Command Prompt
```cmd
# باز کردن Command Prompt و اجرای دستورات
ollama pull vhdm/persian-voice-v1
ollama pull vhdm/whisper-large-fa-v1
```

## 🔧 تنظیمات پیشرفته Windows

### تنظیم Console Encoding
```cmd
# در Command Prompt
chcp 65001
set PYTHONIOENCODING=utf-8
```

### تنظیم PowerShell
```powershell
# در PowerShell
$env:PYTHONIOENCODING="utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

### تنظیم Environment Variables
```cmd
# اضافه کردن به System Environment Variables
setx PYTHONIOENCODING "utf-8"
setx OLLAMA_HOST "http://127.0.0.1:11434"
```

## 🐛 مشکلات رایج و راه‌حل‌ها

### 1. Ollama Service شروع نمی‌شود
```cmd
# بررسی وضعیت Ollama
ollama --version

# شروع سرویس
ollama serve

# بررسی پورت
netstat -an | findstr 11434
```

### 2. مدل‌ها دانلود نمی‌شوند
```cmd
# بررسی اتصال اینترنت
ping ollama.ai

# بررسی فضای دیسک
dir C:\Users\%USERNAME%\.ollama

# پاک کردن cache
ollama rm vhdm/persian-voice-v1
ollama pull vhdm/persian-voice-v1
```

### 3. خطای Permission
```cmd
# اجرای Command Prompt به عنوان Administrator
# یا اجرای PowerShell به عنوان Administrator
```

### 4. خطای Firewall
```cmd
# اضافه کردن Ollama به Windows Firewall
# یا غیرفعال کردن موقت Firewall
```

## 📋 مراحل عیب‌یابی گام به گام

### مرحله 1: بررسی پیش‌نیازها
```cmd
# بررسی Python
python --version

# بررسی Ollama
ollama --version

# بررسی pip packages
pip list | findstr ollama
```

### مرحله 2: بررسی سرویس‌ها
```cmd
# بررسی Ollama service
curl http://127.0.0.1:11434/api/tags

# یا با PowerShell
Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags"
```

### مرحله 3: تست نصب مدل
```cmd
# تست مدل موجود
ollama list

# تست عملکرد مدل
ollama run vhdm/persian-voice-v1 "سلام"
```

### مرحله 4: تست سرویس Speech-to-Text
```cmd
# شروع سرویس
python app.py

# در ترمینال جدید
curl http://localhost:8001/health
```

## 🛠️ اسکریپت‌های کمکی

### اسکریپت بررسی وضعیت
```python
# check_status.py
import requests
import subprocess

def check_ollama():
    try:
        response = requests.get("http://127.0.0.1:11434/api/tags")
        if response.status_code == 200:
            print("✅ Ollama is running")
            models = response.json().get('models', [])
            print(f"📋 Installed models: {len(models)}")
            for model in models:
                print(f"   - {model['name']}")
            return True
        else:
            print("❌ Ollama is not responding")
            return False
    except:
        print("❌ Ollama is not running")
        return False

def check_speech_service():
    try:
        response = requests.get("http://localhost:8001/health")
        if response.status_code == 200:
            print("✅ Speech-to-text service is running")
            data = response.json()
            print(f"   Whisper: {data.get('whisper_available', False)}")
            print(f"   Ollama: {data.get('ollama_available', False)}")
            return True
        else:
            print("❌ Speech-to-text service is not responding")
            return False
    except:
        print("❌ Speech-to-text service is not running")
        return False

if __name__ == "__main__":
    print("🔍 Checking system status...")
    check_ollama()
    check_speech_service()
```

### اسکریپت نصب مجدد
```python
# reinstall_models.py
import requests
import json

def reinstall_model(model_name):
    print(f"🔄 Reinstalling {model_name}...")
    
    # Remove existing model
    try:
        requests.delete(f"http://127.0.0.1:11434/api/delete", 
                       json={"name": model_name})
        print(f"   Removed existing {model_name}")
    except:
        pass
    
    # Install fresh
    try:
        response = requests.post(f"http://127.0.0.1:11434/api/pull",
                               json={"name": model_name},
                               stream=True, timeout=600)
        
        if response.status_code == 200:
            print(f"✅ {model_name} reinstalled successfully")
            return True
        else:
            print(f"❌ Failed to reinstall {model_name}")
            return False
    except Exception as e:
        print(f"❌ Error reinstalling {model_name}: {e}")
        return False

if __name__ == "__main__":
    models = ["vhdm/persian-voice-v1", "vhdm/whisper-large-fa-v1"]
    for model in models:
        reinstall_model(model)
```

## 🎯 راه‌حل‌های جایگزین

### 1. استفاده از Docker
```dockerfile
# Dockerfile برای Ollama
FROM ollama/ollama:latest
RUN ollama pull vhdm/persian-voice-v1
RUN ollama pull vhdm/whisper-large-fa-v1
```

### 2. استفاده از WSL2
```bash
# نصب Ollama در WSL2
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
ollama pull vhdm/persian-voice-v1
ollama pull vhdm/whisper-large-fa-v1
```

### 3. استفاده از مدل‌های جایگزین
```python
# در app.py، تغییر مدل‌ها
PERSIAN_MODELS = {
    "persian_voice": "vhdm/persian-voice-v1",
    "whisper_fa": "vhdm/whisper-large-fa-v1",
    "fallback": "whisper-large"  # مدل جایگزین
}
```

## 📞 پشتیبانی بیشتر

### لاگ‌های مفید
```cmd
# لاگ Ollama
ollama logs

# لاگ Python
python app.py > speech_service.log 2>&1

# لاگ Windows
eventvwr.msc
```

### اطلاعات سیستم
```cmd
# اطلاعات سیستم
systeminfo

# اطلاعات شبکه
ipconfig /all

# اطلاعات Python
python -c "import sys; print(sys.version)"
```

### تماس با پشتیبانی
اگر مشکلات ادامه داشت:
1. اجرای `python setup_persian_models_windows.py`
2. ذخیره خروجی کامل
3. ارسال اطلاعات سیستم و خطاها
