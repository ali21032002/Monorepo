# Speech-to-Text Service - Hybrid Persian Mode

## 🚀 راه‌اندازی سریع

### 1. نصب Dependencies
```bash
pip install -r requirements.txt
```

### 2. راه‌اندازی مدل‌های فارسی ترکیبی
```bash
# برای Hugging Face models (جدید)
python setup_huggingface_models.py

# برای Ollama models (قدیمی)
python setup_persian_models.py
```

### 3. اجرای سرویس
```bash
python app.py
```

## 📋 ویژگی‌های جدید

- ✅ **تبدیل ترکیبی**: استفاده از چندین مدل فارسی برای دقت بالاتر
- ✅ **مدل‌های فارسی پیشرفته**: `vhdm/persian-voice-v1` و `vhdm/whisper-large-fa-v1`
- ✅ **پردازش موازی**: استفاده همزمان از مدل‌ها
- ✅ **انتخاب هوشمند**: انتخاب بهترین نتیجه بر اساس اعتماد
- ✅ **پشتیبانی کامل از فارسی**: بهینه‌سازی شده برای زبان فارسی

## 🔧 مدل‌های پشتیبانی شده

### مدل‌های ترکیبی (جدید):
- `vhdm/whisper-large-fa-v1` - مدل Whisper فارسی از Hugging Face
- `whisper-large` - مدل Whisper چندزبانه محلی
- `vhdm/persian-voice-v1` - مجموعه داده فارسی (نه مدل)

### مدل‌های قدیمی (پشتیبانی شده):
- `vosk-model-small-fa-0.22` - مدل فارسی Vosk
- `vosk-model-small-en-us-0.15` - مدل انگلیسی Vosk

### زبان‌های پشتیبانی شده:
- `fa` - فارسی (بهینه‌سازی شده)
- `en` - انگلیسی
- `auto` - تشخیص خودکار

## 🧪 تست

### Health Check:
```bash
curl http://localhost:8001/health
```

### تست تبدیل ترکیبی (جدید):
```bash
curl -X POST "http://localhost:8001/transcribe-hybrid" \
  -F "audio_file=@test.wav" \
  -F "language=fa" \
  -F "model_preference=auto"
```

### تست مدل‌های موجود:
```bash
curl http://localhost:8001/models
```

### تست خودکار:
```bash
python test_hybrid_stt.py
```

### Transcription قدیمی:
```bash
curl -X POST "http://localhost:8001/transcribe-chat" \
  -F "audio_file=@test.wav" \
  -F "language=fa"
```

## 📁 ساختار فایل‌ها

```
speechToText/
├── app.py                      # سرویس اصلی (به‌روزرسانی شده)
├── requirements.txt            # Dependencies (شامل Ollama)
├── download_models.py          # دانلود مدل‌های Vosk
├── setup_persian_models.py     # راه‌اندازی مدل‌های فارسی (جدید)
├── test_hybrid_stt.py          # تست تبدیل ترکیبی (جدید)
├── HYBRID_PERSIAN_SETUP.md     # راهنمای کامل (جدید)
├── README_OFFLINE.md           # این فایل
└── vosk-model-*/              # مدل‌های دانلود شده
```

## ⚠️ نکات مهم

### مدل‌های ترکیبی (جدید):
1. **حجم مدل‌ها**: مدل‌های فارسی Hugging Face حدود 1-3GB حجم دارن
2. **اولین بار**: باید transformers و مدل‌ها رو نصب کنید
3. **فضای دیسک**: حداقل 5GB فضای خالی نیاز دارید
4. **سرعت**: مدل‌های ترکیبی کندترن ولی دقت بالاتری دارن
5. **اینترنت**: برای دانلود مدل‌ها نیاز به اینترنت دارید
6. **GPU**: برای سرعت بهتر، GPU توصیه می‌شود

### مدل‌های قدیمی (Vosk):
1. **حجم مدل‌ها**: هر مدل حدود 100MB حجم داره
2. **اولین بار**: باید مدل‌ها رو دانلود کنید
3. **فضای دیسک**: حداقل 200MB فضای خالی نیاز دارید
4. **سرعت**: مدل‌های کوچک سریع‌ترن ولی دقت کمتری دارن

## 🆘 عیب‌یابی

### مدل‌های ترکیبی (جدید):

#### Hugging Face Models (جدید):
```bash
# راه‌اندازی مدل‌های Hugging Face
python setup_huggingface_models.py

# تست مدل‌ها
python test_persian_models.py
```

#### Ollama Models (قدیمی):
```bash
# Windows (مشکل Encoding)
python setup_persian_models_windows.py

# Linux/macOS
python setup_persian_models.py
```

### مدل‌های قدیمی (Vosk):
```bash
# دانلود دستی مدل فارسی
wget https://alphacephei.com/vosk/models/vosk-model-small-fa-0.22.zip
unzip vosk-model-small-fa-0.22.zip

# نصب مجدد Vosk
pip uninstall vosk
pip install vosk==0.3.45
```

## 🎯 نتیجه

### مدل‌های ترکیبی:
حالا می‌تونید از دقت بالای تبدیل ترکیبی فارسی استفاده کنید!

### مدل‌های قدیمی:
می‌تونید بدون نیاز به اینترنت از speech-to-text استفاده کنید!

## 📚 مستندات بیشتر

- `HYBRID_PERSIAN_SETUP.md` - راهنمای کامل مدل‌های ترکیبی
- `WINDOWS_TROUBLESHOOTING.md` - راهنمای عیب‌یابی Windows
- `test_hybrid_stt.py` - تست‌های خودکار
- `setup_huggingface_models.py` - راه‌اندازی مدل‌های Hugging Face (جدید)
- `setup_persian_models.py` - راه‌اندازی مدل‌های Ollama (قدیمی)
- `setup_persian_models_windows.py` - راه‌اندازی Ollama برای Windows
