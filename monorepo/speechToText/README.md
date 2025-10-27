# Speech-to-Text Service

سرویس تبدیل گفتار به متن با پشتیبانی از مدل‌های ترکیبی فارسی و انگلیسی و مستندات کامل Swagger.

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

سرویس روی پورت **8001** اجرا می‌شود.

## 📚 مستندات API (Swagger)

سرویس شامل مستندات کامل Swagger است:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **OpenAPI JSON**: http://localhost:8001/openapi.json

### 🎤 اندپوینت‌های اصلی

#### تبدیل گفتار
- `POST /transcribe` - تبدیل پایه گفتار به متن
- `POST /transcribe-chat` - تبدیل بهینه شده برای رابط چت
- `POST /transcribe-hybrid` - تبدیل ترکیبی با مدل‌های فارسی برای حداکثر دقت

#### مدیریت مدل‌ها
- `GET /models` - لیست مدل‌های موجود و وضعیت آنها
- `GET /test-models` - تست تمام مدل‌های موجود

#### نظارت و تشخیص
- `GET /health` - بررسی سلامت سرویس
- `GET /diagnose` - تشخیص محیط سیستم (PyTorch, CUDA)

### 🌐 ویژگی‌ها

- **مدل‌های ترکیبی**: استفاده از چندین مدل فارسی برای دقت بالاتر
- **پشتیبانی کامل از فارسی**: بهینه‌سازی شده برای زبان فارسی
- **پردازش موازی**: استفاده همزمان از مدل‌ها
- **انتخاب هوشمند**: انتخاب بهترین نتیجه بر اساس اعتماد
- **تشخیص خودکار زبان**: پشتیبانی از فارسی، انگلیسی و تشخیص خودکار
- **مستندات کامل**: تمام اندپوینت‌ها با توضیحات فارسی

### 🔧 مدل‌های پشتیبانی شده

#### مدل‌های ترکیبی (جدید):
- `vhdm/whisper-large-fa-v1` - مدل Whisper فارسی از Hugging Face
- `whisper-large` - مدل Whisper چندزبانه محلی
- `vhdm/persian-voice-v1` - مجموعه داده فارسی (نه مدل)

#### مدل‌های قدیمی (پشتیبانی شده):
- `vosk-model-small-fa-0.22` - مدل فارسی Vosk
- `vosk-model-small-en-us-0.15` - مدل انگلیسی Vosk

#### زبان‌های پشتیبانی شده:
- `fa` - فارسی (بهینه‌سازی شده)
- `en` - انگلیسی
- `auto` - تشخیص خودکار

### 📝 مثال‌های استفاده

#### تبدیل پایه
```bash
curl -X POST "http://localhost:8001/transcribe" \
  -F "audio_file=@test.wav" \
  -F "language=fa" \
  -F "model_size=large"
```

#### تبدیل ترکیبی (توصیه شده)
```bash
curl -X POST "http://localhost:8001/transcribe-hybrid" \
  -F "audio_file=@test.wav" \
  -F "language=fa" \
  -F "model_preference=auto"
```

#### تبدیل برای چت
```bash
curl -X POST "http://localhost:8001/transcribe-chat" \
  -F "audio_file=@test.wav" \
  -F "language=fa"
```

#### بررسی وضعیت مدل‌ها
```bash
curl http://localhost:8001/models
```

#### تست سلامت سرویس
```bash
curl http://localhost:8001/health
```

### 🧪 تست و عیب‌یابی

#### تست خودکار مدل‌ها
```bash
curl http://localhost:8001/test-models
```

#### تشخیص محیط سیستم
```bash
curl http://localhost:8001/diagnose
```

### ⚠️ نکات مهم

#### مدل‌های ترکیبی (جدید):
1. **حجم مدل‌ها**: مدل‌های فارسی Hugging Face حدود 1-3GB حجم دارن
2. **اولین بار**: باید transformers و مدل‌ها رو نصب کنید
3. **فضای دیسک**: حداقل 5GB فضای خالی نیاز دارید
4. **سرعت**: مدل‌های ترکیبی کندترن ولی دقت بالاتری دارن
5. **اینترنت**: برای دانلود مدل‌ها نیاز به اینترنت دارید
6. **GPU**: برای سرعت بهتر، GPU توصیه می‌شود

#### مدل‌های قدیمی (Vosk):
1. **حجم مدل‌ها**: هر مدل حدود 100MB حجم داره
2. **اولین بار**: باید مدل‌ها رو دانلود کنید
3. **فضای دیسک**: حداقل 200MB فضای خالی نیاز دارید
4. **سرعت**: مدل‌های کوچک سریع‌ترن ولی دقت کمتری دارن

### 🆘 عیب‌یابی

#### مدل‌های ترکیبی (جدید):

##### Hugging Face Models (جدید):
```bash
# راه‌اندازی مدل‌های Hugging Face
python setup_huggingface_models.py

# تست مدل‌ها
python test_persian_models.py
```

##### Ollama Models (قدیمی):
```bash
# Windows (مشکل Encoding)
python setup_persian_models_windows.py

# Linux/macOS
python setup_persian_models.py
```

#### مدل‌های قدیمی (Vosk):
```bash
# دانلود دستی مدل فارسی
wget https://alphacephei.com/vosk/models/vosk-model-small-fa-0.22.zip
unzip vosk-model-small-fa-0.22.zip

# نصب مجدد Vosk
pip uninstall vosk
pip install vosk==0.3.45
```

### 📁 ساختار فایل‌ها

```
speechToText/
├── app.py                      # سرویس اصلی (با Swagger)
├── requirements.txt            # Dependencies
├── README.md                  # این فایل (جدید)
├── README_OFFLINE.md          # راهنمای کامل
├── download_models.py          # دانلود مدل‌های Vosk
├── setup_persian_models.py    # راه‌اندازی مدل‌های فارسی
├── test_hybrid_stt.py          # تست تبدیل ترکیبی
├── INSTALL_WINDOWS.md          # راهنمای نصب Windows
├── PERSIAN_MODELS_SETUP.md     # راهنمای مدل‌های فارسی
├── WINDOWS_TROUBLESHOOTING.md  # راهنمای عیب‌یابی Windows
└── vosk-model-*/              # مدل‌های دانلود شده
```

### 🎯 نتیجه

#### مدل‌های ترکیبی:
حالا می‌تونید از دقت بالای تبدیل ترکیبی فارسی استفاده کنید!

#### مدل‌های قدیمی:
می‌تونید بدون نیاز به اینترنت از speech-to-text استفاده کنید!

### 📚 مستندات بیشتر

- `README_OFFLINE.md` - راهنمای کامل و جزئیات فنی
- `INSTALL_WINDOWS.md` - راهنمای نصب برای Windows
- `PERSIAN_MODELS_SETUP.md` - راهنمای مدل‌های فارسی
- `WINDOWS_TROUBLESHOOTING.md` - راهنمای عیب‌یابی Windows
- `test_hybrid_stt.py` - تست‌های خودکار
- `setup_huggingface_models.py` - راه‌اندازی مدل‌های Hugging Face
- `setup_persian_models.py` - راه‌اندازی مدل‌های Ollama

### 🔗 اتصال با سرویس‌های دیگر

این سرویس به طور خودکار با سرویس Backend (پورت 8000) یکپارچه می‌شود و از طریق اندپوینت‌های زیر قابل دسترسی است:

- `POST /api/speech-to-text` - در سرویس Backend
- `POST /api/chat-speech-to-text` - برای رابط چت

تمام اندپوینت‌ها از طریق مستندات Swagger قابل مشاهده و تست هستند.
