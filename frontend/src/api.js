const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  let body = null
  try {
    body = await res.json()
  } catch {
    // no JSON body (e.g. 204)
  }

  if (!res.ok) {
    const message =
      body?.detail && typeof body.detail === 'string'
        ? body.detail
        : body?.error || `Request failed with status ${res.status}`
    const error = new Error(message)
    error.status = res.status
    error.body = body
    throw error
  }

  return body
}

export function ingestNote({ content, title }) {
  return request('/ingest', {
    method: 'POST',
    body: JSON.stringify({ source_type: 'note', content, title: title || null }),
  })
}

export function ingestUrl({ url }) {
  return request('/ingest', {
    method: 'POST',
    body: JSON.stringify({ source_type: 'url', url }),
  })
}

export function listItems() {
  return request('/items')
}

export function askQuestion({ question }) {
  return request('/query', {
    method: 'POST',
    body: JSON.stringify({ question }),
  })
}
