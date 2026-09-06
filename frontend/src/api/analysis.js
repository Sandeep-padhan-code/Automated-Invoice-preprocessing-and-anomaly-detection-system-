import { request } from './client'
export async function analyzeInvoice(file) {
  const body = new FormData()
  body.append('file', file)
  return request('/api/analyze', { method: 'POST', body })
}
