import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useTheme } from '../hooks/useTheme'
import './Layout.css'

export default function Layout() {
  const { user, isAdmin, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()

  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="sidebar-logo-icon">🔧</span>
          <span className="sidebar-logo-text">AutoCRM</span>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/leads" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>
            <span className="nav-icon">📝</span><span>Заявки</span>
          </NavLink>
          <NavLink to="/kanban" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>
            <span className="nav-icon">📌</span><span>Канбан</span>
          </NavLink>
          {isAdmin && (
            <NavLink to="/dashboard" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>
              <span className="nav-icon">📊</span><span>Дашборд</span>
            </NavLink>
          )}
        </nav>

        <div className="sidebar-role-badge">
          <span className={`role-badge role-badge--${user?.role ?? 'manager'}`}>
            {user?.role === 'admin' ? 'Директор' : 'Менеджер'}
          </span>
        </div>

        <div className="sidebar-bottom">
          <button
            className="theme-toggle"
            onClick={toggleTheme}
            title={theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
          >
            {theme === 'dark' ? '☀️' : '🌙'} {theme === 'dark' ? 'Светлая' : 'Тёмная'}
          </button>
          <div className="sidebar-user-email" title={user?.email}>{user?.email}</div>
          <button className="btn-logout" onClick={handleLogout}>Выйти</button>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
