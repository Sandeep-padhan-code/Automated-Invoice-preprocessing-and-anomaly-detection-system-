import React from 'react'
import { Menu, Search } from 'lucide-react'
export default function Navbar({ page, onMenu, onSearch, onProfile }) {
  return <header className="topbar"><button className="mobile-menu" onClick={onMenu} aria-label="Open navigation"><Menu size={20}/></button><div className="crumb"><span>Workspace</span><b>/</b><strong>{page}</strong></div><div className="top-actions"><button className="icon-button" aria-label="Search" onClick={onSearch}><Search size={18}/></button><button className="avatar" aria-label="Open profile" onClick={onProfile}>AK</button></div></header>
}
