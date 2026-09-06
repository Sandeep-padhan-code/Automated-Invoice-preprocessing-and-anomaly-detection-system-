import React from 'react'
import { ArrowUpRight, CircleAlert, FileCheck2, FileText, Percent } from 'lucide-react'
const icons = { total: FileText, normal: FileCheck2, anomalous: CircleAlert, rate: Percent }
export default function MetricCard({ type, label, value, detail }) {
  const Icon = icons[type] || FileText
  return <article className="metric-card"><div className="metric-top"><span>{label}</span><Icon size={17}/></div><strong>{value}</strong><small>{detail}<ArrowUpRight size={13}/></small></article>
}
