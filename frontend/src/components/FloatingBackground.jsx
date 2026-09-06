import React, { useEffect, useRef } from 'react'

const labels = ['OCR', 'AI', 'ML', 'INVOICE', 'VALIDATED', 'ANOMALY', 'DATA', '98.5%']

export default function FloatingBackground() {
  const ref = useRef(null)
  useEffect(() => {
    const node = ref.current
    if (!node || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    let frame = 0; let targetX = 0; let targetY = 0; let x = 0; let y = 0
    const move = (event) => { targetX = (event.clientX / window.innerWidth - .5) * 2; targetY = (event.clientY / window.innerHeight - .5) * 2 }
    const tick = () => { x += (targetX - x) * .045; y += (targetY - y) * .045; node.style.setProperty('--mx', `${x * 18}px`); node.style.setProperty('--my', `${y * 18}px`); frame = requestAnimationFrame(tick) }
    window.addEventListener('pointermove', move, { passive: true }); frame = requestAnimationFrame(tick)
    return () => { window.removeEventListener('pointermove', move); cancelAnimationFrame(frame) }
  }, [])
  return <div className="floating-bg" ref={ref} aria-hidden="true"><div className="orb orb-one"/><div className="orb orb-two"/><div className="grid-glow"/><div className="float-labels">{labels.map((label, index) => <span key={label} style={{ '--i': index }}>{label}</span>)}</div><div className="cursor-glow"/></div>
}
