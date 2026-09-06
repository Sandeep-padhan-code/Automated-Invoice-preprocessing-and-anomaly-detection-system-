import React from 'react'
import { BarChart3, Boxes, Home, Info, Settings2 } from 'lucide-react'
export default function Sidebar({ page, setPage, onSettings }) {
  const links = [['Home', Home], ['Dashboard', BarChart3], ['Inventory', Boxes], ['About', Info]]
  return <aside className="sidebar"><div className="side-brand"><div className="logo-mark">AI</div><div><b>AI Invoice</b><small>Intelligence</small></div></div><nav aria-label="Primary navigation">{links.map(([name, Icon]) => <button className={page === name ? 'nav-item active' : 'nav-item'} onClick={() => setPage(name)} key={name}><Icon size={17}/>{name}</button>)}</nav><button className="nav-item settings" onClick={onSettings}><Settings2 size={17}/>Settings</button></aside>
}
