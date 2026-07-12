import { useEffect, useState } from 'react'
import './App.css'

const steps = ['Reading Document', 'Splitting Chunks', 'Generating Embeddings', 'ChromaDB Synced']
const STORAGE_KEYS = {
  groq: 'rag-groq-key',
  nomic: 'rag-nomic-key',
}

function App() {
  const [ingesting, setIngesting] = useState(false)
  const [querying, setQuerying] = useState(false)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [context, setContext] = useState([])
  const [error, setError] = useState('')
  const [status, setStatus] = useState('Ready to ingest a PDF and explore the RAG pipeline.')
  const [stepsState, setStepsState] = useState([false, false, false, false])
  const [metrics, setMetrics] = useState({
    chunks: 0,
    collection: 'Not synced',
    lastRun: 'Not run',
  })
  const [groqApiKey, setGroqApiKey] = useState('')
  const [nomicApiKey, setNomicApiKey] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [saveKeys, setSaveKeys] = useState(true)

  useEffect(() => {
    setGroqApiKey(localStorage.getItem(STORAGE_KEYS.groq) || '')
    setNomicApiKey(localStorage.getItem(STORAGE_KEYS.nomic) || '')
  }, [])

  useEffect(() => {
    if (saveKeys) {
      localStorage.setItem(STORAGE_KEYS.groq, groqApiKey)
      localStorage.setItem(STORAGE_KEYS.nomic, nomicApiKey)
    } else {
      localStorage.removeItem(STORAGE_KEYS.groq)
      localStorage.removeItem(STORAGE_KEYS.nomic)
    }
  }, [groqApiKey, nomicApiKey, saveKeys])

  const handleIngest = async (event) => {
    event.preventDefault()
    setIngesting(true)
    setError('')
    setAnswer('')
    setContext([])
    setStatus('Reading your PDF and preparing the document...')
    setStepsState([true, false, false, false])

    try {
      const formData = new FormData()
      if (selectedFile) {
        formData.append('file', selectedFile)
      }
      if (groqApiKey.trim()) {
        formData.append('groq_api_key', groqApiKey.trim())
      }
      if (nomicApiKey.trim()) {
        formData.append('nomic_api_key', nomicApiKey.trim())
      }

      await new Promise((resolve) => window.setTimeout(resolve, 400))
      setStatus('Splitting the document into overlapping chunks...')
      setStepsState([true, true, false, false])

      await new Promise((resolve) => window.setTimeout(resolve, 400))
      setStatus('Generating embeddings and preparing retrieval context...')
      setStepsState([true, true, true, false])

      const response = await fetch('/api/ingest', {
        method: 'POST',
        body: formData,
      })

      const payload = await response.json().catch(() => ({}))
      if (!response.ok) {
        throw new Error(payload.detail || 'Ingestion failed')
      }

      setStatus(payload.message || 'Ingestion complete.')
      setStepsState([true, true, true, true])
      setMetrics({
        chunks: payload.chunks_created ?? 0,
        collection: 'Local ChromaDB',
        lastRun: new Date().toLocaleTimeString(),
      })
    } catch (err) {
      setError(err.message || 'Something went wrong during ingestion.')
      setStatus('Ingestion failed.')
      setStepsState([true, true, false, false])
    } finally {
      setIngesting(false)
    }
  }

  const handleQuery = async (event) => {
    event.preventDefault()
    if (!question.trim()) {
      setError('Enter a question to retrieve context and generate an answer.')
      return
    }

    setQuerying(true)
    setError('')
    setAnswer('')
    setContext([])
    setStatus('Searching the local vector store and assembling the prompt...')

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          groq_api_key: groqApiKey.trim() || undefined,
          nomic_api_key: nomicApiKey.trim() || undefined,
        }),
      })

      const payload = await response.json().catch(() => ({}))
      if (!response.ok) {
        throw new Error(payload.detail || 'Query failed')
      }

      setAnswer(payload.answer || 'No answer generated.')
      setContext(payload.context || [])
      setStatus('Answer generated from the retrieved chunks.')
    } catch (err) {
      setError(err.message || 'The query could not be completed.')
      setStatus('Query failed.')
    } finally {
      setQuerying(false)
    }
  }

  return (
    <div className="app-shell">
      <div className="panel">
        <div className="hero">
          <div>
            <div className="badge">RAG Explorer • Local Chroma + Groq</div>
            <h1>Inspect the full retrieval-augmented generation pipeline.</h1>
            <p>
              Upload a PDF, add your API keys, ingest the document, and then ask questions to inspect the exact context used for the answer.
            </p>
          </div>
          <button className="primary-btn" type="button" onClick={handleIngest} disabled={ingesting}>
            {ingesting ? 'Ingesting…' : 'Trigger Data Ingestion'}
          </button>
        </div>

        <div className="control-grid">
          <div className="section-card">
            <h2>Upload PDF</h2>
            <label className="upload-box">
              <input type="file" accept=".pdf,.txt" onChange={(event) => setSelectedFile(event.target.files?.[0] || null)} />
              <span>{selectedFile ? selectedFile.name : 'Choose a PDF or TXT file'}</span>
            </label>
            <p className="helper">If no file is selected, the backend will fall back to the bundled sample PDF.</p>
          </div>

          <div className="section-card">
            <h2>API key settings</h2>
            <label className="field">
              <span>Groq API key</span>
              <input
                type="password"
                value={groqApiKey}
                onChange={(event) => setGroqApiKey(event.target.value)}
                placeholder="sk-..."
              />
            </label>
            <label className="field">
              <span>Nomic API key</span>
              <input
                type="password"
                value={nomicApiKey}
                onChange={(event) => setNomicApiKey(event.target.value)}
                placeholder="nm-..."
              />
            </label>
            <label className="checkbox-row">
              <input type="checkbox" checked={saveKeys} onChange={() => setSaveKeys((value) => !value)} />
              <span>Save these keys in this browser</span>
            </label>
          </div>
        </div>

        <div className="metrics">
          <div className="metric-card">
            <h3>Total Chunks</h3>
            <p>{metrics.chunks}</p>
          </div>
          <div className="metric-card">
            <h3>Vector Store</h3>
            <p>{metrics.collection}</p>
          </div>
          <div className="metric-card">
            <h3>Last Run</h3>
            <p>{metrics.lastRun}</p>
          </div>
        </div>

        <div className="steps">
          {steps.map((step, index) => (
            <div key={step} className={`step${stepsState[index] ? ' active' : ''}`}>
              {index + 1}. {step}
            </div>
          ))}
        </div>

        {status && <p className="status">{status}</p>}
        {error && <p className="error">{error}</p>}

        <form className="query-box" onSubmit={handleQuery}>
          <input
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask about the uploaded product requirements document..."
          />
          <button className="primary-btn" disabled={querying} type="submit">
            {querying ? 'Searching…' : 'Run RAG Query'}
          </button>
        </form>

        {(answer || context.length > 0) && (
          <div className="results-grid">
            <div className="answer-card">
              <h2>Answer</h2>
              <p>{answer}</p>
            </div>
            <div className="context-card">
              <h2>Context Chunks</h2>
              <div className="context-list">
                {context.map((item, index) => (
                  <div key={`${item.text}-${index}`} className="context-item">
                    <p>{item.text}</p>
                    <small>Similarity score: {item.score ?? 'n/a'}</small>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
