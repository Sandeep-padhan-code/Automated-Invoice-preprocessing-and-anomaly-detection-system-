const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export async function request(path, options = {}) {
  if (!API_URL) throw new Error('API not configured')
  let response
  try {
    response = await fetch(`${API_URL}${path}`, options)
  } catch {
    throw new Error('FastAPI backend is not running. Start it with: python -m uvicorn backend:app --reload --port 8000')
  }
  if (!response.ok) {
    let detail = `Request failed (${response.status})`
    try { detail = (await response.json()).detail || detail } catch { /* keep status fallback */ }
    throw new Error(detail)
  }
  return response.json()
}
