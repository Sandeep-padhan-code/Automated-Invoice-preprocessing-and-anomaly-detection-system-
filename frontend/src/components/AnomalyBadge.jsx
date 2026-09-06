import React from 'react'

export default function AnomalyBadge({ anomaly, severity }) {
  return <span className={`badge ${anomaly ? 'badge-alert' : 'badge-ok'}`}><i />{anomaly ? severity || 'Review' : 'Validated'}</span>
}
