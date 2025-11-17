# راهنمای Export مستندات

این راهنما روش‌های مختلف برای دریافت مستندات به صورت فایل را توضیح می‌دهد.

## روش 1: HTML Static Files (پیشنهادی)

مستندات به صورت HTML static در پوشه `site/` ساخته می‌شود:

```powershell
python -m mkdocs build
```

فایل‌های HTML در پوشه `site/` قرار دارند. می‌توانید:
- کل پوشه `site/` را کپی کنید
- فایل `site/index.html` را در مرورگر باز کنید
- پوشه `site/` را در یک وب سرور قرار دهید

## روش 2: تبدیل HTML به PDF با مرورگر

1. فایل `site/index.html` را در مرورگر باز کنید
2. کلید `Ctrl+P` را بزنید (یا File > Print)
3. در قسمت Destination، "Save as PDF" را انتخاب کنید
4. تنظیمات را تنظیم کنید (مثلاً Background graphics را فعال کنید)
5. روی "Save" کلیک کنید

## روش 3: استفاده از اسکریپت build_docs.py

```powershell
python build_docs.py
```

این اسکریپت مستندات را می‌سازد و مسیر فایل‌ها را نمایش می‌دهد.

## روش 4: Archive کردن پوشه site

می‌توانید کل پوشه `site/` را به صورت ZIP یا TAR.GZ فشرده کنید:

```powershell
# PowerShell
Compress-Archive -Path site\* -DestinationPath documentation.zip

# یا با 7-Zip
7z a documentation.zip site\
```

## نکات مهم

- فایل‌های HTML در پوشه `site/` کاملاً standalone هستند
- می‌توانید کل پوشه را به هر جایی منتقل کنید
- برای مشاهده، فقط کافی است `index.html` را در مرورگر باز کنید
- برای PDF، استفاده از Print to PDF مرورگر بهترین کیفیت را دارد

