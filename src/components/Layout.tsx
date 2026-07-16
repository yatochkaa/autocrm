import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import './Layout.css'

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo">🔧 AutoCRM</div>
        <nav className="sidebar-nav">
          <NavLink to="/orders" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            📝 Заявки
          </NavLink>
          <NavLink to="/kanban" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            📌 Канбан
          </NavLink>
          <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            📊 Дашборд
          </NavLink>
        </nav>
        <div className="sidebar-user">
          <span>{user?.full_name ?? user?.username}</span>
          <button onClick={handleLogout} className="btn-logout">Выйти</button>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
