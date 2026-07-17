import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useTheme } from '../hooks/useTheme'
import { getUsers } from '../api/settings'
import { Icon } from './Icon'
import './Layout.css'

export default function Layout() {
  const { user, isAdmin, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const [displayName, setDisplayName] = useState('')

  useEffect(() => {
    if (!user) return
    getUsers().then(users => setDisplayName(users.find(item => item.id === user.id)?.full_name ?? '')).catch(() => undefined)
  }, [user])

  const handleLogout = () => { logout(); navigate('/login') }
  const name = displayName || (isAdmin ? 'Директор' : 'Менеджер')
  const initials = name.split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0]?.toUpperCase()).join('') || 'A'

  const navClass = ({ isActive }: { isActive:boolean }) => `nav-link${isActive ? ' active' : ''}`
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo"><span className="logo-mark"><Icon name="logo" size={21}/></span><span className="sidebar-logo-text">AutoCRM</span></div>
        <nav className="sidebar-nav">
          <NavLink to="/leads" className={navClass}><Icon name="leads"/><span>Заявки</span></NavLink>
          <NavLink to="/kanban" className={navClass}><Icon name="kanban"/><span>Канбан</span></NavLink>
          {isAdmin && <><NavLink to="/dashboard" className={navClass}><Icon name="dashboard"/><span>Дашборд</span></NavLink><NavLink to="/settings" className={navClass}><Icon name="settings"/><span>Настройки</span></NavLink></>}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-profile"><span className="profile-avatar">{initials}</span><span className="profile-copy"><b>{name}</b><small>{isAdmin ? 'Директор' : 'Менеджер'}</small></span></div>
          <button className="theme-toggle" onClick={toggleTheme}><span className="theme-label"><Icon name={theme === 'dark' ? 'moon' : 'sun'} size={17}/>{theme === 'dark' ? 'Тёмная тема' : 'Светлая тема'}</span><span className={`theme-switch${theme === 'dark' ? ' on' : ''}`}><i/></span></button>
          <button className="btn-logout" onClick={handleLogout}><Icon name="logout" size={17}/><span>Выйти</span></button>
        </div>
      </aside>
      <main className="main-content"><Outlet/></main>
    </div>
  )
}
