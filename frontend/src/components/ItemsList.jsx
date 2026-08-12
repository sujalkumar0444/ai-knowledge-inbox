function formatTimestamp(iso) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

function SourceTag({ type }) {
  const isUrl = type === 'url'
  return (
    <span
      className={`mono text-[10px] tracking-wider px-1.5 py-0.5 rounded ${
        isUrl ? 'bg-accent-soft text-accent' : 'bg-line text-ink'
      }`}
    >
      {isUrl ? 'URL' : 'NOTE'}
    </span>
  )
}

export default function ItemsList({ items, loading, error, onRetry }) {
  if (loading) {
    return <p className="text-sm text-muted px-1">Loading saved items…</p>
  }

  if (error) {
    return (
      <div className="text-sm text-warn px-1 flex items-center gap-2">
        <span>Couldn't load items: {error}</span>
        <button onClick={onRetry} className="underline hover:text-ink">
          Retry
        </button>
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-line px-4 py-6 text-center">
        <p className="text-sm text-muted">
          Nothing saved yet. Add a note or URL above to start building your inbox.
        </p>
      </div>
    )
  }

  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li
          key={item.id}
          className="rounded-md border border-line bg-panel px-3.5 py-3 hover:border-accent/60 transition-colors"
        >
          <div className="flex items-center justify-between gap-2 mb-1">
            <div className="flex items-center gap-2 min-w-0">
              <SourceTag type={item.source_type} />
              <span className="text-sm font-medium truncate">
                {item.title || (item.source_url ?? 'Untitled note')}
              </span>
            </div>
            <span className="mono text-[11px] text-muted whitespace-nowrap">
              {formatTimestamp(item.created_at)}
            </span>
          </div>
          <p className="text-sm text-muted leading-snug line-clamp-2">{item.preview}</p>
          {item.source_url && (
            <a
              href={item.source_url}
              target="_blank"
              rel="noreferrer"
              className="mono text-[11px] text-accent hover:underline block mt-1 truncate"
            >
              {item.source_url}
            </a>
          )}
          <span className="mono text-[10px] text-muted block mt-1.5">
            {item.chunk_count} chunk{item.chunk_count === 1 ? '' : 's'} indexed
          </span>
        </li>
      ))}
    </ul>
  )
}
