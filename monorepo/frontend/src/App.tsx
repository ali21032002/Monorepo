import { useMemo, useState, useEffect, useRef } from 'react'
import './App.css'
import ChartComponent from './components/ChartComponent'

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
  
  // Typing animation states
  const [typingMessageId, setTypingMessageId] = useState<string | null>(null)
  const [typingText, setTypingText] = useState('')

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

  // Typing animation function
  const typeText = (text: string, messageId: string, baseSpeed: number = 30) => {
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
      // Smart message history management
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
        
        // For longer conversations, use a smart selection strategy:
        // 1. Always include the first 2 messages (context establishment)
        // 2. Include the last 8 messages (recent context)
        // 3. Try to include important messages (containing names, key info)
        
        const importantMessages = []
        
        // Add first 3 messages for context
        if (previousMessages.length >= 3) {
          importantMessages.push(...previousMessages.slice(0, 3))
        }
        
        // Add last 10 messages for recent context
        const recentMessages = previousMessages.slice(-10)
        importantMessages.push(...recentMessages)
        
        // Try to include important messages from the middle
        if (previousMessages.length > 13) {
          const middleMessages = previousMessages.slice(3, -10)
          const importantKeywords = ['نام', 'اسم', 'کیه', 'کیست', 'کجا', 'چطور', 'چرا', 'چگونه', 'مشکل', 'خطا', 'اشتباه', 'کمک', 'راهنمایی', 'تحلیل', 'بررسی', 'نمودار', 'توضیح', 'پیشنهاد', 'نتیجه']
          
          for (const msg of middleMessages) {
            const content = msg.content.toLowerCase()
            const hasImportantKeyword = importantKeywords.some(keyword => content.includes(keyword))
            const isLongMessage = msg.content.length > 50
            const hasQuestion = content.includes('؟') || content.includes('?')
            const hasName = /نام\s+من|اسم\s+من|من\s+\w+\s+هستم/.test(content)
            
            if (hasImportantKeyword || isLongMessage || hasQuestion || hasName) {
              importantMessages.push(msg)
            }
          }
        }
        
        // Remove duplicates while preserving order
        const uniqueMessages = []
        const seen = new Set()
        
        for (const msg of importantMessages) {
          const key = `${msg.type}-${msg.content.substring(0, 50)}`
          if (!seen.has(key)) {
            seen.add(key)
            uniqueMessages.push({
              role: msg.type === 'user' ? 'user' : 'assistant',
              content: msg.content
            })
          }
        }
        
        // Limit to 18 messages to allow more context for better continuity
        const finalMessages = uniqueMessages.slice(-18)
        
        // Log selection strategy
        console.log(`📝 Enhanced message selection: ${previousMessages.length} total → ${finalMessages.length} selected`)
        console.log(`📝 Selection strategy: First 3 + Last 10 + Important middle messages (enhanced criteria)`)
        
        return finalMessages
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
      
      // Convert audio to text using speech-to-text service
      const formData = new FormData()
      formData.append('audio_file', audioFile, 'uploaded_audio.wav')
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

      // Convert audio to text using speech-to-text service
      const formData = new FormData()
      formData.append('audio', audioFile)
      formData.append('language', language)

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
                <div className='input-help'>
                  <small>💡 می‌توانید متن را مستقیماً وارد کنید، فایل آپلود کنید، یا صدا ضبط/آپلود کنید</small>
                </div>
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
                    🎵 آپلود صدا
                  </label>
                  
                  {/* Audio Recording */}
                  <button 
                    className={`btn ${isRecording ? 'btn-danger' : 'btn-outline'} ${file ? 'disabled' : ''}`}
                    onClick={isRecording ? stopRecording : startRecording}
                    disabled={loading || !!file}
                  >
                    {isRecording ? '⏹ توقف ضبط' : '🎤 ضبط صدا'}
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
                placeholder={file ? 'فایل انتخاب شده است. ابتدا دکمه "استخراج از فایل" را بزنید...' : 'متن خود را اینجا وارد کنید، فایل انتخاب کنید، یا صدا ضبط/آپلود کنید...'} 
                disabled={!!file}
              />
              <div className='actions'>
                <button className='btn btn-primary' onClick={onExtract} disabled={loading || modelsLoading || !!file}>
                  {loading ? 'در حال استخراج...' : 'شروع تحلیل'}
                </button>
                <button className='btn btn-secondary' onClick={onReport} disabled={loading || (!result && !multiResult) || !!file}>
                  گزارش HTML
                </button>
                <button className='btn btn-outline' onClick={loadModels} disabled={modelsLoading || !!file} title='بارگیری مجدد مدل‌ها'>
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
                    <p>می‌توانم در تحلیل متون تخصصی به شما کمک کنم و نمودارهای مختلف بکشم.</p>
                    <p>💡 مثال: "یک نمودار میل‌های از فروش محصولات مختلف بکش" یا "نمودار دایره‌ای از توزیع جمعیت نشان بده"</p>
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
                        <p>
                          {typingMessageId === msg.id ? typingText : msg.content}
                          {typingMessageId === msg.id && (
                            <span className="typing-cursor">|</span>
                          )}
                        </p>
                        
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
                </div>
                
                {/* Chat Action Buttons */}
                <div className='chat-action-buttons'>
                  <button
                    className={`btn ${isRecording ? 'btn-secondary' : 'btn-outline'} chat-voice-btn`}
                    onClick={isRecording ? stopRecording : startRecording}
                    disabled={chatLoading}
                    title={isRecording ? 'توقف ضبط' : 'شروع ضبط صدا'}
                  >
                    {isRecording ? '⏹ توقف ضبط' : '🎙 ضبط صدا'}
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
                    title='آپلود فایل صوتی'
                  >
                    🎵 آپلود صدا
                  </label>
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
