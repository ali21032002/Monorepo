# راه‌اندازی مدل‌های فارسی ترکیبی

## 🎯 هدف
استفاده ترکیبی از مدل‌های `vhdm/persian-voice-v1` و `vhdm/whisper-large-fa-v1` برای افزایش دقت تبدیل صدا به متن فارسی.

## 📋 پیش‌نیازها

### 1. نصب Ollama
```bash
# Windows
winget install Ollama.Ollama

# یا دانلود از سایت رسمی
# https://ollama.ai/download
```

### 2. راه‌اندازی Ollama
```bash
# شروع سرویس Ollama
ollama serve

# در ترمینال جدید
ollama pull vhdm/persian-voice-v1
ollama pull vhdm/whisper-large-fa-v1
```

### 3. نصب وابستگی‌های Python
```bash
cd monorepo/speechToText
pip install -r requirements.txt
```

## 🚀 راه‌اندازی سرویس

### 1. شروع سرویس Speech-to-Text
```bash
cd monorepo/speechToText
python app.py
```

### 2. بررسی وضعیت مدل‌ها
```bash
curl http://localhost:8001/health
```

### 3. مشاهده مدل‌های موجود
```bash
curl http://localhost:8001/models
```

## 🎤 استفاده از تبدیل ترکیبی

### 1. تبدیل ساده (فقط Whisper)
```bash
curl -X POST "http://localhost:8001/transcribe-chat" \
  -F "audio_file=@test.wav" \
  -F "language=fa"
```

### 2. تبدیل ترکیبی (Whisper + مدل‌های فارسی)
```bash
curl -X POST "http://localhost:8001/transcribe-hybrid" \
  -F "audio_file=@test.wav" \
  -F "language=fa" \
  -F "model_preference=auto"
```

## 🔧 تنظیمات پیشرفته

### متغیرهای محیطی
```bash
# تنظیم هاست Ollama
export OLLAMA_HOST="http://127.0.0.1:11434"

# تنظیم مدل پیش‌فرض
export OLLAMA_MODEL="vhdm/persian-voice-v1"
```

### انتخاب مدل خاص
- `auto`: انتخاب خودکار بهترین مدل
- `persian_voice`: استفاده از vhdm/persian-voice-v1
- `whisper_fa`: استفاده از vhdm/whisper-large-fa-v1

## 📊 نحوه کارکرد ترکیبی

### 1. پردازش موازی
- هر دو مدل به صورت همزمان روی فایل صوتی کار می‌کنند
- نتایج با هم مقایسه می‌شوند

### 2. امتیازدهی هوشمند
- هر مدل یک امتیاز اعتماد (confidence) تولید می‌کند
- مدل با امتیاز بالاتر انتخاب می‌شود

### 3. ترکیب نتایج
- اگر نتایج مشابه باشند (>80% شباهت): از مدل با اعتماد بالاتر استفاده می‌شود
- اگر متفاوت باشند: از مدل با اعتماد بالاتر استفاده می‌شود
- نتیجه جایگزین نیز در پاسخ ارائه می‌شود

## 🧪 تست عملکرد

### 1. تست سلامت سرویس
```bash
curl http://localhost:8001/health
```

### 2. تست مدل‌ها
```bash
curl http://localhost:8001/models
```

### 3. تست تبدیل ترکیبی
```bash
# با فایل نمونه
curl -X POST "http://localhost:8001/transcribe-hybrid" \
  -F "audio_file=@sample_persian.wav" \
  -F "language=fa"
```

## 📈 مزایای استفاده ترکیبی

### ✅ افزایش دقت
- استفاده از نقاط قوت هر مدل
- کاهش خطاهای احتمالی

### ✅ پشتیبانی بهتر از فارسی
- مدل‌های تخصصی فارسی
- درک بهتر لهجه‌ها و تلفظ‌ها

### ✅ قابلیت اطمینان
- اگر یک مدل خطا کند، مدل دیگر جایگزین می‌شود
- مقایسه نتایج برای اطمینان از صحت

## ⚠️ نکات مهم

### 1. منابع سیستم
- هر دو مدل به صورت همزمان اجرا می‌شوند
- نیاز به RAM و CPU بیشتر

### 2. زمان پردازش
- تبدیل ترکیبی کمی بیشتر طول می‌کشد
- اما دقت بالاتری ارائه می‌دهد

### 3. وابستگی به Ollama
- اگر Ollama در دسترس نباشد، فقط از Whisper استفاده می‌شود
- سرویس همچنان کار می‌کند

## 🆘 عیب‌یابی

### مشکل: مدل‌های فارسی در دسترس نیستند
```bash
# بررسی وضعیت Ollama
ollama list

# دانلود مجدد مدل‌ها
ollama pull vhdm/persian-voice-v1
ollama pull vhdm/whisper-large-fa-v1
```

### مشکل: خطای اتصال به Ollama
```bash
# بررسی سرویس Ollama
ollama serve

# بررسی پورت
netstat -an | findstr 11434
```

### مشکل: خطای تبدیل صوتی
```bash
# نصب FFmpeg
# Windows: winget install FFmpeg
# یا استفاده از اسکریپت موجود
./install_ffmpeg_windows.ps1
```

## 📝 مثال پاسخ ترکیبی

```json
{
  "text": "سلام، این یک تست تبدیل صدا به متن فارسی است",
  "language": "fa",
  "confidence": 0.95,
  "model_used": "vhdm/persian-voice-v1",
  "hybrid_results": {
    "similarity": 0.92,
    "alternative": "سلام، این یک تست تبدیل صدا به متن فارسی است",
    "models_compared": 3,
    "error": null
  }
}
```

## 🎯 نتیجه

با استفاده از این راه‌حل ترکیبی، می‌توانید:
- دقت تبدیل صدا به متن فارسی را افزایش دهید
- از نقاط قوت هر مدل استفاده کنید
- قابلیت اطمینان سیستم را بهبود دهید
- نتایج بهتری برای کاربران فارسی‌زبان ارائه دهید
