import { useMemo, useState, useEffect, useRef } from 'react'
import './App.css'

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
}

interface ChatResponse {
  message: string
  analysis?: ExtractionResponse | MultiModelResponse | null
  analysisMode?: 'single' | 'multi'
}

function App() {
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

  // Tab navigation
  const [activeTab, setActiveTab] = useState<'analysis' | 'chat'>('analysis')
  
  // Common settings
  const [language, setLanguage] = useState<'fa' | 'en'>('fa')
  const [domain, setDomain] = useState<'general' | 'legal' | 'medical' | 'police'>('police')
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
  
  // Auto-resize textarea function
  const autoResizeTextarea = (textarea: HTMLTextAreaElement) => {
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 128) + 'px' // Max height of 8rem (128px)
  }
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null)
  const [chatLoading, setChatLoading] = useState(false)
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null)
  const [chatMode, setChatMode] = useState<'single' | 'multi'>('single')
  const [darkMode, setDarkMode] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [settingsTab, setSettingsTab] = useState<'chat' | 'analysis' | 'general'>('chat')

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
  
  // Ref for auto-scrolling chat messages
  const chatMessagesEndRef = useRef<HTMLDivElement>(null)
  
  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    chatMessagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
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
      
      // Police domain specific interpretations
      if (domain === 'police' && language === 'fa') {
        if (suspiciousBehaviors.length > 0 || criminalInferences.length > 0) {
          interpretations.push({
            text: `${suspectName} احتمالاً دزد است و در اینجا دزدی کرده است!`,
            confidence: 'high',
            type: 'inference',
            entities: [suspectName]
          })
        }
        
        if (suspiciousBehaviors.length > 0) {
          interpretations.push({
            text: `رفتارهای مشکوک شناسایی شده: ${suspiciousBehaviors.map(b => b.name).join('، ')}`,
            confidence: 'high',
            type: 'warning',
            entities: suspiciousBehaviors.map(b => b.name)
          })
        }
      }
      
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
      const resp = await fetchWithTimeout('/api/models')
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`)
      const data = await resp.json()
      
      if (data.models && data.models.length > 0) {
        setAvailableModels(data.models)
        
        if (!model && data.models.length > 0) setModel(data.models[0])
        if (!modelFirst && data.models.length > 0) setModelFirst(data.models[0])
        if (!modelSecond && data.models.length > 1) setModelSecond(data.models[1])
        if (!modelReferee && data.models.length > 2) setModelReferee(data.models[2])
        else if (!modelReferee && data.models.length > 0) setModelReferee(data.models[0])
      }
    } catch (e: any) {
      console.error('Failed to load models:', e)
      const fallbackModels = ['gemma3:4b', 'qwen2.5.2:7b', 'llava:7b']
      setAvailableModels(fallbackModels)
      setModel(fallbackModels[0])
      setModelFirst(fallbackModels[0])
      setModelSecond(fallbackModels[1])
      setModelReferee(fallbackModels[2])
    } finally {
      setModelsLoading(false)
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

  // Chat functions
  const sendChatMessage = async (message: string, isAudio = false, audioUrl?: string) => {
    if (!message.trim() && !isAudio) return

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
      const resp = await fetchWithTimeout('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          language,
          domain,
          model: model || modelReferee || 'gemma3:4b',
          analysisMode: chatMode,
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
        analysisMode: data.analysisMode
      }

      setChatMessages(prev => [...prev, assistantMessage])
      
      // Scroll to bottom after adding assistant message
      setTimeout(() => scrollToBottom(), 100)
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

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      const chunks: BlobPart[] = []

      recorder.ondataavailable = (e) => chunks.push(e.data)
      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' })
        const audioUrl = URL.createObjectURL(blob)
        
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
          // Send audio to speech-to-text service
          const formData = new FormData()
          formData.append('audio_file', blob, 'recording.wav')
          formData.append('language', language)
          
          const response = await fetchWithTimeout('http://localhost:8001/transcribe-chat', {
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
      <header className='hero'>
        <div className='header-content'>
          <div className='header-controls'>
            <div 
              className={`theme-toggle ${darkMode ? 'dark' : 'light'}`}
              onClick={() => setDarkMode(!darkMode)}
              title={darkMode ? 'تغییر به تم روشن' : 'تغییر به تم تاریک'}
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
              title='تنظیمات چت'
            >
              ⚙️
            </button>
          </div>
          <div className='header-text'>
            <h1 className='title'>مرکز مدیریت و تحلیل داده فراجا</h1>
            <p className='subtitle'>سیستم هوشمند تحلیل متن با قابلیت داوری توسط چند مدل مختلف</p>
            <div className='header-description'>
              <div className='description-item'>
                <span className='description-icon'>
                  {activeTab === 'chat' ? '🤖' : '🔗'}
                </span>
                <span className='description-text'>
                  {activeTab === 'chat' ? 'دستیار تعاملی هوشمند' : 'استخراج روابط چند گانه از متن'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

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
            chatMode === 'multi' ? 'داوری چندمدله' : 'تک مدل'
          ) : (
            analysisMode === 'multi' ? 'داوری چندمدله' : 'تک مدل'
          )}
        </div>
      </div>

      {/* Settings Popup */}
      {settingsOpen && (
        <div className='settings-popup-overlay' onClick={() => setSettingsOpen(false)}>
          <div className='settings-popup' onClick={(e) => e.stopPropagation()}>
            <div className='settings-header'>
              <h3>⚙️ تنظیمات سیستم</h3>
              <button 
                className='settings-confirm'
                onClick={() => setSettingsOpen(false)}
              >
                ✓ تایید
              </button>
            </div>
            
            {/* Settings Tabs */}
            <div className='settings-tabs'>
              <button 
                className={`settings-tab ${settingsTab === 'chat' ? 'active' : ''}`}
                onClick={() => setSettingsTab('chat')}
              >
                💬 چت
              </button>
              <button 
                className={`settings-tab ${settingsTab === 'analysis' ? 'active' : ''}`}
                onClick={() => setSettingsTab('analysis')}
              >
                📊 تحلیل
              </button>
              <button 
                className={`settings-tab ${settingsTab === 'general' ? 'active' : ''}`}
                onClick={() => setSettingsTab('general')}
              >
                ⚙️ عمومی
              </button>
            </div>
            
            <div className='settings-content'>
              {/* Chat Tab */}
              {settingsTab === 'chat' && (
                <div className='settings-tab-content'>
                  <div className='settings-section'>
                    <h4>🎯 حالت چت</h4>
                    <div className='settings-options'>
                      <label className='settings-option'>
                        <input
                          type='radio'
                          name='chatMode'
                          value='single'
                          checked={chatMode === 'single'}
                          onChange={(e) => setChatMode(e.target.value as 'single' | 'multi')}
                        />
                        <span>تک مدل</span>
                      </label>
                      <label className='settings-option'>
                        <input
                          type='radio'
                          name='chatMode'
                          value='multi'
                          checked={chatMode === 'multi'}
                          onChange={(e) => setChatMode(e.target.value as 'single' | 'multi')}
                        />
                        <span>چند مدل</span>
                      </label>
                    </div>
                  </div>
                  
                  <div className='settings-section'>
                    <h4>🤖 مدل چت</h4>
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
                      <option value=''>انتخاب مدل...</option>
                      {availableModels.map((modelName) => (
                        <option key={modelName} value={modelName}>
                          {modelName}
                        </option>
                      ))}
                    </select>
                  </div>

                  {chatMode === 'multi' && (
                    <>
                      <div className='settings-section'>
                        <h4>🤖 مدل دوم چت</h4>
                        <select 
                          value={modelSecond}
                          onChange={(e) => setModelSecond(e.target.value)}
                          className='settings-select'
                        >
                          <option value=''>انتخاب مدل دوم...</option>
                          {availableModels.map((modelName) => (
                            <option key={modelName} value={modelName}>
                              {modelName}
                            </option>
                          ))}
                        </select>
                      </div>
                      
                      <div className='settings-section'>
                        <h4>⚖️ مدل داور چت</h4>
                        <select 
                          value={modelReferee}
                          onChange={(e) => setModelReferee(e.target.value)}
                          className='settings-select'
                        >
                          <option value=''>انتخاب مدل داور...</option>
                          {availableModels.map((modelName) => (
                            <option key={modelName} value={modelName}>
                              {modelName}
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
                    <h4>📊 حالت تحلیل</h4>
                    <div className='settings-options'>
                      <label className='settings-option'>
                        <input
                          type='radio'
                          name='analysisMode'
                          value='single'
                          checked={analysisMode === 'single'}
                          onChange={(e) => setAnalysisMode(e.target.value as 'single' | 'multi')}
                        />
                        <span>تک مدل</span>
                      </label>
                      <label className='settings-option'>
                        <input
                          type='radio'
                          name='analysisMode'
                          value='multi'
                          checked={analysisMode === 'multi'}
                          onChange={(e) => setAnalysisMode(e.target.value as 'single' | 'multi')}
                        />
                        <span>چند مدل</span>
                      </label>
                    </div>
                  </div>
                  
                  <div className='settings-section'>
                    <h4>🤖 مدل تحلیل</h4>
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
                      <option value=''>انتخاب مدل...</option>
                      {availableModels.map((modelName) => (
                        <option key={modelName} value={modelName}>
                          {modelName}
                        </option>
                      ))}
                    </select>
                  </div>

                  {analysisMode === 'multi' && (
                    <>
                      <div className='settings-section'>
                        <h4>🤖 مدل دوم تحلیل</h4>
                        <select 
                          value={modelSecond}
                          onChange={(e) => setModelSecond(e.target.value)}
                          className='settings-select'
                        >
                          <option value=''>انتخاب مدل دوم...</option>
                          {availableModels.map((modelName) => (
                            <option key={modelName} value={modelName}>
                              {modelName}
                            </option>
                          ))}
                        </select>
                      </div>
                      
                      <div className='settings-section'>
                        <h4>⚖️ مدل داور تحلیل</h4>
                        <select 
                          value={modelReferee}
                          onChange={(e) => setModelReferee(e.target.value)}
                          className='settings-select'
                        >
                          <option value=''>انتخاب مدل داور...</option>
                          {availableModels.map((modelName) => (
                            <option key={modelName} value={modelName}>
                              {modelName}
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
                    <h4>🌐 زبان</h4>
                    <div className='settings-options'>
                      <label className='settings-option'>
                        <input
                          type='radio'
                          name='language'
                          value='fa'
                          checked={language === 'fa'}
                          onChange={(e) => setLanguage(e.target.value as 'fa' | 'en')}
                        />
                        <span>فارسی</span>
                      </label>
                      <label className='settings-option'>
                        <input
                          type='radio'
                          name='language'
                          value='en'
                          checked={language === 'en'}
                          onChange={(e) => setLanguage(e.target.value as 'fa' | 'en')}
                        />
                        <span>English</span>
                      </label>
                    </div>
                  </div>

                  <div className='settings-section'>
                    <h4>🎯 حوزه تخصصی</h4>
                    <select 
                      value={domain}
                      onChange={(e) => setDomain(e.target.value as 'general' | 'legal' | 'medical' | 'police')}
                      className='settings-select'
                    >
                      <option value='general'>عمومی</option>
                      <option value='legal'>حقوقی</option>
                      <option value='medical'>پزشکی</option>
                      <option value='police'>پلیسی</option>
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
          تحلیل متن
        </button>
        <button 
          className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          دستیار هوشمند
        </button>
      </div>

      {error && <p className='error'>{error}</p>}

      {/* Analysis Tab */}
      {activeTab === 'analysis' && (
        <div className='analysis-tab'>
          <div className='main-content'>
            <div className='input-section'>
              <div className='input-header'>
                <h3>متن ورودی</h3>
                <div className='file-controls'>
                  <input 
                    type='file' 
                    id='file-input'
                    onChange={(e) => setFile(e.target.files?.[0] || null)} 
                    style={{ display: 'none' }}
                  />
                  <label htmlFor='file-input' className='btn btn-outline'>
                    انتخاب فایل
                  </label>
                  {file && (
                    <button className='btn btn-outline' onClick={onExtractFile} disabled={loading}>
                      استخراج از فایل
                    </button>
                  )}
                </div>
              </div>
              <textarea 
                className='textarea' 
                value={text} 
                onChange={(e) => setText(e.target.value)} 
                placeholder='متن خود را اینجا وارد کنید یا فایل انتخاب کنید...' 
              />
              <div className='actions'>
                <button className='btn btn-primary' onClick={onExtract} disabled={loading || modelsLoading}>
                  {loading ? 'در حال استخراج...' : 'شروع تحلیل'}
                </button>
                <button className='btn btn-secondary' onClick={onReport} disabled={loading || (!result && !multiResult)}>
                  گزارش HTML
                </button>
                <button className='btn btn-outline' onClick={loadModels} disabled={modelsLoading} title='بارگیری مجدد مدل‌ها'>
                  {modelsLoading ? 'بارگیری...' : 'بارگیری مدل‌ها'}
                </button>
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
                    <p>👋 سلام! من دستیار هوشمند {
                      domain === 'police' ? 'امنیتی و پلیسی' :
                      domain === 'legal' ? 'حقوقی' :
                      domain === 'medical' ? 'پزشکی' : 'عمومی'
                    } هستم.</p>
                    <p>می‌توانم در تحلیل متون تخصصی به شما کمک کنم. سوال خود را بپرسید.</p>
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
                        <p>{msg.content}</p>
                        
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
                          {msg.timestamp.toLocaleTimeString('fa-IR')}
                        </small>
                        <div className='message-actions'>
                          <button
                            className={`copy-btn ${copiedMessageId === msg.id ? 'copied' : ''}`}
                            onClick={() => copyMessage(msg.content, msg.id)}
                            title='کپی پیام'
                          >
                            {copiedMessageId === msg.id ? '✓' : '⧉'}
                          </button>
                          <button
                            className='resend-btn'
                            onClick={() => resendMessage(msg.content)}
                            title='ارسال مجدد'
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
                      <p>در حال پردازش...</p>
                    </div>
                  </div>
                )}
                {/* Invisible element for auto-scroll */}
                <div ref={chatMessagesEndRef} />
              </div>
              
              <div className='chat-input-area'>
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
                    placeholder='پیام خود را بنویسید... (Shift+Enter برای خط جدید)'
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
                    disabled={chatLoading || (!chatInput.trim())}
                    title='ارسال پیام'
                  >
                    ➤
                  </button>
                  <button
                    className={`btn ${isRecording ? 'btn-secondary' : 'btn-outline'} chat-voice-btn`}
                    onClick={isRecording ? stopRecording : startRecording}
                    disabled={chatLoading}
                    title={isRecording ? 'توقف ضبط' : 'شروع ضبط صدا'}
                  >
                    {isRecording ? '⏹ توقف' : '🎙 ضبط'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
