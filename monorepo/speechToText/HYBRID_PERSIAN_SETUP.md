# راه‌اندازی تبدیل ترکیبی صدا به متن فارسی

این راهنما نحوه راه‌اندازی سیستم ترکیبی تبدیل صدا به متن فارسی را با استفاده از مدل‌های `vhdm/persian-voice-v1` و `vhdm/whisper-large-fa-v1` توضیح می‌دهد.

## 🎯 مزایای استفاده ترکیبی

- **دقت بالاتر**: ترکیب نتایج دو مدل برای دقت بهتر
- **مقایسه هوشمند**: انتخاب بهترین نتیجه بر اساس امتیاز اعتماد
- **پشتیبانی کامل از فارسی**: هر دو مدل مخصوص زبان فارسی بهینه‌سازی شده‌اند
- **پردازش موازی**: استفاده همزمان از مدل‌ها برای سرعت بیشتر

## 📋 پیش‌نیازها

### 1. نصب Ollama
```bash
# Windows
winget install Ollama.Ollama

# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. راه‌اندازی Ollama
```bash
# شروع سرویس Ollama
ollama serve

# در ترمینال جدید، مدل‌های فارسی را دانلود کنید
ollama pull vhdm/persian-voice-v1
ollama pull vhdm/whisper-large-fa-v1
```

### 3. نصب وابستگی‌های Python
```bash
cd monorepo/speechToText
pip install -r requirements.txt
```

## 🚀 راه‌اندازی سرویس

### 1. شروع سرویس تبدیل صدا به متن
```bash
cd monorepo/speechToText
python app.py
```

سرویس روی پورت `8001` شروع می‌شود.

### 2. بررسی وضعیت سرویس
```bash
curl http://localhost:8001/health
```

پاسخ باید شامل اطلاعات زیر باشد:
```json
{
  "status": "ok",
  "whisper_available": true,
  "ollama_available": true,
  "persian_models": {
    "persian_voice": "available",
    "whisper_fa": "available"
  },
  "hybrid_mode": "available"
}
```

## 🧪 تست عملکرد

### 1. اجرای تست‌های خودکار
```bash
python test_hybrid_stt.py
```

### 2. تست دستی با curl
```bash
# تست تبدیل ترکیبی
curl -X POST "http://localhost:8001/transcribe-hybrid" \
  -F "audio_file=@test_persian.wav" \
  -F "language=fa" \
  -F "model_preference=auto"
```

### 3. تست مدل‌های موجود
```bash
curl http://localhost:8001/models
```

## 📡 API Endpoints

### 1. `/transcribe-hybrid` (جدید)
تبدیل ترکیبی با استفاده از هر دو مدل فارسی:

```bash
POST /transcribe-hybrid
Content-Type: multipart/form-data

Parameters:
- audio_file: فایل صوتی (webm, wav, mp3)
- language: زبان (fa برای فارسی)
- model_preference: ترجیح مدل (auto, persian_voice, whisper_fa)
```

**پاسخ:**
```json
{
  "text": "متن تبدیل شده",
  "language": "fa",
  "confidence": 0.95,
  "model_used": "persian_voice",
  "hybrid_results": {
    "similarity": 0.87,
    "models_compared": 3,
    "alternative": "متن جایگزین"
  }
}
```

### 2. `/health`
بررسی وضعیت سرویس و مدل‌ها

### 3. `/models`
لیست مدل‌های موجود و وضعیت آن‌ها

## 🔧 تنظیمات پیشرفته

### متغیرهای محیطی
```bash
# تنظیم هاست Ollama
export OLLAMA_HOST="http://127.0.0.1:11434"

# تنظیم مدل پیش‌فرض
export OLLAMA_MODEL="vhdm/persian-voice-v1"
```

### تنظیمات مدل
```python
# در فایل app.py
PERSIAN_MODELS = {
    "persian_voice": "vhdm/persian-voice-v1",
    "whisper_fa": "vhdm/whisper-large-fa-v1"
}
```

## 📊 مقایسه عملکرد

### مدل‌های پشتیبانی شده:

| مدل | نوع | زبان | دقت | سرعت |
|-----|-----|------|------|------|
| Whisper Large | محلی | چندزبانه | بالا | متوسط |
| Persian Voice v1 | Ollama | فارسی | بالا | سریع |
| Whisper FA v1 | Ollama | فارسی | بالا | سریع |
| **ترکیبی** | **هر دو** | **فارسی** | **بسیار بالا** | **متوسط** |

### الگوریتم ترکیب:

1. **پردازش موازی**: هر دو مدل همزمان روی فایل صوتی کار می‌کنند
2. **محاسبه شباهت**: مقایسه نتایج با الگوریتم SequenceMatcher
3. **انتخاب هوشمند**:
   - اگر شباهت > 80%: انتخاب مدل با اعتماد بالاتر
   - اگر شباهت < 80%: انتخاب مدل با اعتماد بالاتر
   - ارائه نتیجه جایگزین برای مقایسه

## 🐛 عیب‌یابی

### مشکل: Ollama در دسترس نیست
```bash
# بررسی وضعیت Ollama
ollama list

# راه‌اندازی مجدد
ollama serve
```

### مشکل: مدل‌های فارسی دانلود نشده
```bash
# دانلود مجدد مدل‌ها
ollama pull vhdm/persian-voice-v1
ollama pull vhdm/whisper-large-fa-v1
```

### مشکل: خطای FFmpeg
```bash
# Windows
winget install FFmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

### مشکل: خطای pydub
```bash
pip install pydub
```

## 📈 بهینه‌سازی عملکرد

### 1. تنظیم timeout
```python
# در تابع hybrid_transcribe
result = future.result(timeout=30)  # 30 ثانیه timeout
```

### 2. تنظیم تعداد worker ها
```python
# در ThreadPoolExecutor
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
```

### 3. تنظیم کیفیت صدا
```python
# در تبدیل صدا
audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
```

## 🎯 استفاده در پروژه

### در Frontend (React):
```javascript
const transcribeHybrid = async (audioFile) => {
  const formData = new FormData();
  formData.append('audio_file', audioFile);
  formData.append('language', 'fa');
  formData.append('model_preference', 'auto');
  
  const response = await fetch('/api/transcribe-hybrid', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
};
```

### در Backend (Python):
```python
import requests

def transcribe_hybrid(audio_file_path):
    with open(audio_file_path, 'rb') as f:
        files = {'audio_file': f}
        data = {'language': 'fa', 'model_preference': 'auto'}
        
        response = requests.post(
            'http://localhost:8001/transcribe-hybrid',
            files=files,
            data=data
        )
        
        return response.json()
```

## 🔮 توسعه‌های آینده

- [ ] پشتیبانی از مدل‌های فارسی بیشتر
- [ ] تنظیمات پیشرفته برای ترکیب نتایج
- [ ] ذخیره‌سازی cache برای بهبود سرعت
- [ ] پشتیبانی از فرمت‌های صوتی بیشتر
- [ ] رابط کاربری برای مقایسه مدل‌ها

## 📞 پشتیبانی

برای سوالات و مشکلات:
1. بررسی فایل `test_hybrid_stt.py` برای تست
2. بررسی لاگ‌های سرویس در کنسول
3. استفاده از endpoint `/health` برای تشخیص مشکل
