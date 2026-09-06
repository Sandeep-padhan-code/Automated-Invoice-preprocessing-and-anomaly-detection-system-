import { request } from './client'
import { mockModelPerformance } from '../data/mockData'

export async function getStatistics() {
  try { return { data: await request('/api/statistics'), source: 'api' } }
  catch { return { data: { total: 0, normal: 0, anomalous: 0, anomaly_rate: 0, distribution: [] }, source: 'offline' } }
}

export async function getModelPerformance() {
  try { return { data: await request('/api/models/performance'), source: 'api' } }
  catch { return { data: mockModelPerformance, source: 'mock' } }
}
