# Speech-to-Text Service - Offline Mode

## 🚀 راه‌اندازی سریع

### 1. نصب Dependencies
```bash
pip install -r requirements.txt
```

### 2. دانلود مدل‌های Vosk
```bash
python download_models.py
```

### 3. اجرای سرویس
```bash
python app.py
```

## 📋 ویژگی‌ها

- ✅ **بدون نیاز به اینترنت**: کاملاً offline کار می‌کنه
- ✅ **پشتیبانی از فارسی**: مدل مخصوص فارسی
- ✅ **Fallback به انگلیسی**: اگر مدل فارسی نبود
- ✅ **سریع و سبک**: مدل‌های کوچک و بهینه

## 🔧 تنظیمات

### مدل‌های پشتیبانی شده:
- `vosk-model-small-fa-0.22` - مدل فارسی (اولویت اول)
- `vosk-model-small-en-us-0.15` - مدل انگلیسی (fallback)

### زبان‌های پشتیبانی شده:
- `fa` - فارسی
- `en` - انگلیسی

## 🧪 تست

### Health Check:
```bash
curl http://localhost:8001/health
```

### Transcription:
```bash
curl -X POST "http://localhost:8001/transcribe-chat" \
  -F "audio_file=@test.wav" \
  -F "language=fa"
```

## 📁 ساختار فایل‌ها

```
speechToText/
├── app.py                 # سرویس اصلی
├── requirements.txt       # Dependencies
├── download_models.py     # دانلود مدل‌ها
├── README_OFFLINE.md      # این فایل
└── vosk-model-*/         # مدل‌های دانلود شده
```

## ⚠️ نکات مهم

1. **حجم مدل‌ها**: هر مدل حدود 100MB حجم داره
2. **اولین بار**: باید مدل‌ها رو دانلود کنید
3. **فضای دیسک**: حداقل 200MB فضای خالی نیاز دارید
4. **سرعت**: مدل‌های کوچک سریع‌ترن ولی دقت کمتری دارن

## 🆘 عیب‌یابی

### اگر مدل دانلود نشد:
```bash
# دانلود دستی مدل فارسی
wget https://alphacephei.com/vosk/models/vosk-model-small-fa-0.22.zip
unzip vosk-model-small-fa-0.22.zip
```

### اگر خطای Vosk گرفتید:
```bash
# نصب مجدد Vosk
pip uninstall vosk
pip install vosk==0.3.45
```

## 🎯 نتیجه

حالا می‌تونید بدون نیاز به اینترنت از speech-to-text استفاده کنید!
