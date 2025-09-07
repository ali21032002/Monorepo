import React, { useMemo, useState, useEffect } from 'react'
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

// Interpretation types
interface Interpretation {
  text: string
  confidence: 'high' | 'medium' | 'low'
  type: 'inference' | 'risk' | 'warning' | 'conclusion'
  entities: string[]
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
  const [text, setText] = useState('شخصی با هویت معلوم ؛ با نام که خودش گفته به اسم حسن جودت شندی وارد یک مغازه طلافروشی شده ، مقداری طلا را خریداری کرده ولی بدون پرداخت پول و بدون دریافت فاکتور از مغازه خارج شده است')
  const [language, setLanguage] = useState<'fa' | 'en'>('fa')
  const [domain, setDomain] = useState<'general' | 'legal' | 'medical' | 'police'>('police')
  const [analysisMode, setAnalysisMode] = useState<'single' | 'multi'>('single')
  
  // Available models from Ollama
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [modelsLoading, setModelsLoading] = useState(true)
  
  // Single model state
  const [model, setModel] = useState('')
  const [result, setResult] = useState<ExtractionResponse | null>(null)
  
  // Multi model state  
  const [modelFirst, setModelFirst] = useState('')
  const [modelSecond, setModelSecond] = useState('')
  const [modelReferee, setModelReferee] = useState('')
  const [multiResult, setMultiResult] = useState<MultiModelResponse | null>(null)
  
  // Common state
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const entityCount = useMemo(() => {
    if (analysisMode === 'single') return result?.entities?.length ?? 0
    return multiResult?.final_analysis?.entities?.length ?? 0
  }, [result, multiResult, analysisMode])
  
  const relCount = useMemo(() => {
    if (analysisMode === 'single') return result?.relationships?.length ?? 0
    return multiResult?.final_analysis?.relationships?.length ?? 0
  }, [result, multiResult, analysisMode])

  // Generate smart interpretations
  const generateInterpretations = (entities: Entity[], relationships: Relationship[], domain: string, language: string): Interpretation[] => {
    const interpretations: Interpretation[] = []
    
    console.log('🧠 Generating interpretations for:', { entities, relationships, domain, language })
    
    // Find inference entities (more flexible matching)
    const inferences = entities.filter(e => 
      e.type.includes('INFERENCE') || 
      e.type.includes('SUSPICIOUS') || 
      e.type.includes('RISK') || 
      e.type.includes('THREAT')
    )
    
    // Find suspects and crimes (flexible matching)
    const suspects = entities.filter(e => 
      e.type === 'SUSPECT' || 
      e.type === 'PERSON' || 
      (e.name && (e.name.includes('حسن') || e.name.includes('علی') || e.name.includes('احمد')))
    )
    
    const crimes = entities.filter(e => 
      e.type === 'CRIME' || 
      (e.name && (e.name.includes('سرقت') || e.name.includes('دزدی')))
    )
    
    const suspiciousBehaviors = entities.filter(e => 
      e.type === 'SUSPICIOUS_BEHAVIOR' || 
      (e.name && (e.name.includes('بدون پرداخت') || e.name.includes('بدون فاکتور')))
    )
    
    const criminalInferences = entities.filter(e => 
      e.type === 'CRIMINAL_INFERENCE' || 
      (e.name && (e.name.includes('احتمال') || e.name.includes('دزد')))
    )
    
    console.log('🔍 Found entities:', { suspects, crimes, suspiciousBehaviors, criminalInferences, inferences })
    
    // Always try to generate some interpretation, even for general domains
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
        
        if (criminalInferences.length > 0) {
          interpretations.push({
            text: `بر اساس شواهد موجود، ${suspectName} مرتکب جرم شده است.`,
            confidence: 'medium',
            type: 'conclusion',
            entities: [suspectName]
          })
        }
        
        if (suspiciousBehaviors.length > 0) {
          interpretations.push({
            text: `رفتار مشکوک شناسایی شده: ${suspiciousBehaviors.map(b => b.name).join('، ')}`,
            confidence: 'high',
            type: 'warning',
            entities: suspiciousBehaviors.map(b => b.name)
          })
        }
      }
      
      // General interpretations for any domain
      if (interpretations.length === 0) {
        // Look for any suspicious patterns in entity names
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
        
        // Always provide a basic interpretation if we have a person
        if (interpretations.length === 0) {
          interpretations.push({
            text: `شخص ${suspectName} در این متن نقش کلیدی دارد و نیاز به بررسی بیشتر است.`,
            confidence: 'low',
            type: 'inference',
            entities: [suspectName]
          })
        }
      }
      
      // Threat level assessment
      const threatLevels = entities.filter(e => e.type === 'THREAT_LEVEL')
      if (threatLevels.length > 0) {
        interpretations.push({
          text: `سطح تهدید: ${threatLevels[0].name}`,
          confidence: 'medium',
          type: 'risk',
          entities: [threatLevels[0].name]
        })
      }
    }
    
    if (domain === 'legal' && language === 'fa') {
      // Legal domain interpretations
      const legalInferences = entities.filter(e => e.type === 'LEGAL_INFERENCE')
      const violationRisks = entities.filter(e => e.type === 'VIOLATION_RISK')
      
      if (legalInferences.length > 0) {
        interpretations.push({
          text: `تحلیل حقوقی: ${legalInferences.map(i => i.name).join('، ')}`,
          confidence: 'medium',
          type: 'inference',
          entities: legalInferences.map(i => i.name)
        })
      }
      
      if (violationRisks.length > 0) {
        interpretations.push({
          text: `خطر نقض قانون: ${violationRisks.map(r => r.name).join('، ')}`,
          confidence: 'high',
          type: 'warning',
          entities: violationRisks.map(r => r.name)
        })
      }
    } else if (domain === 'medical' && language === 'fa') {
      // Medical domain interpretations
      const healthRisks = entities.filter(e => e.type === 'HEALTH_RISK')
      const medicalInferences = entities.filter(e => e.type === 'MEDICAL_INFERENCE')
      
      if (healthRisks.length > 0) {
        interpretations.push({
          text: `خطرات سلامتی شناسایی شده: ${healthRisks.map(r => r.name).join('، ')}`,
          confidence: 'high',
          type: 'warning',
          entities: healthRisks.map(r => r.name)
        })
      }
      
      if (medicalInferences.length > 0) {
        interpretations.push({
          text: `تشخیص احتمالی: ${medicalInferences.map(i => i.name).join('، ')}`,
          confidence: 'medium',
          type: 'inference',
          entities: medicalInferences.map(i => i.name)
        })
      }
    }
    
    // General inferences
    const generalInferences = entities.filter(e => e.type === 'INFERENCE')
    if (generalInferences.length > 0) {
      interpretations.push({
        text: `استنتاج: ${generalInferences.map(i => i.name).join('، ')}`,
        confidence: 'medium',
        type: 'inference',
        entities: generalInferences.map(i => i.name)
      })
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

  // Load available models on component mount
  const loadModels = async () => {
    setModelsLoading(true)
    try {
      const resp = await fetchWithTimeout('/api/models')
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`)
      const data = await resp.json()
      
      if (data.models && data.models.length > 0) {
        setAvailableModels(data.models)
        
        // Set default models if not set
        if (!model && data.models.length > 0) {
          setModel(data.models[0])
        }
        if (!modelFirst && data.models.length > 0) {
          setModelFirst(data.models[0])
        }
        if (!modelSecond && data.models.length > 1) {
          setModelSecond(data.models[1])
        }
        if (!modelReferee && data.models.length > 2) {
          setModelReferee(data.models[2])
        } else if (!modelReferee && data.models.length > 0) {
          setModelReferee(data.models[0])
        }
      }
    } catch (e: any) {
      console.error('Failed to load models:', e)
      // Fallback models
      const fallbackModels = ['gemma3:4b', 'qwen2.5:7b', 'gemma2:9b']
      setAvailableModels(fallbackModels)
      setModel(fallbackModels[0])
      setModelFirst(fallbackModels[0])
      setModelSecond(fallbackModels[1])
      setModelReferee(fallbackModels[2])
    } finally {
      setModelsLoading(false)
    }
  }

  // Load models on mount
  useEffect(() => {
    loadModels()
  }, [])

  const onExtract = async () => {
    if (analysisMode === 'single') {
      await onSingleExtract()
    } else {
      await onMultiExtract()
    }
  }

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

  return (
    <div className='app'>
      <header className='hero'>
        <h1 className='title'>LangExtract</h1>
        <p className='subtitle'>استخراج ساختاریافته اطلاعات از متن و فایل</p>
      </header>

      <div className='controls'>
        <label className='field'>
          <span>نوع تحلیل</span>
          <select className='select' value={analysisMode} onChange={(e) => setAnalysisMode(e.target.value as 'single' | 'multi')}>
            <option value='single'>تک مدل</option>
            <option value='multi'>چند مدل (داوری)</option>
          </select>
        </label>
        
        <label className='field'>
          <span>زبان</span>
          <select className='select' value={language} onChange={(e) => setLanguage(e.target.value as 'fa' | 'en')}>
            <option value='fa'>فارسی</option>
            <option value='en'>English</option>
          </select>
        </label>
        
        <label className='field'>
          <span>حوزه تخصصی</span>
          <select className='select' value={domain} onChange={(e) => setDomain(e.target.value as 'general' | 'legal' | 'medical' | 'police')}>
            <option value='general'>عمومی</option>
            <option value='legal'>حقوقی</option>
            <option value='medical'>پزشکی</option>
            <option value='police'>پلیسی</option>
          </select>
        </label>

        {analysisMode === 'single' ? (
          <label className='field'>
            <span>مدل</span>
            {modelsLoading ? (
              <select className='select' disabled>
                <option>در حال بارگیری...</option>
              </select>
            ) : (
              <select className='select' value={model} onChange={(e) => setModel(e.target.value)}>
                {availableModels.map((modelName) => (
                  <option key={modelName} value={modelName}>{modelName}</option>
                ))}
              </select>
            )}
          </label>
        ) : (
          <>
            <label className='field'>
              <span>مدل اول</span>
              {modelsLoading ? (
                <select className='select' disabled>
                  <option>در حال بارگیری...</option>
                </select>
              ) : (
                <select className='select' value={modelFirst} onChange={(e) => setModelFirst(e.target.value)}>
                  {availableModels.map((modelName) => (
                    <option key={modelName} value={modelName}>{modelName}</option>
                  ))}
                </select>
              )}
            </label>
            <label className='field'>
              <span>مدل دوم</span>
              {modelsLoading ? (
                <select className='select' disabled>
                  <option>در حال بارگیری...</option>
                </select>
              ) : (
                <select className='select' value={modelSecond} onChange={(e) => setModelSecond(e.target.value)}>
                  {availableModels.map((modelName) => (
                    <option key={modelName} value={modelName}>{modelName}</option>
                  ))}
                </select>
              )}
            </label>
            <label className='field'>
              <span>مدل داور</span>
              {modelsLoading ? (
                <select className='select' disabled>
                  <option>در حال بارگیری...</option>
                </select>
              ) : (
                <select className='select' value={modelReferee} onChange={(e) => setModelReferee(e.target.value)}>
                  {availableModels.map((modelName) => (
                    <option key={modelName} value={modelName}>{modelName}</option>
                  ))}
                </select>
              )}
            </label>
          </>
        )}
        
      </div>

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

      {error && <p className='error'>{error}</p>}
      
      {/* Single Model Results */}
      {analysisMode === 'single' && result && (
        <section className='results'>
          <div className='stats'>
            <p>Entities: {entityCount} | Relationships: {relCount} | Model: {result.model}</p>
          </div>
          
          {/* Smart Interpretations */}
          {interpretations.length > 0 && (
            <div className='interpretations'>
              <h3>🧠 تفسیر هوشمند</h3>
              {interpretations.map((interp, idx) => (
                <div key={idx} className={`interpretation interpretation-${interp.type} confidence-${interp.confidence}`}>
                  <div className='interpretation-icon'>
                    {interp.type === 'inference' && '🔍'}
                    {interp.type === 'warning' && '⚠️'}
                    {interp.type === 'risk' && '🚨'}
                    {interp.type === 'conclusion' && '✅'}
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
          
          <div className='grid'>
            <div className='glass'>
              <h3>موجودیت‌ها</h3>
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
              <h3>روابط</h3>
              <ul className='list'>
                {result.relationships.map((r, idx) => (
                  <li key={idx}>
                    <code>{r.source_entity_id}</code> — <b>{r.type}</b> → <code>{r.target_entity_id}</code>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      )}

      {/* Multi Model Results */}
      {analysisMode === 'multi' && multiResult && (
        <section className='results'>
          <div className='stats'>
            <p>
              Final Entities: {multiResult.final_analysis.entities.length} | 
              Final Relationships: {multiResult.final_analysis.relationships.length} |
              Agreement: {(multiResult.agreement_score! * 100).toFixed(1)}% |
              Domain: {multiResult.domain}
            </p>
          </div>
          
          {/* Analysis Steps */}
          <div className='multi-analysis'>
            <div className='analysis-step'>
              <h3>🤖 مدل اول: {multiResult.first_analysis.model_name}</h3>
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
              <h3>🤖 مدل دوم: {multiResult.second_analysis.model_name}</h3>
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
              <h3>⚖️ تصمیم نهایی داور: {multiResult.final_analysis.model_name}</h3>
              
              {/* Smart Interpretations for Multi-Model */}
              {interpretations.length > 0 && (
                <div className='interpretations'>
                  <h4>🧠 تفسیر نهایی هوشمند</h4>
                  {interpretations.map((interp, idx) => (
                    <div key={idx} className={`interpretation interpretation-${interp.type} confidence-${interp.confidence}`}>
                      <div className='interpretation-icon'>
                        {interp.type === 'inference' && '🔍'}
                        {interp.type === 'warning' && '⚠️'}
                        {interp.type === 'risk' && '🚨'}
                        {interp.type === 'conclusion' && '✅'}
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
                <h3>⚠️ تعارضات شناسایی شده</h3>
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
        </section>
      )}
    </div>
  )
}

export default App
