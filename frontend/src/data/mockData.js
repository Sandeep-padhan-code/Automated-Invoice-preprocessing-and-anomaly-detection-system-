export const mockInvoices = [
  { invoice_number: 'PO-554764', date: '2024-08-21', vendor: 'Northstar Office Supply', client: 'LedgerLens Operations', subtotal: 1480, tax: 0, total: 1480, expected_total: 1746.4, difference: -266.4, anomaly: true, severity: 'Medium', score: 50, anomaly_text: 'Missing tax' },
  { invoice_number: 'PO-794887', date: '2024-08-19', vendor: 'CIMCO Refrigeration', client: 'Arctic Retail Group', subtotal: 7830, tax: 1300, total: 7830, expected_total: 9130, difference: -1300, anomaly: true, severity: 'Medium', score: 50, anomaly_text: 'Total mismatch' },
  { invoice_number: '257667', date: '2024-08-16', vendor: 'Apex Services Ltd.', client: 'Nour Services Inc.', subtotal: 2400, tax: 432, total: 2550, expected_total: 2832, difference: -282, anomaly: true, severity: 'High', score: 50, anomaly_text: 'Total mismatch' },
  { invoice_number: '282297', date: '2024-08-12', vendor: 'Blue Oak Logistics', client: 'LedgerLens Operations', subtotal: 5200, tax: 936, total: 6136, expected_total: 6136, difference: 0, anomaly: false, severity: 'Normal', score: 0, anomaly_text: 'Validated' },
  { invoice_number: 'INV-8628', date: '2024-08-08', vendor: 'Apex Services Ltd.', client: 'Nour Services Inc.', subtotal: 13766.32, tax: 2753.26, total: 16540.91, expected_total: 16519.58, difference: 21.33, anomaly: true, severity: 'Low', score: 50, anomaly_text: 'Shipping variance' },
  { invoice_number: 'INV-9182', date: '2024-08-02', vendor: 'Moss & Finch', client: 'LedgerLens Operations', subtotal: 914, tax: 164.52, total: 1078.52, expected_total: 1078.52, difference: 0, anomaly: false, severity: 'Normal', score: 0, anomaly_text: 'Validated' }
]

export const mockStatistics = { total: 337, normal: 205, anomalous: 132, anomaly_rate: 39.17, processing: [{ name: 'Normal', value: 205 }, { name: 'Anomalous', value: 132 }], distribution: [{ name: 'Missing field', value: 44 }, { name: 'Total mismatch', value: 38 }, { name: 'Tax mismatch', value: 21 }, { name: 'Negative amount', value: 9 }, { name: 'Duplicate invoice', value: 12 }, { name: 'Date issue', value: 8 }], trend: [{ date: 'Aug 01', total: 12400 }, { date: 'Aug 05', total: 18600 }, { date: 'Aug 09', total: 14200 }, { date: 'Aug 13', total: 25800 }, { date: 'Aug 17', total: 21400 }, { date: 'Aug 21', total: 31900 }, { date: 'Aug 25', total: 28600 }] }

export const mockModelPerformance = [
  { model: 'Logistic Regression', accuracy: 1, precision: 1, recall: 1, f1: 1 },
  { model: 'Random Forest', accuracy: 1, precision: 1, recall: 1, f1: 1 },
  { model: 'Isolation Forest', accuracy: .6618, precision: .7, recall: .2593, f1: .3784 }
]
