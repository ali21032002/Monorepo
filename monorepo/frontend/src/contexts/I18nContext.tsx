import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'

type Locale = 'fa' | 'en' | 'ar'

type Translations = Record<string, Record<Locale, string>>

const translations: Translations = {
  // App
  'app.title': { fa: 'دستیار هوش مصنوعی Mentora', en: 'Mentora AI Assistant', ar: 'مساعد الذكاء الاصطناعي Mentora' },
  'app.subtitle': { fa: 'سیستم هوشمند تحلیل متن با قابلیت داوری توسط چند مدل مختلف', en: 'Intelligent text analysis with multi-model adjudication', ar: 'تحليل نص ذكي مع تحكيم متعدد النماذج' },

  // Settings
  'settings.title': { fa: '⚙️ تنظیمات سیستم', en: '⚙️ System Settings', ar: '⚙️ إعدادات النظام' },
  'settings.confirm': { fa: '✓ تایید', en: '✓ Confirm', ar: '✓ تأكيد' },

  // Tabs
  'tab.chat': { fa: '💬 چت', en: '💬 Chat', ar: '💬 الدردشة' },
  'tab.analysis': { fa: '📊 تحلیل', en: '📊 Analysis', ar: '📊 التحليل' },
  'tab.general': { fa: '⚙️ عمومی', en: '⚙️ General', ar: '⚙️ عام' },
  'tabs.analysis': { fa: 'تحلیل متن', en: 'Text Analysis', ar: 'تحليل النص' },
  'tabs.chat': { fa: 'دستیار هوشمند', en: 'Smart Assistant', ar: 'المساعد الذكي' },

  // Theme
  'theme.toLight': { fa: 'تغییر به تم روشن', en: 'Switch to Light', ar: 'التبديل إلى الفاتح' },
  'theme.toDark': { fa: 'تغییر به تم تاریک', en: 'Switch to Dark', ar: 'التبديل إلى الداكن' },

  // General
  'general.language': { fa: '🌐 زبان', en: '🌐 Language', ar: '🌐 اللغة' },
  'general.language.fa': { fa: 'فارسی', en: 'Persian', ar: 'الفارسية' },
  'general.language.en': { fa: 'انگلیسی', en: 'English', ar: 'الإنجليزية' },
  'general.language.ar': { fa: 'عربی', en: 'Arabic', ar: 'العربية' },
  'general.domain': { fa: '🎯 حوزه تخصصی', en: '🎯 Domain', ar: '🎯 المجال' },
  'general.domain.general': { fa: 'عمومی', en: 'General', ar: 'عام' },
  'general.domain.legal': { fa: 'حقوقی', en: 'Legal', ar: 'قانوني' },
  'general.domain.medical': { fa: 'پزشکی', en: 'Medical', ar: 'طبي' },
  'general.domain.police': { fa: 'پلیسی', en: 'Police', ar: 'شرطي' },

  // Chat
  'chat.mode.title': { fa: '🎯 حالت چت', en: '🎯 Chat mode', ar: '🎯 وضع الدردشة' },
  'chat.mode.single': { fa: 'تک مدل', en: 'Single model', ar: 'نموذج واحد' },
  'chat.mode.multi': { fa: 'چند مدل', en: 'Multi model', ar: 'عدة نماذج' },
  'chat.model.title': { fa: '🤖 مدل چت', en: '🤖 Chat model', ar: '🤖 نموذج الدردشة' },
  'chat.model.select': { fa: 'انتخاب مدل...', en: 'Select model...', ar: 'اختر نموذج...' },
  'chat.model.second': { fa: '🤖 مدل دوم چت', en: '🤖 Second chat model', ar: '🤖 نموذج الدردشة الثاني' },
  'chat.model.second.select': { fa: 'انتخاب مدل دوم...', en: 'Select second model...', ar: 'اختر النموذج الثاني...' },
  'chat.model.judge': { fa: '⚖️ مدل داور چت', en: '⚖️ Chat judge model', ar: '⚖️ نموذج حكم الدردشة' },
  'chat.model.judge.select': { fa: 'انتخاب مدل داور...', en: 'Select judge model...', ar: 'اختر نموذج الحكم...' },
  'chat.welcome.1': { fa: '👋 سلام! من Mentora هستم دستیار هوش مصنوعی.', en: '👋 Hello! I am Mentora, the AI assistant.', ar: '👋 مرحبا! أنا Mentora، مساعد الذكاء الاصطناعي.' },
  'chat.welcome.2': { fa: 'می‌توانم در تحلیل متون تخصصی به شما کمک کنم و نمودارهای مختلف بکشم.', en: 'I can help analyze specialized texts and draw various charts.', ar: 'أستطيع المساعدة في تحليل النصوص المتخصصة ورسم مخططات مختلفة.' },
  'chat.welcome.3': { fa: '💡 مثال: "یک نمودار میله‌ای از روند بهبود بیماری بیمار بکش" یا "نمودار دایره‌ای از توزیع جمعیت نشان بده"', en: '💡 Example: "Draw a bar chart of patient recovery progress" or "Show a pie chart of population distribution"', ar: '💡 مثال: "ارسم مخططًا شريطيًا لتقدم شفاء المريض" أو "اعرض مخططًا دائريًا لتوزيع السكان"' },
  'chat.processing': { fa: 'در حال پردازش...', en: 'Processing...', ar: 'جارٍ المعالجة...' },
  'chat.placeholder': { fa: 'پیام خود را بنویسید... (Shift+Enter برای خط جدید)', en: 'Type your message... (Shift+Enter for new line)', ar: 'اكتب رسالتك... (Shift+Enter لسطر جديد)' },
  'chat.send': { fa: 'ارسال پیام', en: 'Send message', ar: 'إرسال رسالة' },
  'chat.copy': { fa: 'کپی پیام', en: 'Copy message', ar: 'نسخ الرسالة' },
  'chat.resend': { fa: 'ارسال مجدد', en: 'Resend', ar: 'إعادة الإرسال' },
  'chat.record.start': { fa: '🎙 ضبط صدا', en: '🎙 Start recording', ar: '🎙 بدء التسجيل' },
  'chat.record.stop': { fa: '⏹ توقف ضبط', en: '⏹ Stop recording', ar: '⏹ إيقاف التسجيل' },
  'chat.audio.upload': { fa: '🎵 آپلود صدا', en: '🎵 Upload audio', ar: '🎵 رفع الصوت' },
  'chat.audio.tooltip': { fa: 'آپلود فایل صوتی (مدل هیبرید فارسی)', en: 'Upload audio file (Hybrid Persian model)', ar: 'رفع ملف صوتي (نموذج هجين فارسي)' },

  // Analysis
  'analysis.mode.title': { fa: '📊 حالت تحلیل', en: '📊 Analysis mode', ar: '📊 وضع التحليل' },
  'analysis.model.title': { fa: '🤖 مدل تحلیل', en: '🤖 Analysis model', ar: '🤖 نموذج التحليل' },
  'analysis.model.select': { fa: 'انتخاب مدل...', en: 'Select model...', ar: 'اختر نموذج...' },
  'analysis.model.second': { fa: '🤖 مدل دوم تحلیل', en: '🤖 Second analysis model', ar: '🤖 نموذج التحليل الثاني' },
  'analysis.model.second.select': { fa: 'انتخاب مدل دوم...', en: 'Select second model...', ar: 'اختر النموذج الثاني...' },
  'analysis.model.judge': { fa: '⚖️ مدل داور تحلیل', en: '⚖️ Analysis judge model', ar: '⚖️ نموذج حكم التحليل' },
  'analysis.model.judge.select': { fa: 'انتخاب مدل داور...', en: 'Select judge model...', ar: 'اختر نموذج الحكم...' },
  'analysis.input.title': { fa: 'متن ورودی', en: 'Input text', ar: 'النص المدخل' },
  'analysis.input.hint': { fa: '💡 می‌توانید متن را مستقیماً وارد کنید، فایل آپلود کنید، یا صدا ضبط/آپلود کنید', en: '💡 You can type text, upload a file, or record/upload audio', ar: '💡 يمكنك كتابة نص أو رفع ملف أو تسجيل/رفع صوت' },
  'analysis.file.choose': { fa: 'انتخاب فایل', en: 'Choose file', ar: 'اختر ملف' },
  'analysis.audio.upload': { fa: '🎵 آپلود صدا', en: '🎵 Upload audio', ar: '🎵 رفع الصوت' },
  'analysis.record.start': { fa: '🎤 ضبط صدا', en: '🎤 Record audio', ar: '🎤 تسجيل صوت' },
  'analysis.record.stop': { fa: '⏹ توقف ضبط', en: '⏹ Stop recording', ar: '⏹ إيقاف التسجيل' },
  'analysis.file.selected.extract': { fa: 'استخراج از فایل', en: 'Extract from file', ar: 'استخراج من الملف' },
  'analysis.extract.start': { fa: 'شروع تحلیل', en: 'Start analysis', ar: 'بدء التحليل' },
  'analysis.extract.loading': { fa: 'در حال استخراج...', en: 'Extracting...', ar: 'جارٍ الاستخراج...' },
  'analysis.report.html': { fa: 'گزارش HTML', en: 'HTML Report', ar: 'تقرير HTML' },
  'analysis.models.reload': { fa: 'بارگیری مدل‌ها', en: 'Reload models', ar: 'إعادة تحميل النماذج' },
  'analysis.models.loading': { fa: 'بارگیری...', en: 'Loading...', ar: 'جارٍ التحميل...' },
  'analysis.smart.title': { fa: 'تفسیر هوشمند', en: 'Smart Interpretation', ar: 'تفسير ذكي' },
  'analysis.confidence': { fa: 'اطمینان', en: 'Confidence', ar: 'الثقة' },

  // Header description
  'header.desc.chat': { fa: 'دستیار تعاملی هوشمند', en: 'Interactive smart assistant', ar: 'مساعد تفاعلي ذكي' },
  'header.desc.analysis': { fa: 'استخراج روابط چند گانه از متن', en: 'Multi-relation extraction from text', ar: 'استخراج علاقات متعددة من النص' },

  // Database
  'db.view.structure': { fa: 'مشاهده ساختار پایگاه داده', en: 'View database structure', ar: 'عرض هيكل قاعدة البيانات' },
  'db.inactive': { fa: 'اتصال به پایگاه داده غیرفعال', en: 'Database connection inactive', ar: 'اتصال قاعدة البيانات غير نشط' },
  'db.connection': { fa: 'اتصال به پایگاه داده', en: 'Database connection', ar: 'اتصال قاعدة البيانات' },
  'active': { fa: 'فعال', en: 'Active', ar: 'نشط' },
  'inactive': { fa: 'غیرفعال', en: 'Inactive', ar: 'غير نشط' },

  // Auth
  'auth.title.loggedIn': { fa: 'پروفایل/مدیریت', en: 'Profile/Manage', ar: 'الملف/الإدارة' },
  'auth.title.loggedOut': { fa: 'ورود/ثبت‌نام', en: 'Login/Register', ar: 'تسجيل الدخول/التسجيل' },
}

interface I18nContextValue {
  locale: Locale
  setLocale: (l: Locale) => void
  direction: 'rtl' | 'ltr'
  t: (key: string) => string
}

const I18nContext = createContext<I18nContextValue | undefined>(undefined)

const DEFAULT_LOCALE: Locale = 'fa'
const STORAGE_KEY = 'app.locale'

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => {
    const saved = localStorage.getItem(STORAGE_KEY) as Locale | null
    return saved === 'fa' || saved === 'en' || saved === 'ar' ? saved : DEFAULT_LOCALE
  })

  const direction: 'rtl' | 'ltr' = locale === 'en' ? 'ltr' : 'rtl'

  const setLocale = (l: Locale) => {
    setLocaleState(l)
    localStorage.setItem(STORAGE_KEY, l)
  }

  useEffect(() => {
    document.documentElement.setAttribute('lang', locale)
    document.documentElement.setAttribute('dir', direction)
  }, [locale, direction])

  const t = useMemo(() => {
    return (key: string) => (translations[key]?.[locale] ?? translations[key]?.[DEFAULT_LOCALE] ?? key)
  }, [locale])

  const value = useMemo(() => ({ locale, setLocale, direction, t }), [locale, direction])

  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  )
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext)
  if (!ctx) throw new Error('useI18n must be used within I18nProvider')
  return ctx
}


