import { useMemo, useState } from 'react'
import './App.css'

interface Entity { id?: string; name: string; type: string; attributes?: Record<string, any> }
interface Relationship { id?: string; source_entity_id: string; target_entity_id: string; type: string; attributes?: Record<string, any> }
interface ExtractionResponse { text: string; language: string; model: string; entities: Entity[]; relationships: Relationship[] }

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
  const [text, setText] = useState('شخصی با نام علی سلیمی که در تهران کار می کند و در نیروی انتظامی و شرکت راهبرد هوشمند شهر کار می کند و همکار هایی با نام های یادگاری و خسروی دارد . او در نیروی انتظامی رییس گروه مهندسی است و در راهبرد هوشمند شهر مشاور  برنامه نویسی و جاوا است.')
  const [language, setLanguage] = useState<'fa' | 'en'>('fa')
  const [model, setModel] = useState('gemma3:4b')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ExtractionResponse | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const entityCount = useMemo(() => result?.entities?.length ?? 0, [result])
  const relCount = useMemo(() => result?.relationships?.length ?? 0, [result])

  const onExtract = async () => {
    setLoading(true)
    setError(null)
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
          <span>زبان</span>
          <select className='select' value={language} onChange={(e) => setLanguage(e.target.value as 'fa' | 'en')}>
            <option value='fa'>فارسی</option>
            <option value='en'>English</option>
          </select>
        </label>
        <label className='field'>
          <span>مدل</span>
          <input className='input' value={model} onChange={(e) => setModel(e.target.value)} placeholder='مثال: gemma3:4b' />
        </label>
        <label className='field'>
          <input type='file' onChange={(e) => setFile(e.target.files?.[0] || null)} />
          <button className='btn btn-outline' onClick={onExtractFile} disabled={loading || !file}>استخراج از فایل</button>
        </label>
      </div>

      <textarea className='textarea' value={text} onChange={(e) => setText(e.target.value)} placeholder='متن خود را اینجا وارد کنید...' />

      <div className='actions'>
        <button className='btn btn-primary' onClick={onExtract} disabled={loading}>{loading ? 'در حال استخراج...' : 'استخراج'}</button>
        <button className='btn btn-secondary' onClick={onReport} disabled={loading || !result}>گزارش HTML</button>
      </div>

      {error && <p className='error'>{error}</p>}
      {result && (
        <section className='results'>
          <div className='stats'>
            <p>Entities: {entityCount} | Relationships: {relCount}</p>
          </div>
          <div className='grid'>
            <div className='glass'>
              <h3>Entities</h3>
              <ul className='list'>
                {result.entities.map((e, idx) => (
                  <li key={idx}><b>{e.name}</b> <small>({e.type})</small></li>
                ))}
              </ul>
            </div>
            <div className='glass'>
              <h3>Relationships</h3>
              <ul className='list'>
                {result.relationships.map((r, idx) => (
                  <li key={idx}><code>{r.source_entity_id}</code> — <b>{r.type}</b> → <code>{r.target_entity_id}</code></li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}

export default App
