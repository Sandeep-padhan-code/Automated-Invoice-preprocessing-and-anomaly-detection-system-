import { request } from './client'
export async function getInvoices() {
  try { return { data: await request('/api/invoices'), source: 'api' } }
  catch { return { data: [], source: 'offline' } }
}

export async function getInvoice(id) {
  try { return { data: await request(`/api/invoices/${id}`), source: 'api' } }
  catch { return { data: null, source: 'offline' } }
}
