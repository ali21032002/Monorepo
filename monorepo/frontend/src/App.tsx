import { useMemo, useState, useEffect, useRef } from 'react'
import './App.css'
import ChartComponent from './components/ChartComponent'
import DatabasePopup from './components/DatabasePopup'
import AuthPanel from './components/AuthPanel'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { useI18n } from './contexts/I18nContext'

// Function to translate model names to Persian
const translateModelName = (modelName: string): string => {
  const modelTranslations: Record<string, string> = {
    'gemma2:9b': 'مدل اول با 2:9 بیلیون پارامتر',
    'gemma2:2b': 'مدل دوم با 2:2 بیلیون پارامتر',
    'gemma3:4b': 'مدل سوم با 3:4 بیلیون پارامتر',
    'qwen2.5:7b': 'مدل چهارم با 2.5:7 بیلیون پارامتر',
    'qwen2.5.2:7b': 'مدل پنجم با 2.5.2:7 بیلیون پارامتر',
    'llama3:8b': 'مدل ششم با 3:8 بیلیون پارامتر',
    'llava:7b': 'مدل هفتم با 7 بیلیون پارامتر',
    'mistral:7b': 'مدل هشتم با 7 بیلیون پارامتر',
    'codellama:7b': 'مدل نهم با 7 بیلیون پارامتر',
    'phi3:3.8b': 'مدل دهم با 3:3.8 بیلیون پارامتر',
    'deepseek-coder:6.7b': 'مدل یازدهم با 6.7 بیلیون پارامتر',
    'gemma2:latest': 'مدل دوازدهم (آخرین نسخه)',
    'gemma3:latest': 'مدل سیزدهم (آخرین نسخه)',
    'qwen2.5:latest': 'مدل چهاردهم (آخرین نسخه)',
    'llama3:latest': 'مدل پانزدهم (آخرین نسخه)',
    'mistral:latest': 'مدل شانزدهم (آخرین نسخه)',
    'codellama:latest': 'مدل هفدهم (آخرین نسخه)',
    'phi3:latest': 'مدل هجدهم (آخرین نسخه)',
    'deepseek-coder:latest': 'مدل نوزدهم (آخرین نسخه)',
    'llava:latest': 'مدل بیستم (آخرین نسخه)'
  }
  
  // Check if it's a :latest model that's not in our list
  if (modelName.endsWith(':latest') && !modelTranslations[modelName]) {
    const baseModel = modelName.replace(':latest', '')
    return `${baseModel} (آخرین نسخه)`
  }
  
  return modelTranslations[modelName] || modelName
}

interface Entity { id?: string; name: string; type: string; attributes?: Record<string, any> }
interface Relationship { id?: string; source_entity_id: string; target_entity_id: string; type: string; attributes?: Record<string, any> }
interface ExtractionResponse { text: string; language: string; model: string; entities: Entity[]; relationships: Relationship[] }

interface ModelAnalysis {
  model_name: string
  entities: Entity[]
  relationships: Relationship[]
  confidence_score?: number
  reasoning?: string
}

interface MultiModelResponse {
  text: string
  language: string
  domain: string
  first_analysis: ModelAnalysis
  second_analysis: ModelAnalysis
  final_analysis: ModelAnalysis
  agreement_score?: number
  conflicting_entities: string[]
  conflicting_relationships: string[]
}

interface Interpretation {
  text: string
  confidence: 'high' | 'medium' | 'low'
  type: 'inference' | 'risk' | 'warning' | 'conclusion'
  entities: string[]
}

interface ChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  isAudio?: boolean
  audioUrl?: string
  analysis?: ExtractionResponse | MultiModelResponse | null
  analysisMode?: 'single' | 'multi'
  chart?: ChartData | null
}

interface ChartData {
  type: 'line' | 'bar' | 'pie' | 'doughnut';
  title: string;
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }[];
}

interface ChatResponse {
  message: string
  analysis?: ExtractionResponse | MultiModelResponse | null
  analysisMode?: 'single' | 'multi'
  chart?: ChartData | null
}

// Elasticsearch indices status response shape
interface EsIndicesResponse {
  enabled?: boolean
  configured?: string[]
  existing?: string[]
  error?: string
}

function InnerApp() {
  const { t, locale, setLocale, direction } = useI18n()
  const REQUEST_TIMEOUT_MS = 130000

  const fetchWithTimeout = async (input: RequestInfo | URL, init: RequestInit = {}, timeoutMs = REQUEST_TIMEOUT_MS) => {
    const controller = new AbortController()
    const id = setTimeout(() => controller.abort(), timeoutMs)
    try {
      const resp = await fetch(input, { ...init, signal: controller.signal })
      return resp
    } finally {
      clearTimeout(id)
    }
  }

  // Fetch Elasticsearch status periodically
  const refreshEsStatus = async () => {
    try {
      setEsLoading(true)
      const resp = await fetchWithTimeout('/api/reports/indices', { method: 'GET' })
      const data: EsIndicesResponse = await resp.json()
      setEsInfo(data)
    } catch (e) {
      setEsInfo({ enabled: false, error: (e as Error).message })
    } finally {
      setEsLoading(false)
    }
  }

  useEffect(() => {
    refreshEsStatus()
    const t = setInterval(() => refreshEsStatus(), 30000)
    return () => clearInterval(t)
  }, [])

  // Tab navigation
  const [activeTab, setActiveTab] = useState<'analysis' | 'chat'>('analysis')
  
  // Common settings
  const [language, setLanguage] = useState<'fa' | 'en' | 'ar'>(locale)
  const [domain, setDomain] = useState<'general' | 'medical'>('general')
  const [error, setError] = useState<string | null>(null)
  
  // Models
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [modelsLoading, setModelsLoading] = useState(true)
  
  // Analysis states
  const [text, setText] = useState('شخصی با هویت معلوم ؛ با نام که خودش گفته به اسم حسن جودت شندی وارد یک مغازه طلافروشی شده ، مقداری طلا را خریداری کرده ولی بدون پرداخت پول و بدون دریافت فاکتور از مغازه خارج شده است')
  const [analysisMode, setAnalysisMode] = useState<'single' | 'multi'>('single')
  const [model, setModel] = useState('')
  const [modelFirst, setModelFirst] = useState('')
  const [modelSecond, setModelSecond] = useState('')
  const [modelReferee, setModelReferee] = useState('')
  const [result, setResult] = useState<ExtractionResponse | null>(null)
  const [multiResult, setMultiResult] = useState<MultiModelResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  
  // Chat states
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatInputRef, setChatInputRef] = useState<HTMLTextAreaElement | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [uploadedImages, setUploadedImages] = useState<File[]>([])
  const [imagePreviewUrls, setImagePreviewUrls] = useState<string[]>([])
  
  // Auto-resize textarea function
  const autoResizeTextarea = (textarea: HTMLTextAreaElement) => {
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 128) + 'px' // Max height of 8rem (128px)
  }

  // Handle image upload
  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files) return

    const newImages: File[] = []
    const newPreviewUrls: string[] = []

    Array.from(files).forEach(file => {
      if (file.type.startsWith('image/')) {
        newImages.push(file)
        const url = URL.createObjectURL(file)
        newPreviewUrls.push(url)
      }
    })

    setUploadedImages(prev => [...prev, ...newImages])
    setImagePreviewUrls(prev => [...prev, ...newPreviewUrls])
  }

  // Remove image
  const removeImage = (index: number) => {
    setUploadedImages(prev => prev.filter((_, i) => i !== index))
    setImagePreviewUrls(prev => {
      URL.revokeObjectURL(prev[index])
      return prev.filter((_, i) => i !== index)
    })
  }

  // Cleanup image URLs on unmount
  useEffect(() => {
    return () => {
      imagePreviewUrls.forEach(url => URL.revokeObjectURL(url))
    }
  }, [imagePreviewUrls])
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null)
  const [chatLoading, setChatLoading] = useState(false)
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null)
  const [speechModels, setSpeechModels] = useState<any>(null)
  const [chatMode, setChatMode] = useState<'single' | 'multi'>('single')
  const [darkMode, setDarkMode] = useState(true)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [authOpen, setAuthOpen] = useState(false)
  const [settingsTab, setSettingsTab] = useState<'chat' | 'analysis' | 'general'>('chat')
  const [databasePopupOpen, setDatabasePopupOpen] = useState(false)
  
  // Typing animation states
  const [typingMessageId, setTypingMessageId] = useState<string | null>(null)
  const [typingText, setTypingText] = useState('')

  // Elasticsearch status
  const [esInfo, setEsInfo] = useState<EsIndicesResponse | null>(null)
  const [, setEsLoading] = useState<boolean>(false)

  // Apply dark mode to body and html
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark-mode')
      document.body.classList.add('dark-mode')
    } else {
      document.documentElement.classList.remove('dark-mode')
      document.body.classList.remove('dark-mode')
    }
  }, [darkMode])

  // Sync app language with i18n provider
  useEffect(() => {
    setLanguage(locale)
  }, [locale])

  useEffect(() => {
    setLocale(language)
    // Update document title when language changes
    document.title = t('app.title')
  }, [language])
  
  // Ref for auto-scrolling chat messages
  const chatMessagesEndRef = useRef<HTMLDivElement>(null)
  
  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    chatMessagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // Typing animation function
  const typeText = (text: string, messageId: string, baseSpeed: number = 30) => {
    // Skip typing animation for messages containing HTML tables
    if (text.includes('<table') && text.includes('</table>')) {
      // For table content, show immediately without typing animation
      setChatMessages(prev => prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, content: text }
          : msg
      ))
      // Scroll to bottom immediately
      setTimeout(() => scrollToBottom(), 100)
      return
    }
    
    setTypingMessageId(messageId)
    setTypingText('')
    
    // Adjust speed based on text length - shorter texts type faster
    const adjustedSpeed = text.length > 200 ? baseSpeed : Math.max(baseSpeed * 0.7, 15)
    
    let currentIndex = 0
    const interval = setInterval(() => {
      if (currentIndex < text.length) {
        setTypingText(text.substring(0, currentIndex + 1))
        currentIndex++
        
        // Auto-scroll every few characters to avoid too much scrolling
        if (currentIndex % 10 === 0) {
          scrollToBottom()
        }
      } else {
        clearInterval(interval)
        setTypingMessageId(null)
        setTypingText('')
        
        // Update the actual message with full text
        setChatMessages(prev => prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, content: text }
            : msg
        ))
        
        // Final scroll to bottom
        setTimeout(() => scrollToBottom(), 100)
      }
    }, adjustedSpeed)
    
    return () => clearInterval(interval)
  }

  // Computed values - removed unused entityCount and relCount

  // Generate smart interpretations
  const generateInterpretations = (entities: Entity[], relationships: Relationship[], domain: string, language: string): Interpretation[] => {
    const interpretations: Interpretation[] = []
    
    console.log('🧠 Generating interpretations for:', { entities, relationships, domain, language })
    
    // Find suspects and crimes (flexible matching)
    const suspects = entities.filter(e => 
      e.type === 'SUSPECT' || 
      e.type === 'PERSON' || 
      (e.name && (e.name.includes('حسن') || e.name.includes('علی') || e.name.includes('احمد')))
    )
    
    const suspiciousBehaviors = entities.filter(e => 
      e.type === 'SUSPICIOUS_BEHAVIOR' || 
      (e.name && (e.name.includes('بدون پرداخت') || e.name.includes('بدون فاکتور')))
    )
    
    const criminalInferences = entities.filter(e => 
      e.type === 'CRIMINAL_INFERENCE' || 
      (e.name && (e.name.includes('احتمال') || e.name.includes('دزد')))
    )
    
    console.log('🔍 Found entities:', { suspects, suspiciousBehaviors, criminalInferences })
    
    // Always try to generate some interpretation
    if (suspects.length > 0) {
      const suspectName = suspects[0].name
      
      
      // General interpretations for any domain
      if (interpretations.length === 0) {
        const suspiciousEntities = entities.filter(e => 
          e.name.includes('بدون') || 
          e.name.includes('احتمال') || 
          e.name.includes('خرید') ||
          e.name.includes('طلا')
        )
        
        if (suspiciousEntities.length > 0) {
          interpretations.push({
            text: `${suspectName} در موقعیت مشکوکی قرار دارد. عناصر قابل توجه: ${suspiciousEntities.map(e => e.name).join('، ')}`,
            confidence: 'medium',
            type: 'inference',
            entities: [suspectName, ...suspiciousEntities.map(e => e.name)]
          })
        }
      }
    }
    
    console.log('✅ Generated interpretations:', interpretations)
    return interpretations
  }

  // Get interpretations for current results
  const interpretations = useMemo(() => {
    if (analysisMode === 'single' && result) {
      return generateInterpretations(result.entities, result.relationships, domain, language)
    } else if (analysisMode === 'multi' && multiResult) {
      return generateInterpretations(
        multiResult.final_analysis.entities, 
        multiResult.final_analysis.relationships, 
        multiResult.domain, 
        multiResult.language
      )
    }
    return []
  }, [result, multiResult, analysisMode, language, domain])

  // Load available models
  const loadModels = async () => {
    setModelsLoading(true)
    try {
      console.log('🔄 Loading models from /api/models...')
      const resp = await fetchWithTimeout('/api/models')
      console.log('📡 Response status:', resp.status, resp.statusText)
      
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`)
      const data = await resp.json()
      console.log('📊 Models data received:', data)
      
      if (data.models && data.models.length > 0) {
        console.log('✅ Setting models:', data.models)
        setAvailableModels(data.models)
        
        if (!model && data.models.length > 0) setModel(data.models[0])
        if (!modelFirst && data.models.length > 0) setModelFirst(data.models[0])
        if (!modelSecond && data.models.length > 1) setModelSecond(data.models[1])
        if (!modelReferee && data.models.length > 2) setModelReferee(data.models[2])
        else if (!modelReferee && data.models.length > 0) setModelReferee(data.models[0])
      } else {
        console.warn('⚠️ No models found in response')
      }
    } catch (e: any) {
      console.error('❌ Failed to load models:', e)
      const fallbackModels = ['gemma3:4b', 'qwen2.5.2:7b', 'llava:7b']
      console.log('🔄 Using fallback models:', fallbackModels)
      setAvailableModels(fallbackModels)
      setModel(fallbackModels[0])
      setModelFirst(fallbackModels[0])
      setModelSecond(fallbackModels[1])
      setModelReferee(fallbackModels[2])
    } finally {
      setModelsLoading(false)
    }
    
    // Also load speech models
    await loadSpeechModels()
  }

  // Load speech models status
  const loadSpeechModels = async () => {
    try {
      // Load general speech models
      const response = await fetchWithTimeout('/api/speech-models', {
        method: 'GET',
      })
      
      if (response.ok) {
        const data = await response.json()
        setSpeechModels(data)
        console.log('🎯 Speech models loaded:', data)
      }
      
      // Also load chatbot-specific status
      const chatResponse = await fetchWithTimeout('/api/chat-speech-status', {
        method: 'GET',
      })
      
      if (chatResponse.ok) {
        const chatData = await chatResponse.json()
        console.log('🎯 Chat speech status loaded:', chatData)
      }
    } catch (e) {
      console.error('Failed to load speech models:', e)
    }
  }

  useEffect(() => {
    loadModels()
  }, [])

  // Auto-scroll when messages change
  useEffect(() => {
    scrollToBottom()
  }, [chatMessages, chatLoading])

  // Analysis functions
  const onSingleExtract = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    setMultiResult(null)
    try {
      const resp = await fetchWithTimeout('/api/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, language, model, schema: 'general' }),
      })
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`)
      const data: ExtractionResponse = await resp.json()
      setResult(data)
    } catch (e: any) {
      setError(e?.name === 'AbortError' ? 'Timeout' : (e.message || 'Failed'))
    } finally {
      setLoading(false)
    }
  }

  const onMultiExtract = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    setMultiResult(null)
    try {
      const resp = await fetchWithTimeout('/api/multi_extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          language,
          domain,
          model_first: modelFirst,
          model_second: modelSecond,
          model_referee: modelReferee,
        }),
      })
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`)
      const data: MultiModelResponse = await resp.json()
      setMultiResult(data)
    } catch (e: any) {
      setError(e?.name === 'AbortError' ? 'Timeout' : (e.message || 'Failed'))
    } finally {
      setLoading(false)
    }
  }

  const onExtract = async () => {
    if (analysisMode === 'single') {
      await onSingleExtract()
    } else {
      await onMultiExtract()
    }
  }

  const onExtractFile = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('language', language)
      fd.append('schema', 'general')
      fd.append('model', model)
      const resp = await fetchWithTimeout('/api/extract_file', { method: 'POST', body: fd })
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`)
      const data: ExtractionResponse = await resp.json()
      setResult(data)
      setText(data.text)
      
      // Clear the file after successful extraction to re-enable other controls
      setFile(null)
      console.log('📄 File extracted successfully, controls re-enabled')
    } catch (e: any) {
      setError(e?.name === 'AbortError' ? 'Timeout' : (e.message || 'Failed'))
    } finally {
      setLoading(false)
    }
  }

  const onReport = async () => {
    const resp = await fetchWithTimeout('/api/report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language, model, schema: 'general' }),
    })
    const html = await resp.text()
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
  }

  // Chart request detection function
  const detectChartRequest = (message: string): string | null => {
    const messageLower = message.toLowerCase()
    
    // Direct chart request keywords
    const directChartKeywords = [
      'نمودار', 'چارت', 'گراف', 'chart', 'graph',
      'رسم کن', 'بکش', 'نشان بده', 'نمایش بده',
      'تصویری نشان بده', 'بصری نشان بده'
    ]
    
    // Strong indicators for chart requests
    const strongIndicators = [
      'نمودار بکش', 'چارت بکش', 'رسم کن', 'گراف بکش',
      'نمودار رسم کن', 'نمودار بده', 'نمودار نمایش بده',
      'chart draw', 'draw chart', 'visualize this', 'create chart',
      'نمودار میخوام', 'نمودار می‌خوام', 'chart میخوام'
    ]
    
    // Check for strong indicators first
    for (const indicator of strongIndicators) {
      if (messageLower.includes(indicator)) {
        return 'strong_request'
      }
    }
    
    // Check for direct chart keywords
    const directCount = directChartKeywords.filter(keyword => messageLower.includes(keyword)).length
    if (directCount > 0) {
      return 'direct_request'
    }
    
    // Check for analytical content that might benefit from charts
    // BUT ONLY if there are actual numbers or data to visualize
    const analyticalPatterns = [
      'مقایسه', 'تفاوت', 'بیشتر', 'کمتر', 'برتر', 'بدتر',
      'درصد', 'تعداد', 'مقدار', 'میزان', 'سطح', 'نرخ',
      'افزایش', 'کاهش', 'روند', 'تغییر', 'پیشرفت'
    ]
    
    // Check for actual numbers or quantitative data
    const hasNumbers = /\d+/.test(message)
    const hasDataWords = ['آمار', 'داده', 'statistics', 'data', 'dataset', 'عدد', 'رقم', 'اعداد'].some(word => messageLower.includes(word))
    
    const analyticalCount = analyticalPatterns.filter(pattern => messageLower.includes(pattern)).length
    
    // Only suggest chart for analytical content if there are actual numbers or data
    if (analyticalCount >= 2 && (hasNumbers || hasDataWords)) {
      return 'analytical_content'
    }
    
    return null
  }


  // Chat functions
  const sendChatMessage = async (message: string, isAudio = false, audioUrl?: string) => {
    if (!message.trim() && !isAudio && uploadedImages.length === 0) return
    
    // Detect chart request
    const chartRequestType = detectChartRequest(message)
    if (chartRequestType) {
      console.log(`📊 Chart request detected in frontend: ${chartRequestType}`)
    }

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: message,
      timestamp: new Date(),
      isAudio,
      audioUrl
    }
    
    setChatMessages(prev => [...prev, userMessage])
    setChatInput('')
    setChatLoading(true)
    
    // Scroll to bottom after adding user message
    setTimeout(() => scrollToBottom(), 100)

    try {
      // Enhanced message history management with importance weighting
      const prepareMessageHistory = (messages: ChatMessage[]) => {
        // Exclude the current user message that was just added
        const previousMessages = messages.slice(0, -1)
        
        // If we have few messages, send all of them
        if (previousMessages.length <= 8) {
          return previousMessages.map(msg => ({
            role: msg.type === 'user' ? 'user' : 'assistant',
            content: msg.content
          }))
        }
        
        // Enhanced selection strategy with importance weighting:
        // 1. Calculate importance scores for all messages
        // 2. Prioritize newer messages with higher coefficients
        // 3. Boost messages with history references
        // 4. Select based on combined importance scores
        
        const calculateMessageImportance = (msg: ChatMessage, index: number, total: number) => {
          let score = 0
          const content = msg.content.toLowerCase()
          
          // Recency weight - newer messages get higher scores (exponential boost)
          const recencyWeight = 1.0 + (index / total) * 1.2  // 1.0 to 2.2 range
          score += recencyWeight * 10
          
          // Content importance
          const highImportanceKeywords = ['نام', 'اسم', 'کیه', 'کیست', 'کجا', 'چطور', 'چرا', 'چگونه', 'مشکل', 'خطا', 'اشتباه', 'کمک', 'راهنمایی', 'تحلیل', 'بررسی', 'نمودار', 'توضیح', 'پیشنهاد', 'نتیجه', 'مهم', 'ضروری', 'اولویت']
          const mediumImportanceKeywords = ['سوال', 'پاسخ', 'جواب', 'درباره', 'راجع', 'موضوع', 'بحث']
          
          // Count keyword matches
          const highMatches = highImportanceKeywords.filter(keyword => content.includes(keyword)).length
          const mediumMatches = mediumImportanceKeywords.filter(keyword => content.includes(keyword)).length
          
          score += highMatches * 8  // High importance keywords
          score += mediumMatches * 4  // Medium importance keywords
          
          // History reference boost - VERY IMPORTANT
          const historyKeywords = ['قبلا', 'قبل', 'پیش', 'سابقه', 'تاریخچه', 'مکالمه قبل', 'پیام قبل', 'گفتم', 'گفتی', 'گفته', 'یادت', 'یادم', 'یاد', 'همون', 'همان', 'آن چیزی', 'اون چیزی']
          const historyMatches = historyKeywords.filter(keyword => content.includes(keyword)).length
          if (historyMatches > 0) {
            score += historyMatches * 15  // Major boost for history references
            console.log(`📊 History reference detected in message ${index}: "${msg.content.substring(0, 50)}..." (boost: +${historyMatches * 15})`)
          }
          
          // Question boost
          if (content.includes('؟') || content.includes('?')) {
            score += 6
          }
          
          // Length boost for detailed messages
          if (msg.content.length > 100) score += 3
          if (msg.content.length > 200) score += 3
          
          // Name/identity patterns
          const namePatterns = ['نام من', 'اسم من', 'من .+ هستم']
          if (namePatterns.some(pattern => new RegExp(pattern).test(content))) {
            score += 10
          }
          
          return { message: msg, score, index, recencyWeight, historyMatches }
        }
        
        // Calculate importance for all messages
        const scoredMessages = previousMessages.map((msg, index) => 
          calculateMessageImportance(msg, index, previousMessages.length)
        )
        
        // Sort by importance score
        scoredMessages.sort((a, b) => b.score - a.score)
        
        // Log top scoring messages
        console.log('📊 Top 5 most important messages:')
        scoredMessages.slice(0, 5).forEach((scored, i) => {
          console.log(`  ${i+1}. Score: ${scored.score.toFixed(1)} (Recency: ${scored.recencyWeight.toFixed(2)}, History refs: ${scored.historyMatches}) - "${scored.message.content.substring(0, 50)}..."`)
        })
        
        const importantMessages = []
        
        // Always include the most recent 6 messages (highest recency weight)
        const recentMessages = previousMessages.slice(-6)
        importantMessages.push(...recentMessages)
        
        // Add high-scoring messages from the rest
        const remainingMessages = scoredMessages.filter(scored => 
          !recentMessages.some(recent => recent.content === scored.message.content)
        )
        
        // Take top 12 remaining messages by importance
        const additionalMessages = remainingMessages.slice(0, 12).map(scored => scored.message)
        importantMessages.push(...additionalMessages)
        
        // Remove duplicates while preserving chronological order
        const uniqueMessages = []
        const seen = new Set()
        
        for (const msg of importantMessages) {
          const key = `${msg.type}-${msg.content.substring(0, 50)}`
          if (!seen.has(key)) {
            seen.add(key)
            uniqueMessages.push(msg)
          }
        }
        
        // Sort by original message order (chronological) to maintain conversation flow
        uniqueMessages.sort((a, b) => {
          const aIndex = previousMessages.findIndex(m => m.content === a.content)
          const bIndex = previousMessages.findIndex(m => m.content === b.content)
          return aIndex - bIndex
        })
        
        // Convert to API format
        const finalMessages = uniqueMessages.map(msg => ({
          role: msg.type === 'user' ? 'user' : 'assistant',
          content: msg.content
        }))
        
        // Limit to 20 messages for better context while maintaining performance
        const limitedMessages = finalMessages.slice(-20)
        
        // Enhanced logging
        console.log(`📊 Enhanced message selection with importance weighting:`)
        console.log(`  📝 Total messages: ${previousMessages.length}`)
        console.log(`  📝 Selected messages: ${limitedMessages.length}`)
        console.log(`  📝 Recent messages (high priority): ${recentMessages.length}`)
        console.log(`  📝 Additional important messages: ${additionalMessages.length}`)
        console.log(`  📝 Messages with history references: ${scoredMessages.filter(s => s.historyMatches > 0).length}`)
        
        return limitedMessages
      }
      
      const recentMessages = prepareMessageHistory(chatMessages)
      
      // Debug: Log the message history being sent
      console.log('📝 Sending message history:', recentMessages.length, 'messages')
      console.log('📝 Message history details:', recentMessages)
      
      // Log conversation summary
      if (recentMessages.length > 0) {
        const firstMessage = recentMessages[0]
        const lastMessage = recentMessages[recentMessages.length - 1]
        console.log(`📝 Conversation span: "${firstMessage.content.substring(0, 30)}..." → "${lastMessage.content.substring(0, 30)}..."`)
      }
      
      // Validate message history
      if (recentMessages.length > 15) {
        console.warn('⚠️ Large message history may affect performance')
      }
      
      // Check for proper conversation flow
      const userCount = recentMessages.filter(msg => msg.role === 'user').length
      const assistantCount = recentMessages.filter(msg => msg.role === 'assistant').length
      console.log(`📝 Message balance: ${userCount} user, ${assistantCount} assistant messages`)
      
      // Check for conversation quality
      if (userCount > 0 && assistantCount > 0) {
        const balanceRatio = userCount / assistantCount
        if (balanceRatio > 2) {
          console.warn('⚠️ Warning: User messages significantly outnumber assistant messages')
        } else if (balanceRatio < 0.5) {
          console.warn('⚠️ Warning: Assistant messages significantly outnumber user messages')
        } else {
          console.log('✅ Good conversation balance')
        }
      }
      
      // Check for important content
      const allContent = recentMessages.map(msg => msg.content).join(' ')
      if (allContent.includes('نام') || allContent.includes('اسم')) {
        console.log('📝 Context contains name/identity information')
      }
      if (allContent.includes('مشکل') || allContent.includes('خطا')) {
        console.log('📝 Context contains problem/error information')
      }
      if (allContent.includes('؟') || allContent.includes('?')) {
        console.log('📝 Context contains questions')
      }

      // Check if we have images to send
      if (uploadedImages.length > 0) {
        // Send images with FormData
        const formData = new FormData()
        formData.append('message', message)
        formData.append('language', language)
        formData.append('domain', domain)
        formData.append('model', model || modelReferee || 'gemma3:4b')
        formData.append('analysisMode', chatMode)
        formData.append('message_history', JSON.stringify(recentMessages))
        
        if (chatMode === 'multi') {
          formData.append('model_first', modelFirst || 'gemma3:4b')
          formData.append('model_second', modelSecond || 'qwen2.5:7b')
          formData.append('model_referee', modelReferee || 'llama3:8b')
        }
        
        // Add images
        uploadedImages.forEach((image) => {
          formData.append(`images`, image)
        })
        
        const resp = await fetchWithTimeout('/api/chat-with-images', {
          method: 'POST',
          body: formData
        })
        
        // Clear uploaded images after sending
        setUploadedImages([])
        setImagePreviewUrls(prev => {
          prev.forEach(url => URL.revokeObjectURL(url))
          return []
        })
        
        if (!resp.ok) {
          throw new Error(`HTTP ${resp.status}: ${resp.statusText}`)
        }
        
        const data = await resp.json()
        
        // Handle response (always image processing message for now)
        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: data.response || 'در حال حاضر سرویس پردازش تصویر در حال پیاده سازی است و به زودی قابل استفاده خواهد بود',
          timestamp: new Date()
        }
        setChatMessages(prev => [...prev, assistantMessage])
        setChatLoading(false)
        setTimeout(() => scrollToBottom(), 100)
        return
      }
      
      // Regular text-only request
      const resp = await fetchWithTimeout('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          language,
          domain,
          model: model || modelReferee || 'gemma3:4b',
          analysisMode: chatMode,
          message_history: recentMessages,
          ...(chatMode === 'multi' && {
            model_first: modelFirst,
            model_second: modelSecond,
            model_referee: modelReferee
          })
        }),
      })

      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`)
      const data: ChatResponse = await resp.json()

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.message,
        timestamp: new Date(),
        analysis: data.analysis,
        analysisMode: data.analysisMode,
        chart: data.chart
      }

      // Log response quality
      console.log(`📝 Received response: ${data.message.length} characters`)
      if (data.message.length < 10) {
        console.warn('⚠️ Warning: Very short response from server')
      } else if (data.message.length > 500) {
        console.log('📝 Long response received')
      }
      
      // Check if response seems to consider history
      if (recentMessages.length > 0) {
        const historyIndicators = ['قبلاً', 'سابقاً', 'گفتم', 'گفتید', 'قبل', 'پیش', 'همان', 'همین']
        const considersHistory = historyIndicators.some(indicator => data.message.includes(indicator))
        if (considersHistory) {
          console.log('✅ Response appears to consider conversation history')
        } else {
          console.log('⚠️ Response may not be considering conversation history')
        }
        
        // Check for specific references to previous messages
        const hasSpecificReference = recentMessages.some(msg => 
          msg.content.length > 10 && data.message.includes(msg.content.substring(0, 10))
        )
        if (hasSpecificReference) {
          console.log('✅ Response contains specific reference to previous message')
        }
        
        // Check for continuity in conversation
        const hasContinuity = recentMessages.some(msg => 
          msg.role === 'user' && data.message.toLowerCase().includes(msg.content.toLowerCase().substring(0, 5))
        )
        if (hasContinuity) {
          console.log('✅ Response shows good conversation continuity')
        }
        
        // Check for context awareness
        const hasContextAwareness = recentMessages.some(msg => 
          msg.role === 'assistant' && data.message.toLowerCase().includes(msg.content.toLowerCase().substring(0, 5))
        )
        if (hasContextAwareness) {
          console.log('✅ Response shows context awareness from previous assistant messages')
        }
        
        // Overall conversation quality assessment
        const qualityIndicators = [
          considersHistory,
          hasSpecificReference,
          hasContinuity,
          hasContextAwareness
        ]
        const qualityScore = qualityIndicators.filter(Boolean).length
        console.log(`📝 Conversation quality score: ${qualityScore}/4`)
        
        if (qualityScore >= 3) {
          console.log('✅ Excellent conversation quality')
        } else if (qualityScore >= 2) {
          console.log('✅ Good conversation quality')
        } else if (qualityScore >= 1) {
          console.log('⚠️ Fair conversation quality')
        } else {
          console.log('⚠️ Poor conversation quality - may not be considering history')
        }
        
        // Store quality score for potential future use
        if (qualityScore < 2) {
          console.warn('⚠️ Consider improving conversation context or model parameters')
        }
        
        // Log conversation summary for debugging
        console.log(`📝 Conversation summary: ${recentMessages.length} messages, quality: ${qualityScore}/4`)
        if (recentMessages.length > 0) {
          const lastUserMessage = recentMessages.filter(msg => msg.role === 'user').pop()
          const lastAssistantMessage = recentMessages.filter(msg => msg.role === 'assistant').pop()
          if (lastUserMessage) {
            console.log(`📝 Last user message: "${lastUserMessage.content.substring(0, 50)}..."`)
          }
          if (lastAssistantMessage) {
            console.log(`📝 Last assistant message: "${lastAssistantMessage.content.substring(0, 50)}..."`)
          }
        }
        
        // Log current message for context
        console.log(`📝 Current user message: "${message.substring(0, 50)}..."`)
        console.log(`📝 Current assistant response: "${data.message.substring(0, 50)}..."`)
        
        // Log conversation flow for debugging
        console.log(`📝 Conversation flow: ${recentMessages.length} previous messages → current exchange`)
        if (recentMessages.length > 0) {
          const userMessages = recentMessages.filter(msg => msg.role === 'user').length
          const assistantMessages = recentMessages.filter(msg => msg.role === 'assistant').length
          console.log(`📝 Previous flow: ${userMessages} user messages, ${assistantMessages} assistant messages`)
        }
        
        // Log conversation quality metrics
        console.log(`📝 Quality metrics: History consideration: ${considersHistory}, Specific refs: ${hasSpecificReference}, Continuity: ${hasContinuity}, Context awareness: ${hasContextAwareness}`)
        
        // Log conversation health check
        const healthCheck = {
          hasHistory: recentMessages.length > 0,
          hasQuality: qualityScore >= 2,
          hasContinuity: hasContinuity,
          hasContext: hasContextAwareness
        }
        console.log(`📝 Conversation health check:`, healthCheck)
        
        if (!healthCheck.hasHistory) {
          console.warn('⚠️ No conversation history available')
        }
        if (!healthCheck.hasQuality) {
          console.warn('⚠️ Low conversation quality detected')
        }
        
        // Log conversation improvement suggestions
        if (qualityScore < 2) {
          console.log('💡 Suggestions for better conversation quality:')
          if (!considersHistory) {
            console.log('  - Model may need better history context')
          }
          if (!hasSpecificReference) {
            console.log('  - Model may need to reference specific previous messages')
          }
          if (!hasContinuity) {
            console.log('  - Model may need better conversation continuity')
          }
          if (!hasContextAwareness) {
            console.log('  - Model may need better context awareness')
          }
        }
        
        // Log conversation performance summary
        console.log(`📝 Performance summary: ${recentMessages.length} messages processed, quality score: ${qualityScore}/4, response time: ${Date.now() - Date.now()}ms`)
      }

      // Add assistant message with empty content first
      const assistantMessageWithEmptyContent = {
        ...assistantMessage,
        content: ''
      }
      setChatMessages(prev => [...prev, assistantMessageWithEmptyContent])
      
      // Start typing animation
      setTimeout(() => {
        typeText(data.message, assistantMessage.id, 20) // 20ms per character
      }, 200)
    } catch (e: any) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `خطا در پردازش پیام: ${e.message || 'نامشخص'}`,
        timestamp: new Date()
      }
      setChatMessages(prev => [...prev, errorMessage])
      
      // Scroll to bottom after adding error message
      setTimeout(() => scrollToBottom(), 100)
    } finally {
      setChatLoading(false)
    }
  }

  // Audio upload handler for chat tab
  const handleChatAudioUpload = async (audioFile: File | undefined) => {
    if (!audioFile) return

    try {
      setChatLoading(true)
      
      // Convert audio to text using hybrid speech-to-text service via backend
      const formData = new FormData()
      formData.append('audio_file', audioFile, 'uploaded_audio.wav')
      formData.append('language', language)
      formData.append('use_hybrid', 'true')
      formData.append('model_preference', 'auto')
      
      const response = await fetchWithTimeout('/api/chat-speech-to-text', {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) {
        throw new Error(`Speech-to-text failed: ${response.status}`)
      }
      
      const transcriptionResult = await response.json()
      const transcribedText = transcriptionResult.text || 'خطا در تبدیل صدا به متن'
      
      if (transcribedText && transcribedText.trim()) {
        // Send the transcribed text as a chat message
        await sendChatMessage(transcribedText, false)
        console.log('🎵 Audio uploaded and transcribed for chat:', transcribedText.substring(0, 100) + '...')
      } else {
        throw new Error('متن استخراج شده خالی است')
      }
    } catch (e: any) {
      console.error('Chat audio upload error:', e)
      
      // Check if the error is due to service unavailability
      let errorMessage = 'خطا در تبدیل صدا به متن. لطفاً دوباره تلاش کنید.'
      
      if (e.name === 'AbortError') {
        errorMessage = 'سرویس تحلیل صدا در دسترس نیست. لطفاً با پشتیبانی تماس بگیرید.'
      } else if (e.message && (
        e.message.includes('Failed to fetch') || 
        e.message.includes('NetworkError') ||
        e.message.includes('ERR_CONNECTION_REFUSED') ||
        e.message.includes('ERR_NETWORK_CHANGED')
      )) {
        errorMessage = 'سرویس تحلیل صدا در دسترس نیست. لطفاً با پشتیبانی تماس بگیرید.'
      } else if (e.message && e.message.includes('Speech-to-text failed: 503')) {
        errorMessage = 'سرویس تحلیل صدا در دسترس نیست. لطفاً با پشتیبانی تماس بگیرید.'
      }
      
      // Send error message to chat
      await sendChatMessage(errorMessage, false)
    } finally {
      setChatLoading(false)
    }
  }

  // Audio upload handler for analysis tab
  const handleAudioUpload = async (audioFile: File | undefined) => {
    if (!audioFile) return

    try {
      setLoading(true)
      setError(null)

      // Convert audio to text using hybrid speech-to-text service
      const formData = new FormData()
      formData.append('audio_file', audioFile)
      formData.append('language', language)
      formData.append('use_hybrid', 'true')
      formData.append('model_preference', 'auto')

      const response = await fetchWithTimeout('/api/speech-to-text', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`خطا در تبدیل صدا به متن: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      
      if (data.text && data.text.trim()) {
        // Set the transcribed text to the textarea
        setText(data.text)
        console.log('🎵 Audio transcribed successfully:', data.text.substring(0, 100) + '...')
      } else {
        throw new Error('متن استخراج شده خالی است')
      }
    } catch (e: any) {
      console.error('Audio upload error:', e)
      setError(`خطا در آپلود صدا: ${e.message || 'نامشخص'}`)
    } finally {
      setLoading(false)
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      const chunks: BlobPart[] = []

      recorder.ondataavailable = (e) => chunks.push(e.data)
      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' })
        const audioUrl = URL.createObjectURL(blob)
        
        // Check if we're in analysis tab or chat tab
        if (activeTab === 'analysis') {
          // For analysis tab, set the transcribed text directly
          try {
            setLoading(true)
            setError(null)
            
            // Send audio to hybrid speech-to-text service
            const formData = new FormData()
            formData.append('audio_file', blob, 'recording.wav')
            formData.append('language', language)
            formData.append('model_preference', 'auto')
            
            const response = await fetchWithTimeout('http://localhost:8001/transcribe-hybrid', {
              method: 'POST',
              body: formData,
            })
            
            if (!response.ok) {
              throw new Error(`Speech-to-text failed: ${response.status}`)
            }
            
            const transcriptionResult = await response.json()
            const transcribedText = transcriptionResult.text || 'خطا در تبدیل صدا به متن'
            
            if (transcribedText && transcribedText.trim()) {
              setText(transcribedText)
              console.log('🎤 Audio transcribed for analysis:', transcribedText.substring(0, 100) + '...')
            } else {
              throw new Error('متن استخراج شده خالی است')
            }
          } catch (e: any) {
            console.error('Audio transcription error:', e)
            setError(`خطا در تبدیل صدا به متن: ${e.message || 'نامشخص'}`)
          } finally {
            setLoading(false)
          }
        } else {
          // For chat tab, use existing chat functionality
          // Add user message with audio
          const userMessage: ChatMessage = {
            id: Date.now().toString(),
            type: 'user',
            content: '[صدا ضبط شد]',
            timestamp: new Date(),
            isAudio: true,
            audioUrl
          }
          setChatMessages(prev => [...prev, userMessage])
          
          // Show processing message
          setChatLoading(true)
          
          // Scroll to bottom after adding user message
          setTimeout(() => scrollToBottom(), 100)
          
          try {
            // Send audio to hybrid speech-to-text service via backend
            const formData = new FormData()
            formData.append('audio_file', blob, 'recording.wav')
            formData.append('language', language)
            formData.append('use_hybrid', 'true')
            formData.append('model_preference', 'auto')
            
            const response = await fetchWithTimeout('/api/chat-speech-to-text', {
              method: 'POST',
              body: formData,
            })
            
            if (!response.ok) {
              throw new Error(`Speech-to-text failed: ${response.status}`)
            }
            
            const transcriptionResult = await response.json()
            const transcribedText = transcriptionResult.text || 'خطا در تبدیل صدا به متن'
            
            // Hide processing message and send transcribed text
            setChatLoading(false)
            await sendChatMessage(transcribedText, false)
          } catch (e: any) {
            console.error('خطا در تبدیل صدا به متن:', e)
            
            // Check if the error is due to service unavailability
            let errorMessage = 'خطا در تبدیل صدا به متن. لطفاً دوباره تلاش کنید.'
            
            if (e.name === 'AbortError') {
              errorMessage = 'سرویس تحلیل صدا در دسترس نیست. لطفاً با پشتیبانی تماس بگیرید.'
            } else if (e.message && (
              e.message.includes('Failed to fetch') || 
              e.message.includes('NetworkError') ||
              e.message.includes('ERR_CONNECTION_REFUSED') ||
              e.message.includes('ERR_NETWORK_CHANGED')
            )) {
              errorMessage = 'سرویس تحلیل صدا در دسترس نیست. لطفاً با پشتیبانی تماس بگیرید.'
            } else if (e.message && e.message.includes('Speech-to-text failed: 503')) {
              errorMessage = 'سرویس تحلیل صدا در دسترس نیست. لطفاً با پشتیبانی تماس بگیرید.'
            }
            
            // Hide processing message and send error message
            setChatLoading(false)
            await sendChatMessage(errorMessage, false)
          }
        }
      }

      recorder.start()
      setMediaRecorder(recorder)
      setIsRecording(true)
    } catch (e) {
      console.error('خطا در ضبط صدا:', e)
      alert('دسترسی به میکروفون امکان‌پذیر نیست')
    }
  }

  const stopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop()
      mediaRecorder.stream.getTracks().forEach(track => track.stop())
      setMediaRecorder(null)
      setIsRecording(false)
    }
  }

  // Copy message function
  const copyMessage = async (messageContent: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(messageContent)
      setCopiedMessageId(messageId)
      
      // Reset copy state after 2 seconds
      setTimeout(() => {
        setCopiedMessageId(null)
      }, 2000)
    } catch (err) {
      console.error('خطا در کپی:', err)
      // Fallback for older browsers
      const textArea = document.createElement('textarea')
      textArea.value = messageContent
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      
      setCopiedMessageId(messageId)
      setTimeout(() => {
        setCopiedMessageId(null)
      }, 2000)
    }
  }

  // Resend message function
  const resendMessage = (messageContent: string) => {
    setChatInput(messageContent)
    // Focus on textarea field after setting the content
    setTimeout(() => {
      if (chatInputRef) {
        chatInputRef.focus()
        chatInputRef.setSelectionRange(chatInputRef.value.length, chatInputRef.value.length)
        autoResizeTextarea(chatInputRef)
      }
    }, 100)
  }

  return (
    <div className={`app ${darkMode ? 'dark-mode' : ''}`}>
      <header className='hero' style={{ direction }}>
        <div className='header-content'>
          <div className='header-controls'>
            <div 
              className={`theme-toggle ${darkMode ? 'dark' : 'light'}`}
              onClick={() => setDarkMode(!darkMode)}
              title={darkMode ? t('theme.toLight') : t('theme.toDark')}
            >
              <div className='toggle-track'>
                <div className='toggle-thumb'>
                  <span className='toggle-icon'>{darkMode ? '🌙' : '☀️'}</span>
                </div>
              </div>
            </div>
            <button 
              className='settings-btn'
              onClick={() => setSettingsOpen(!settingsOpen)}
              title={t('settings.title')}
            >
              ⚙️
            </button>
            <AuthButton onOpen={() => setAuthOpen(true)} />
            
            {/* Database Status Indicator */}
            <div 
              className={`database-status ${esInfo?.enabled && !esInfo?.error ? 'active' : 'inactive'}`}
              onClick={() => esInfo?.enabled && !esInfo?.error && setDatabasePopupOpen(true)}
              title={esInfo?.enabled ? (esInfo?.error ? `${t('db.connection')}: ${esInfo.error}` : t('db.view.structure')) : t('db.inactive')}
            >
              <span className='db-icon'>🗄️</span>
              <span className='db-text'>
                {t('db.connection')} ({esInfo?.enabled && !esInfo?.error ? t('active') : t('inactive')})
              </span>
            </div>

            {/* Model Status Indicator */}
            <div className='model-status-indicator'>
              <div className='status-icon'>
                {activeTab === 'chat' ? (
                  chatMode === 'multi' ? '⚖️' : '🤖'
                ) : (
                  analysisMode === 'multi' ? '⚖️' : '🤖'
                )}
              </div>
              <div className='status-text'>
                {activeTab === 'chat' ? (
                  chatMode === 'multi' ? t('chat.mode.multi') : t('chat.mode.single')
                ) : (
                  analysisMode === 'multi' ? t('chat.mode.multi') : t('chat.mode.single')
                )}
              </div>
            </div>
          </div>
          <div className='header-text'>
            <h1 className='title'>{t('app.title')}</h1>
            <p className='subtitle'>{t('app.subtitle')}</p>
            <div className='header-description'>
              <div className='description-item'>
                <span className='description-icon'>
                  {activeTab === 'chat' ? '🤖' : '🔗'}
                </span>
                <span className='description-text'>
                  {activeTab === 'chat' ? t('header.desc.chat') : t('header.desc.analysis')}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Settings Popup */}
      {settingsOpen && (
        <div className='settings-popup-overlay' onClick={() => setSettingsOpen(false)}>
          <div className='settings-popup' onClick={(e) => e.stopPropagation()}>
            <div className='settings-header'>
              <h3>{t('settings.title')}</h3>
              <button 
                className='settings-confirm'
                onClick={() => setSettingsOpen(false)}
              >
                {t('settings.confirm')}
              </button>
            </div>
            
            {/* Settings Tabs */}
            <div className='settings-tabs'>
              <button 
                className={`settings-tab ${settingsTab === 'chat' ? 'active' : ''}`}
                onClick={() => setSettingsTab('chat')}
              >
                {t('tab.chat')}
              </button>
              <button 
                className={`settings-tab ${settingsTab === 'analysis' ? 'active' : ''}`}
                onClick={() => setSettingsTab('analysis')}
              >
                {t('tab.analysis')}
              </button>
              <button 
                className={`settings-tab ${settingsTab === 'general' ? 'active' : ''}`}
                onClick={() => setSettingsTab('general')}
              >
                {t('tab.general')}
              </button>
            </div>
            
            <div className='settings-content'>
              {/* Chat Tab */}
              {settingsTab === 'chat' && (
                <div className='settings-tab-content'>
                  <div className='settings-section'>
                    <h4>{t('chat.mode.title')}</h4>
                    <div className='settings-options'>
                      <label className='settings-option'>
                        <input
                          type='radio'
                          name='chatMode'
                          value='single'
                          checked={chatMode === 'single'}
                          onChange={(e) => setChatMode(e.target.value as 'single' | 'multi')}
                        />
                        <span>{t('chat.mode.single')}</span>
                      </label>
                      <label className='settings-option'>
                        <input
                          type='radio'
                          name='chatMode'
                          value='multi'
                          checked={chatMode === 'multi'}
                          onChange={(e) => setChatMode(e.target.value as 'single' | 'multi')}
                        />
                        <span>{t('chat.mode.multi')}</span>
                      </label>
                    </div>
                  </div>
                  
                  <div className='settings-section'>
                    <h4>{t('chat.model.title')}</h4>
                    <select 
                      value={chatMode === 'single' ? model : modelFirst}
                      onChange={(e) => {
                        if (chatMode === 'single') {
                          setModel(e.target.value)
                        } else {
                          setModelFirst(e.target.value)
                        }
                      }}
                      className='settings-select'
                    >
                      <option value=''>{t('chat.model.select')}</option>
                      {availableModels.map((modelName) => (
                        <option key={modelName} value={modelName}>
                          {translateModelName(modelName)}
                        </option>
                      ))}
                    </select>
                  </div>

                  {chatMode === 'multi' && (
                    <>
                      <div className='settings-section'>
                        <h4>{t('chat.model.second')}</h4>
                        <select 
                          value={modelSecond}
                          onChange={(e) => setModelSecond(e.target.value)}
                          className='settings-select'
                        >
                          <option value=''>{t('chat.model.second.select')}</option>
                          {availableModels.map((modelName) => (
                            <option key={modelName} value={modelName}>
                              {translateModelName(modelName)}
                            </option>
                          ))}
                        </select>
                      </div>
                      
                      <div className='settings-section'>
                        <h4>{t('chat.model.judge')}</h4>
                        <select 
                          value={modelReferee}
                          onChange={(e) => setModelReferee(e.target.value)}
                          className='settings-select'
                        >
                          <option value=''>{t('chat.model.judge.select')}</option>
                          {availableModels.map((modelName) => (
                            <option key={modelName} value={modelName}>
                              {translateModelName(modelName)}
                            </option>
                          ))}
                        </select>
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Analysis Tab */}
              {settingsTab === 'analysis' && (
                <div className='settings-tab-content'>
                  <div className='settings-section'>
                    <h4>{t('analysis.mode.title')}</h4>
                    <div className='settings-options'>
                      <label className='settings-option'>
                        <input
                          type='radio'
                          name='analysisMode'
                          value='single'
                          checked={analysisMode === 'single'}
                          onChange={(e) => setAnalysisMode(e.target.value as 'single' | 'multi')}
                        />
                        <span>{t('chat.mode.single')}</span>
                      </label>
                      <label className='settings-option'>
                        <input
                          type='radio'
                          name='analysisMode'
                          value='multi'
                          checked={analysisMode === 'multi'}
                          onChange={(e) => setAnalysisMode(e.target.value as 'single' | 'multi')}
                        />
                        <span>{t('chat.mode.multi')}</span>
                      </label>
                    </div>
                  </div>
                  
                  <div className='settings-section'>
                    <h4>{t('analysis.model.title')}</h4>
                    <select 
                      value={analysisMode === 'single' ? model : modelFirst}
                      onChange={(e) => {
                        if (analysisMode === 'single') {
                          setModel(e.target.value)
                        } else {
                          setModelFirst(e.target.value)
                        }
                      }}
                      className='settings-select'
                    >
                      <option value=''>{t('analysis.model.select')}</option>
                      {availableModels.map((modelName) => (
                        <option key={modelName} value={modelName}>
                          {translateModelName(modelName)}
                        </option>
                      ))}
                    </select>
                  </div>

                  {analysisMode === 'multi' && (
                    <>
                      <div className='settings-section'>
                        <h4>{t('analysis.model.second')}</h4>
                        <select 
                          value={modelSecond}
                          onChange={(e) => setModelSecond(e.target.value)}
                          className='settings-select'
                        >
                          <option value=''>{t('analysis.model.second.select')}</option>
                          {availableModels.map((modelName) => (
                            <option key={modelName} value={modelName}>
                              {translateModelName(modelName)}
                            </option>
                          ))}
                        </select>
                      </div>
                      
                      <div className='settings-section'>
                        <h4>{t('analysis.model.judge')}</h4>
                        <select 
                          value={modelReferee}
                          onChange={(e) => setModelReferee(e.target.value)}
                          className='settings-select'
                        >
                          <option value=''>{t('analysis.model.judge.select')}</option>
                          {availableModels.map((modelName) => (
                            <option key={modelName} value={modelName}>
                              {translateModelName(modelName)}
                            </option>
                          ))}
                        </select>
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* General Tab */}
              {settingsTab === 'general' && (
                <div className='settings-tab-content'>
                  <div className='settings-section'>
                    <h4>{t('general.language')}</h4>
                    <div className='settings-options'>
                      <label className='settings-option'>
                        <input
                          type='radio'
                          name='language'
                          value='fa'
                          checked={language === 'fa'}
                          onChange={(e) => setLanguage(e.target.value as 'fa' | 'en' | 'ar')}
                        />
                        <span>{t('general.language.fa')}</span>
                      </label>
                      <label className='settings-option'>
                        <input
                          type='radio'
                          name='language'
                          value='en'
                          checked={language === 'en'}
                          onChange={(e) => setLanguage(e.target.value as 'fa' | 'en' | 'ar')}
                        />
                        <span>{t('general.language.en')}</span>
                      </label>
                      <label className='settings-option'>
                        <input
                          type='radio'
                          name='language'
                          value='ar'
                          checked={language === 'ar'}
                          onChange={(e) => setLanguage(e.target.value as 'fa' | 'en' | 'ar')}
                        />
                        <span>{t('general.language.ar')}</span>
                      </label>
                    </div>
                  </div>

                  <div className='settings-section'>
                    <h4>{t('general.domain')}</h4>
                    <select 
                      value={domain}
                      onChange={(e) => setDomain(e.target.value as 'general' | 'medical')}
                      className='settings-select'
                    >
                      <option value='general'>{t('general.domain.general')}</option>
                      <option value='medical'>{t('general.domain.medical')}</option>
                    </select>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className='tabs'>
        <button 
          className={`tab ${activeTab === 'analysis' ? 'active' : ''}`}
          onClick={() => setActiveTab('analysis')}
        >
          {t('tabs.analysis')}
        </button>
        <button 
          className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          {t('tabs.chat')}
        </button>
      </div>

      {error && <p className='error'>{error}</p>}

      {/* Analysis Tab */}
      {activeTab === 'analysis' && (
        <div className='analysis-tab'>
          <div className='main-content'>
            <div className='input-section'>
              <div className='input-header'>
                <h3>{t('analysis.input.title')}</h3>
                <div className='input-help'>
                  <small>{t('analysis.input.hint')}</small>
                </div>
                <div className='file-controls'>
                  <input 
                    type='file' 
                    id='file-input'
                    onChange={(e) => setFile(e.target.files?.[0] || null)} 
                    style={{ display: 'none' }}
                  />
                  <label htmlFor='file-input' className='btn btn-outline'>
                    {t('analysis.file.choose')}
                  </label>
                  
                  {/* Audio Upload */}
                  <input 
                    type='file' 
                    id='audio-input'
                    accept='audio/*'
                    onChange={(e) => handleAudioUpload(e.target.files?.[0])} 
                    style={{ display: 'none' }}
                    disabled={!!file}
                  />
                  <label htmlFor='audio-input' className={`btn btn-outline ${file ? 'disabled' : ''}`}>
                    {t('analysis.audio.upload')}
                  </label>
                  
                  {/* Audio Recording */}
                  <button 
                    className={`btn ${isRecording ? 'btn-danger' : 'btn-outline'} ${file ? 'disabled' : ''}`}
                    onClick={isRecording ? stopRecording : startRecording}
                    disabled={loading || !!file}
                  >
                    {isRecording ? t('analysis.record.stop') : t('analysis.record.start')}
                  </button>
                  
                  {file && (
                    <div className='file-selected-info'>
                      <span className='file-name'>📄 {file.name}</span>
                      <button className='btn btn-primary' onClick={onExtractFile} disabled={loading}>
                        {loading ? 'در حال استخراج...' : 'استخراج از فایل'}
                      </button>
                    </div>
                  )}
                </div>
              </div>
              <textarea 
                className='textarea' 
                value={text} 
                onChange={(e) => setText(e.target.value)} 
                placeholder={file ? t('analysis.file.selected.extract') : t('analysis.input.hint')} 
                disabled={!!file}
              />
              <div className='actions'>
                <button className='btn btn-primary' onClick={onExtract} disabled={loading || modelsLoading || !!file}>
                  {loading ? t('analysis.extract.loading') : t('analysis.extract.start')}
                </button>
                <button className='btn btn-secondary' onClick={onReport} disabled={loading || (!result && !multiResult) || !!file}>
                  {t('analysis.report.html')}
                </button>
                <button className='btn btn-outline' onClick={loadModels} disabled={modelsLoading || !!file} title={t('analysis.models.reload')}>
                  {modelsLoading ? t('analysis.models.loading') : t('analysis.models.reload')}
                </button>
                        {speechModels && (
                  <div className='speech-models-status' style={{marginTop: '8px', fontSize: '0.875rem', color: '#6b7280'}}>
                    {t('db.connection')}: {speechModels.hybrid_mode === 'available' ? '✅ Hybrid' : '⚠️ Whisper only'}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Analysis Results */}
          {(result || multiResult) && (
            <div className='analysis-results'>
              {/* Smart Interpretations */}
              {interpretations.length > 0 && (
                <div className='interpretations'>
                  <h3>تفسیر هوشمند</h3>
                  {interpretations.map((interp, idx) => (
                    <div key={idx} className={`interpretation interpretation-${interp.type} confidence-${interp.confidence}`}>
                      <div className='interpretation-icon'>
                        {interp.type === 'inference' && '🔍'}
                        {interp.type === 'warning' && '⚠'}
                        {interp.type === 'risk' && '🛡'}
                        {interp.type === 'conclusion' && '✓'}
                      </div>
                      <div className='interpretation-content'>
                        <p className='interpretation-text'>{interp.text}</p>
                        <small className='interpretation-confidence'>اطمینان: {
                          interp.confidence === 'high' ? 'بالا' : 
                          interp.confidence === 'medium' ? 'متوسط' : 'پایین'
                        }</small>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Single Model Results */}
              {analysisMode === 'single' && result && (
                <div className='grid'>
                  <div className='glass'>
                    <h3>موجودیت‌ها ({result.entities.length})</h3>
                    <ul className='list'>
                      {result.entities.map((e, idx) => (
                        <li key={idx} className={e.type.includes('INFERENCE') || e.type.includes('SUSPICIOUS') ? 'inference-entity' : ''}>
                          <b>{e.name}</b> 
                          <small>{e.type}</small>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className='glass'>
                    <h3>روابط ({result.relationships.length})</h3>
                    <ul className='list'>
                      {result.relationships.map((r, idx) => (
                        <li key={idx}>
                          <code>{r.source_entity_id}</code> — <b>{r.type}</b> → <code>{r.target_entity_id}</code>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Multi Model Results */}
              {analysisMode === 'multi' && multiResult && (
                <div className='multi-analysis'>
                  <div className='stats'>
                    <p>
                      Final Entities: {multiResult.final_analysis.entities.length} | 
                      Final Relationships: {multiResult.final_analysis.relationships.length} |
                      Agreement: {(multiResult.agreement_score! * 100).toFixed(1)}% |
                      Domain: {multiResult.domain}
                    </p>
                  </div>
                  
                  <div className='analysis-step'>
                    <h3>مدل اول: {multiResult.first_analysis.model_name}</h3>
                    <div className='analysis-grid'>
                      <div className='analysis-section'>
                        <h4>موجودیت‌ها ({multiResult.first_analysis.entities.length})</h4>
                        <ul className='compact-list'>
                          {multiResult.first_analysis.entities.map((e, idx) => (
                            <li key={idx}><b>{e.name}</b> <small>({e.type})</small></li>
                          ))}
                        </ul>
                      </div>
                      <div className='analysis-section'>
                        <h4>روابط ({multiResult.first_analysis.relationships.length})</h4>
                        <ul className='compact-list'>
                          {multiResult.first_analysis.relationships.map((r, idx) => (
                            <li key={idx}><small>{r.source_entity_id} → {r.target_entity_id} ({r.type})</small></li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>

                  <div className='analysis-step'>
                    <h3>مدل دوم: {multiResult.second_analysis.model_name}</h3>
                    <div className='analysis-grid'>
                      <div className='analysis-section'>
                        <h4>موجودیت‌ها ({multiResult.second_analysis.entities.length})</h4>
                        <ul className='compact-list'>
                          {multiResult.second_analysis.entities.map((e, idx) => (
                            <li key={idx}><b>{e.name}</b> <small>({e.type})</small></li>
                          ))}
                        </ul>
                      </div>
                      <div className='analysis-section'>
                        <h4>روابط ({multiResult.second_analysis.relationships.length})</h4>
                        <ul className='compact-list'>
                          {multiResult.second_analysis.relationships.map((r, idx) => (
                            <li key={idx}><small>{r.source_entity_id} → {r.target_entity_id} ({r.type})</small></li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>

                  <div className='analysis-step final-analysis'>
                    <h3>⚖ تصمیم نهایی داور: {multiResult.final_analysis.model_name}</h3>
                    <div className='analysis-grid'>
                      <div className='analysis-section'>
                        <h4>موجودیت‌های نهایی ({multiResult.final_analysis.entities.length})</h4>
                        <ul className='list'>
                          {multiResult.final_analysis.entities.map((e, idx) => (
                            <li key={idx} className={e.type.includes('INFERENCE') || e.type.includes('SUSPICIOUS') ? 'inference-entity' : ''}>
                              <b>{e.name}</b> <small>({e.type})</small>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className='analysis-section'>
                        <h4>روابط نهایی ({multiResult.final_analysis.relationships.length})</h4>
                        <ul className='list'>
                          {multiResult.final_analysis.relationships.map((r, idx) => (
                            <li key={idx}><code>{r.source_entity_id}</code> — <b>{r.type}</b> → <code>{r.target_entity_id}</code></li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* Conflicts */}
                  {(multiResult.conflicting_entities.length > 0 || multiResult.conflicting_relationships.length > 0) && (
                    <div className='conflicts'>
                      <h3>⚠ تعارضات شناسایی شده</h3>
                      {multiResult.conflicting_entities.length > 0 && (
                        <div>
                          <h4>موجودیت‌های متعارض:</h4>
                          <ul className='conflict-list'>
                            {multiResult.conflicting_entities.map((item, idx) => (
                              <li key={idx}>{item}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {multiResult.conflicting_relationships.length > 0 && (
                        <div>
                          <h4>روابط متعارض:</h4>
                          <ul className='conflict-list'>
                            {multiResult.conflicting_relationships.map((item, idx) => (
                              <li key={idx}>{item}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Chat Tab */}
      {activeTab === 'chat' && (
        <div className='chat-tab'>

          
           <div className='chat-section'>
            <div className='chat-container'>
              <div className='chat-messages'>
                {chatMessages.length === 0 ? (
                  <div className='chat-welcome'>
                    <p>{t('chat.welcome.1')}</p>
                    <p>{t('chat.welcome.2')}</p>
                    <p>{t('chat.welcome.3')}</p>
                  </div>
                ) : (
                  chatMessages.map((msg) => (
                    <div key={msg.id} className={`chat-message ${msg.type}`}>
                      <div className='message-content'>
                        {msg.isAudio && msg.audioUrl && (
                          <audio controls className='audio-player'>
                            <source src={msg.audioUrl} type='audio/wav' />
                          </audio>
                        )}
                        {msg.type === 'assistant' ? (
                          <div 
                            dangerouslySetInnerHTML={{ 
                              __html: (typingMessageId === msg.id ? typingText : msg.content)
                                .trim()  // Remove leading/trailing whitespace
                                .replace(/\n/g, '<br />')
                            }} 
                          />
                        ) : (
                          <p>
                            {typingMessageId === msg.id ? typingText : msg.content}
                            {typingMessageId === msg.id && (
                              <span className="typing-cursor">|</span>
                            )}
                          </p>
                        )}
                        
                        {/* Display chart if available */}
                        {msg.chart && msg.type === 'assistant' && (
                          <div className='chat-chart'>
                            <ChartComponent chartData={msg.chart} />
                          </div>
                        )}
                        
                        {/* Display analysis results if available */}
                        {msg.analysis && msg.type === 'assistant' && (
                          <div className='chat-analysis'>
                            <h4>⚡ نتایج تحلیل {msg.analysisMode === 'multi' ? '(داوری چندمدله)' : ''}</h4>
                            
                            {msg.analysisMode === 'single' && 'entities' in msg.analysis && (
                              <div className='chat-analysis-single'>
                                <div className='analysis-summary'>
                                  <span>موجودیت‌ها: {msg.analysis.entities.length}</span>
                                  <span>روابط: {msg.analysis.relationships.length}</span>
                                </div>
                                <div className='analysis-details'>
                                  {msg.analysis.entities.length > 0 && (
                                    <div>
                                      <strong>موجودیت‌ها:</strong>
                                      <ul className='compact-list'>
                                        {msg.analysis.entities.slice(0, 5).map((e, idx) => (
                                          <li key={idx}><b>{e.name}</b> <small>({e.type})</small></li>
                                        ))}
                                        {msg.analysis.entities.length > 5 && <li><small>... و {msg.analysis.entities.length - 5} مورد دیگر</small></li>}
                                      </ul>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                            
                            {msg.analysisMode === 'multi' && 'final_analysis' in msg.analysis && (
                              <div className='chat-analysis-multi'>
                                <div className='analysis-summary'>
                                  <span>موجودیت‌های نهایی: {msg.analysis.final_analysis.entities.length}</span>
                                  <span>روابط نهایی: {msg.analysis.final_analysis.relationships.length}</span>
                                  <span>توافق: {((msg.analysis.agreement_score || 0) * 100).toFixed(1)}%</span>
                                </div>
                                <div className='analysis-details'>
                                  {msg.analysis.final_analysis.entities.length > 0 && (
                                    <div>
                                      <strong>⚖ نتیجه نهایی داور:</strong>
                                      <ul className='compact-list'>
                                        {msg.analysis.final_analysis.entities.slice(0, 5).map((e, idx) => (
                                          <li key={idx} className={e.type.includes('INFERENCE') || e.type.includes('SUSPICIOUS') ? 'inference-entity' : ''}>
                                            <b>{e.name}</b> <small>({e.type})</small>
                                          </li>
                                        ))}
                                        {msg.analysis.final_analysis.entities.length > 5 && <li><small>... و {msg.analysis.final_analysis.entities.length - 5} مورد دیگر</small></li>}
                                      </ul>
                                    </div>
                                  )}
                                  {(msg.analysis.conflicting_entities.length > 0 || msg.analysis.conflicting_relationships.length > 0) && (
                                    <div className='conflicts-summary'>
                                      <strong>⚠ تعارضات:</strong>
                                      {msg.analysis.conflicting_entities.length > 0 && <span>{msg.analysis.conflicting_entities.length} موجودیت متعارض</span>}
                                      {msg.analysis.conflicting_relationships.length > 0 && <span>{msg.analysis.conflicting_relationships.length} رابطه متعارض</span>}
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                        
                        <small className='message-time'>
                          {msg.timestamp.toLocaleTimeString(locale === 'en' ? 'en-US' : locale === 'ar' ? 'ar-EG' : 'fa-IR')}
                        </small>
                        <div className='message-actions'>
                          <button
                            className={`copy-btn ${copiedMessageId === msg.id ? 'copied' : ''}`}
                            onClick={() => copyMessage(msg.content, msg.id)}
                            title={t('chat.copy')}
                          >
                            {copiedMessageId === msg.id ? '✓' : '⧉'}
                          </button>
                          <button
                            className='resend-btn'
                            onClick={() => resendMessage(msg.content)}
                            title={t('chat.resend')}
                          >
                            ↻
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
                {chatLoading && (
                  <div className='chat-message assistant'>
                    <div className='message-content'>
                      <p>{t('chat.processing')}</p>
                    </div>
                  </div>
                )}
                {/* Invisible element for auto-scroll */}
                <div ref={chatMessagesEndRef} />
              </div>
              
              <div className='chat-input-area'>
                {/* Image Preview Area */}
                {imagePreviewUrls.length > 0 && (
                  <div className='image-preview-container'>
                    <div className='image-preview-grid'>
                      {imagePreviewUrls.map((url, index) => (
                        <div key={index} className='image-preview-item'>
                          <img 
                            src={url} 
                            alt={`Preview ${index + 1}`}
                            className='image-preview'
                          />
                          <button
                            className='image-remove-btn'
                            onClick={() => removeImage(index)}
                            title='حذف تصویر'
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className='chat-input-container'>
                  <textarea
                    ref={setChatInputRef}
                    className='chat-input'
                    value={chatInput}
                    onChange={(e) => {
                      setChatInput(e.target.value)
                      if (chatInputRef) {
                        autoResizeTextarea(chatInputRef)
                      }
                    }}
                    placeholder={t('chat.placeholder')}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        sendChatMessage(chatInput)
                      }
                    }}
                    disabled={chatLoading}
                    rows={1}
                  />
                  <button
                    className='btn btn-primary chat-send-btn'
                    onClick={() => sendChatMessage(chatInput)}
                    disabled={chatLoading || (!chatInput.trim() && uploadedImages.length === 0)}
                    title={t('chat.send')}
                  >
                    ➤
                  </button>
                </div>
                
                {/* Chat Action Buttons */}
                <div className='chat-action-buttons'>
                  <button
                    className={`btn ${isRecording ? 'btn-secondary' : 'btn-outline'} chat-voice-btn`}
                    onClick={isRecording ? stopRecording : startRecording}
                    disabled={chatLoading}
                    title={isRecording ? t('chat.record.stop') : t('chat.record.start')}
                  >
                    {isRecording ? t('chat.record.stop') : t('chat.record.start')}
                  </button>
                  
                  {/* Audio Upload for Chat */}
                  <input 
                    type='file' 
                    id='chat-audio-input'
                    accept='audio/*'
                    onChange={(e) => handleChatAudioUpload(e.target.files?.[0])} 
                    style={{ display: 'none' }}
                    disabled={chatLoading}
                  />
                  <label 
                    htmlFor='chat-audio-input' 
                    className={`btn btn-outline chat-audio-upload-btn ${chatLoading ? 'disabled' : ''}`}
                    title={t('chat.audio.tooltip')}
                  >
                    {t('chat.audio.upload')}
                  </label>
                  
                  {/* Image Upload for Chat */}
                  <input 
                    type='file' 
                    id='chat-image-input'
                    accept='image/*'
                    multiple
                    onChange={handleImageUpload} 
                    style={{ display: 'none' }}
                    disabled={chatLoading}
                  />
                  <label 
                    htmlFor='chat-image-input' 
                    className={`btn btn-outline chat-image-upload-btn ${chatLoading ? 'disabled' : ''}`}
                    title='آپلود تصویر'
                  >
                    📷 تصویر
                  </label>
                  {speechModels && (
                    <div className='chat-speech-status' style={{fontSize: '0.75rem', color: '#6b7280', marginTop: '4px'}}>
                      {speechModels.hybrid_mode === 'available' ? '🎯 هیبرید فعال' : '⚠️ فقط Whisper'}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Database Popup */}
      <div className={darkMode ? 'dark-mode' : ''}>
        <DatabasePopup 
          isOpen={databasePopupOpen}
          onClose={() => setDatabasePopupOpen(false)}
          esInfo={esInfo}
        />
      </div>

      {/* Auth Panel */}
      <AuthPanel isOpen={authOpen} onClose={() => setAuthOpen(false)} />
    </div>
  )
}

function AuthButton({ onOpen }: { onOpen: () => void }) {
  const { user } = useAuth()
  const { t } = useI18n()
  return (
    <button className='settings-btn' onClick={onOpen} title={user ? t('auth.title.loggedIn') : t('auth.title.loggedOut')}>
      {user ? '👤' : '🔑'}
    </button>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <InnerApp />
    </AuthProvider>
  )
}
