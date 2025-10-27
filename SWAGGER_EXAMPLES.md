# Swagger API Examples

مجموعه مثال‌های کاربردی برای استفاده از API های سرویس‌های LangExtract با مستندات Swagger.

## 📚 دسترسی به مستندات

### Backend Service (Port 8000)
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Speech-to-Text Service (Port 8001)
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## 🔧 Backend Service Examples

### 1. استخراج موجودیت‌ها از متن

#### درخواست:
```bash
curl -X POST "http://localhost:8000/api/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "علی احمدی در تهران زندگی می‌کند و در شرکت فناوری پارس کار می‌کند. او متولد سال 1985 است.",
    "language": "fa",
    "schema_name": "general",
    "model": "gemma3:4b",
    "temperature": 0.1,
    "max_output_tokens": 512
  }'
```

#### پاسخ نمونه:
```json
{
  "text": "علی احمدی در تهران زندگی می‌کند و در شرکت فناوری پارس کار می‌کند. او متولد سال 1985 است.",
  "language": "fa",
  "model": "gemma3:4b",
  "entities": [
    {
      "text": "علی احمدی",
      "label": "PERSON",
      "start": 0,
      "end": 9,
      "confidence": 0.95
    },
    {
      "text": "تهران",
      "label": "LOCATION",
      "start": 13,
      "end": 18,
      "confidence": 0.98
    },
    {
      "text": "شرکت فناوری پارس",
      "label": "ORGANIZATION",
      "start": 25,
      "end": 42,
      "confidence": 0.92
    },
    {
      "text": "1985",
      "label": "DATE",
      "start": 55,
      "end": 59,
      "confidence": 0.89
    }
  ],
  "relationships": [
    {
      "head": "علی احمدی",
      "tail": "تهران",
      "relation": "LIVES_IN",
      "confidence": 0.94
    },
    {
      "head": "علی احمدی",
      "tail": "شرکت فناوری پارس",
      "relation": "WORKS_FOR",
      "confidence": 0.91
    }
  ]
}
```

### 2. تحلیل چندمدله

#### درخواست:
```bash
curl -X POST "http://localhost:8000/api/multi_extract" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "دکتر محمد رضایی در بیمارستان امام خمینی تهران مشغول به کار است.",
    "language": "fa",
    "domain": "medical",
    "model_first": "gemma3:4b",
    "model_second": "qwen2.5:7b",
    "model_referee": "llama3:8b",
    "temperature": 0.1,
    "max_output_tokens": 512
  }'
```

#### پاسخ نمونه:
```json
{
  "text": "دکتر محمد رضایی در بیمارستان امام خمینی تهران مشغول به کار است.",
  "language": "fa",
  "domain": "medical",
  "first_analysis": {
    "entities": [
      {
        "text": "دکتر محمد رضایی",
        "label": "PERSON",
        "start": 0,
        "end": 15,
        "confidence": 0.96
      },
      {
        "text": "بیمارستان امام خمینی",
        "label": "ORGANIZATION",
        "start": 19,
        "end": 37,
        "confidence": 0.94
      }
    ],
    "relationships": [
      {
        "head": "دکتر محمد رضایی",
        "tail": "بیمارستان امام خمینی",
        "relation": "WORKS_AT",
        "confidence": 0.92
      }
    ]
  },
  "second_analysis": {
    "entities": [
      {
        "text": "محمد رضایی",
        "label": "PERSON",
        "start": 4,
        "end": 15,
        "confidence": 0.98
      },
      {
        "text": "بیمارستان امام خمینی تهران",
        "label": "ORGANIZATION",
        "start": 19,
        "end": 44,
        "confidence": 0.95
      }
    ],
    "relationships": [
      {
        "head": "محمد رضایی",
        "tail": "بیمارستان امام خمینی تهران",
        "relation": "EMPLOYED_BY",
        "confidence": 0.89
      }
    ]
  },
  "final_analysis": {
    "entities": [
      {
        "text": "دکتر محمد رضایی",
        "label": "PERSON",
        "start": 0,
        "end": 15,
        "confidence": 0.97
      },
      {
        "text": "بیمارستان امام خمینی",
        "label": "ORGANIZATION",
        "start": 19,
        "end": 37,
        "confidence": 0.95
      }
    ],
    "relationships": [
      {
        "head": "دکتر محمد رضایی",
        "tail": "بیمارستان امام خمینی",
        "relation": "WORKS_AT",
        "confidence": 0.91
      }
    ]
  },
  "agreement_score": 0.87,
  "conflicting_entities": [],
  "conflicting_relationships": []
}
```

### 3. چت تعاملی

#### درخواست:
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "سلام، من علی هستم و در تهران زندگی می‌کنم. می‌تونید در مورد آب و هوای تهران چیزی بگید؟",
    "language": "fa",
    "domain": "general",
    "model": "gemma3:4b",
    "analysisMode": "single",
    "message_history": []
  }'
```

#### پاسخ نمونه:
```json
{
  "message": "سلام علی! خوشحالم که با شما آشنا شدم. تهران شهر زیبایی است و آب و هوای آن معمولاً معتدل است. در فصل بهار و پاییز هوا بسیار دلپذیر است، اما در تابستان‌ها ممکن است گرم باشد و در زمستان‌ها سرد. آیا سوال خاصی در مورد آب و هوا دارید؟",
  "analysis": null,
  "analysisMode": "single",
  "chart": null
}
```

### 4. استخراج از فایل

#### درخواست:
```bash
curl -X POST "http://localhost:8000/api/extract_file" \
  -F "file=@document.pdf" \
  -F "language=fa" \
  -F "schema=general" \
  -F "model=gemma3:4b"
```

### 5. دریافت لیست مدل‌ها

#### درخواست:
```bash
curl -X GET "http://localhost:8000/api/models"
```

#### پاسخ نمونه:
```json
{
  "status": "success",
  "models": [
    "gemma3:4b",
    "qwen2.5:7b",
    "llama3:8b",
    "gemma2:9b"
  ],
  "count": 4
}
```

## 🎤 Speech-to-Text Service Examples

### 1. تبدیل پایه گفتار به متن

#### درخواست:
```bash
curl -X POST "http://localhost:8001/transcribe" \
  -F "audio_file=@speech.wav" \
  -F "language=fa" \
  -F "model_size=large"
```

#### پاسخ نمونه:
```json
{
  "text": "سلام، من علی هستم و در تهران زندگی می‌کنم",
  "language": "fa",
  "confidence": 0.92,
  "model_used": "whisper-large",
  "hybrid_results": null
}
```

### 2. تبدیل ترکیبی (توصیه شده)

#### درخواست:
```bash
curl -X POST "http://localhost:8001/transcribe-hybrid" \
  -F "audio_file=@speech.wav" \
  -F "language=fa" \
  -F "model_preference=auto"
```

#### پاسخ نمونه:
```json
{
  "text": "سلام، من علی هستم و در تهران زندگی می‌کنم",
  "language": "fa",
  "confidence": 0.95,
  "model_used": "whisper-large-fa-v1",
  "hybrid_results": {
    "similarity": 0.89,
    "alternative": "سلام، من علی هستم و در تهران زندگی می‌کنم",
    "models_compared": 3,
    "error": null
  }
}
```

### 3. تبدیل برای چت

#### درخواست:
```bash
curl -X POST "http://localhost:8001/transcribe-chat" \
  -F "audio_file=@speech.wav" \
  -F "language=fa"
```

### 4. بررسی وضعیت مدل‌ها

#### درخواست:
```bash
curl -X GET "http://localhost:8001/models"
```

#### پاسخ نمونه:
```json
{
  "models": {
    "whisper": {
      "name": "whisper-large",
      "type": "local",
      "language": "multilingual",
      "status": "available"
    },
    "whisper_fa": {
      "name": "vhdm/whisper-large-fa-v1",
      "type": "huggingface",
      "language": "persian",
      "status": "available"
    }
  },
  "hybrid_mode": "available",
  "recommended_for_persian": "hybrid",
  "available_models_count": 2,
  "note": "Using 2 models for hybrid transcription"
}
```

### 5. بررسی سلامت سرویس

#### درخواست:
```bash
curl -X GET "http://localhost:8001/health"
```

#### پاسخ نمونه:
```json
{
  "status": "ok",
  "service": "speech-to-text",
  "whisper_available": true,
  "huggingface_available": true,
  "hf_status": "available",
  "persian_models": {
    "whisper_fa": "available",
    "whisper_large": "available"
  },
  "model": "large",
  "supported_languages": ["en", "fa", "auto"],
  "supported_formats": ["webm", "wav", "mp3"],
  "hybrid_mode": "available",
  "note": "Hybrid Persian speech recognition with Whisper + Hugging Face models"
}
```

## 🌐 Frontend Integration Examples

### JavaScript/TypeScript

#### استخراج متن:
```javascript
const response = await fetch('http://localhost:8000/api/extract', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    text: 'علی در تهران زندگی می‌کند',
    language: 'fa',
    schema_name: 'general'
  })
});

const result = await response.json();
console.log(result.entities);
```

#### تبدیل گفتار:
```javascript
const formData = new FormData();
formData.append('audio_file', audioFile);
formData.append('language', 'fa');
formData.append('use_hybrid', 'true');

const response = await fetch('http://localhost:8000/api/speech-to-text', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(result.text);
```

#### چت با سابقه:
```javascript
const chatResponse = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'سلام، چطور می‌تونم کمکتون کنم؟',
    language: 'fa',
    domain: 'general',
    message_history: previousMessages
  })
});

const chatResult = await chatResponse.json();
console.log(chatResult.message);
```

## 🔧 Python Examples

### استفاده با requests

```python
import requests

# استخراج متن
response = requests.post('http://localhost:8000/api/extract', json={
    'text': 'علی در تهران زندگی می‌کند',
    'language': 'fa',
    'schema_name': 'general'
})

result = response.json()
print(f"موجودیت‌ها: {result['entities']}")

# تبدیل گفتار
with open('speech.wav', 'rb') as f:
    files = {'audio_file': f}
    data = {'language': 'fa', 'use_hybrid': True}
    
    response = requests.post('http://localhost:8000/api/speech-to-text', 
                            files=files, data=data)
    
    result = response.json()
    print(f"متن: {result['text']}")
```

### استفاده با httpx (async)

```python
import httpx
import asyncio

async def extract_text():
    async with httpx.AsyncClient() as client:
        response = await client.post('http://localhost:8000/api/extract', json={
            'text': 'محمد دانشجوی دانشگاه تهران است',
            'language': 'fa',
            'schema_name': 'general'
        })
        
        result = response.json()
        return result['entities']

# اجرا
entities = asyncio.run(extract_text())
print(entities)
```

## 📊 Error Handling Examples

### مدیریت خطاها

```javascript
try {
  const response = await fetch('http://localhost:8000/api/extract', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: 'متن نمونه',
      language: 'fa'
    })
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const result = await response.json();
  console.log('موفق:', result);
  
} catch (error) {
  console.error('خطا:', error.message);
}
```

### بررسی وضعیت سرویس

```javascript
async function checkServiceHealth() {
  try {
    const response = await fetch('http://localhost:8000/api/health');
    const health = await response.json();
    
    if (health.status === 'ok') {
      console.log('سرویس فعال است');
      return true;
    } else {
      console.log('سرویس غیرفعال است');
      return false;
    }
  } catch (error) {
    console.error('خطا در اتصال به سرویس:', error);
    return false;
  }
}
```

## 🎯 Best Practices

### 1. استفاده از مدل‌های مناسب
- برای متن فارسی: `gemma3:4b` یا `qwen2.5:7b`
- برای تحلیل چندمدله: استفاده از مدل‌های مختلف
- برای گفتار فارسی: استفاده از `transcribe-hybrid`

### 2. مدیریت سابقه چت
```javascript
const messageHistory = [
  { role: 'user', content: 'سلام' },
  { role: 'assistant', content: 'سلام! چطور می‌تونم کمکتون کنم؟' }
];

const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'در مورد هوش مصنوعی چیزی می‌دونید؟',
    language: 'fa',
    message_history: messageHistory
  })
});
```

### 3. تنظیم پارامترها
```javascript
const config = {
  temperature: 0.1,        // برای دقت بالاتر
  max_output_tokens: 512,   // برای پاسخ‌های کوتاه‌تر
  model: 'gemma3:4b'        // مدل مناسب
};
```

### 4. استفاده از Swagger UI
1. به آدرس http://localhost:8000/docs بروید
2. اندپوینت مورد نظر را انتخاب کنید
3. روی "Try it out" کلیک کنید
4. پارامترها را وارد کنید
5. روی "Execute" کلیک کنید

## 📚 منابع بیشتر

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Swagger UI Documentation](https://swagger.io/tools/swagger-ui/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Persian NLP Best Practices](https://github.com/persiannlp/persiannlp)

---

**نکته**: تمام مثال‌ها با فرض اجرای سرویس‌ها روی پورت‌های پیش‌فرض نوشته شده‌اند. در صورت تغییر پورت‌ها، آدرس‌ها را به‌روزرسانی کنید.
