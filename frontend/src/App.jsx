import { useCallback, useEffect, useState } from 'react'
import IngestForm from './components/IngestForm'
import ItemsList from './components/ItemsList'
import QueryPanel from './components/QueryPanel'
import { listItems } from './api'

export default function App() {
  const [items, setItems] = useState([])
  const [itemsLoading, setItemsLoading] = useState(true)
  const [itemsError, setItemsError] = useState('')

  const fetchItems = useCallback(async () => {
    setItemsLoading(true)
    setItemsError('')
    try {
      const data = await listItems()
      setItems(data.items)
    } catch (err) {
      setItemsError(err.message || 'Unknown error')
    } finally {
      setItemsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchItems()
  }, [fetchItems])

  return (
    <div className="min-h-screen bg-paper">
      <header className="border-b border-line">
        <div className="max-w-3xl mx-auto px-4 py-5 flex items-baseline justify-between">
          <div>
            <h1 className="text-lg font-semibold tracking-tight">AI Knowledge Inbox</h1>
            <p className="text-xs text-muted mt-0.5">
              Save notes and links, then ask questions across everything you've kept.
            </p>
          </div>
          <span className="mono text-[11px] text-muted whitespace-nowrap">
            {items.length} item{items.length === 1 ? '' : 's'} saved
          </span>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-6 space-y-8">
        <section aria-labelledby="add-heading">
          <h2 id="add-heading" className="mono text-[11px] tracking-wider text-muted mb-2">
            ADD CONTENT
          </h2>
          <IngestForm onIngested={fetchItems} />
        </section>

        <section aria-labelledby="ask-heading">
          <h2 id="ask-heading" className="mono text-[11px] tracking-wider text-muted mb-2">
            QUERY
          </h2>
          <QueryPanel />
        </section>

        <section aria-labelledby="items-heading">
          <h2 id="items-heading" className="mono text-[11px] tracking-wider text-muted mb-2">
            SAVED ITEMS
          </h2>
          <ItemsList
            items={items}
            loading={itemsLoading}
            error={itemsError}
            onRetry={fetchItems}
          />
        </section>
      </main>
    </div>
  )
}
