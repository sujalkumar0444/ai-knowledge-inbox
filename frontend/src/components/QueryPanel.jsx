import { useState } from 'react'
import { askQuestion } from '../api'

export default function QueryPanel() {
  const [question, setQuestion] = useState('')
  const [status, setStatus] = useState('idle') // idle | asking | error
  const [errorMessage, setErrorMessage] = useState('')
  const [result, setResult] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!question.trim()) return

    setStatus('asking')
    setErrorMessage('')

    try {
      const data = await askQuestion({ question })
      setResult(data)
      setStatus('idle')
    } catch (err) {
      setStatus('error')
      setErrorMessage(err.message || 'Something went wrong while answering.')
    }
  }

  return (
    <div className="rounded-md border border-line bg-panel">
      <div className="px-4 py-2.5 border-b border-line">
        <span className="mono text-sm font-medium tracking-wide text-ink">ASK</span>
      </div>

      <form onSubmit={handleSubmit} className="p-4 flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about your saved content…"
          className="flex-1 rounded border border-line bg-paper px-3 py-2 text-sm outline-none focus:border-accent focus:ring-1 focus:ring-accent"
        />
        <button
          type="submit"
          disabled={status === 'asking'}
          className="rounded bg-accent text-paper text-sm font-medium px-4 py-2 hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
        >
          {status === 'asking' ? 'Thinking…' : 'Ask'}
        </button>
      </form>

      {status === 'error' && (
        <p className="px-4 pb-4 text-sm text-warn" role="alert">
          {errorMessage}
        </p>
      )}

      {result && (
        <div className="px-4 pb-4 space-y-4 border-t border-line pt-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="mono text-[10px] tracking-wider text-muted">ANSWER</span>
              {result.generation_mode === 'extractive_fallback' && (
                <span className="mono text-[10px] tracking-wider px-1.5 py-0.5 rounded bg-line text-muted">
                  NO LLM KEY · EXTRACTIVE MODE
                </span>
              )}
            </div>
            <p className="text-sm leading-relaxed whitespace-pre-line">{result.answer}</p>
          </div>

          {result.sources.length > 0 && (
            <div>
              <span className="mono text-[10px] tracking-wider text-muted block mb-1.5">
                SOURCES
              </span>
              <ul className="space-y-2">
                {result.sources.map((source, i) => (
                  <li
                    key={`${source.item_id}-${i}`}
                    className="rounded border border-line bg-paper px-3 py-2"
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="text-xs font-medium truncate">
                        {source.title || source.source_url || 'Untitled'}
                      </span>
                      <span className="mono text-[10px] text-muted whitespace-nowrap">
                        {Math.round(source.similarity * 100)}% match
                      </span>
                    </div>
                    <p className="text-xs text-muted leading-snug">{source.snippet}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
