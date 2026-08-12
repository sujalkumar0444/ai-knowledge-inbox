import { useState } from 'react'
import { ingestNote, ingestUrl } from '../api'

const TABS = [
  { id: 'note', label: 'Note' },
  { id: 'url', label: 'URL' },
]

export default function IngestForm({ onIngested }) {
  const [tab, setTab] = useState('note')
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [url, setUrl] = useState('')
  const [status, setStatus] = useState('idle') // idle | saving | error
  const [errorMessage, setErrorMessage] = useState('')

  const resetFields = () => {
    setTitle('')
    setContent('')
    setUrl('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setStatus('saving')
    setErrorMessage('')

    try {
      if (tab === 'note') {
        if (!content.trim()) throw new Error('Write something before saving.')
        await ingestNote({ content, title })
      } else {
        if (!url.trim()) throw new Error('Enter a URL before saving.')
        await ingestUrl({ url })
      }
      resetFields()
      setStatus('idle')
      onIngested?.()
    } catch (err) {
      setStatus('error')
      setErrorMessage(err.message || 'Something went wrong while saving.')
    }
  }

  return (
    <div className="rounded-md border border-line bg-panel">
      <div className="flex border-b border-line">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => {
              setTab(t.id)
              setStatus('idle')
              setErrorMessage('')
            }}
            className={`px-4 py-2.5 text-sm font-medium mono tracking-wide transition-colors ${
              tab === t.id
                ? 'text-accent border-b-2 border-accent -mb-px'
                : 'text-muted hover:text-ink'
            }`}
          >
            {t.label.toUpperCase()}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="p-4 space-y-3">
        {tab === 'note' ? (
          <>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Title (optional)"
              className="w-full rounded border border-line bg-paper px-3 py-2 text-sm outline-none focus:border-accent focus:ring-1 focus:ring-accent"
            />
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste or write a note to save..."
              rows={5}
              className="w-full rounded border border-line bg-paper px-3 py-2 text-sm outline-none focus:border-accent focus:ring-1 focus:ring-accent resize-y"
            />
          </>
        ) : (
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/article"
            className="w-full rounded border border-line bg-paper px-3 py-2 text-sm outline-none focus:border-accent focus:ring-1 focus:ring-accent"
          />
        )}

        {status === 'error' && (
          <p className="text-sm text-warn" role="alert">
            {errorMessage}
          </p>
        )}

        <div className="flex items-center justify-between pt-1">
          <span className="text-xs text-muted mono">
            {tab === 'url' ? 'Page content is fetched server-side.' : 'Stored as plain text.'}
          </span>
          <button
            type="submit"
            disabled={status === 'saving'}
            className="rounded bg-ink text-paper text-sm font-medium px-4 py-2 hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {status === 'saving' ? 'Saving…' : 'Save to inbox'}
          </button>
        </div>
      </form>
    </div>
  )
}
