import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line, CartesianGrid,
} from 'recharts'
import { getDashboardStats } from '../api/dashboard'
import type { DashboardStats } from '../types'
import { STATUS_LABELS, STATUS_COLORS, SOURCE_LABELS } from '../utils/constants'
import { formatRub } from '../utils/format'
import './DashboardPage.css'

const PIE_COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#06b6d4']

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDashboardStats()
      .then(setStats)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="dash-loading">Загрузка...</div>
  if (!stats) return <div className="dash-loading">Нет данных</div>

  // Готовим данные для графиков
  const sourceData = stats.by_source.map(s => ({
    name: SOURCE_LABELS[s.source] ?? s.source,
    value: s.count,
  }))

  const statusData = stats.by_status.map(s => ({
    name: STATUS_LABELS[s.status] ?? s.status,
    count: s.count,
    fill: STATUS_COLORS[s.status] ?? '#999',
  }))

  const revenueData = stats.revenue_by_day.map(d => ({
    date: d.date.slice(5), // MM-DD
    revenue: d.revenue,
    margin: d.margin,
  }))

  return (
    <div className="dashboard">
      <h1 className="page-title">Дашборд</h1>

      {/* Карточки с цифрами */}
      <div className="stats-grid">
        <StatCard label="Всего заявок" value={stats.total_orders} />
        <StatCard label="Продажи" value={stats.sold_orders} accent="#10b981" />
        <StatCard label="Отказы" value={stats.rejected_orders} accent="#ef4444" />
        <StatCard label="Конверсия" value={`${stats.conversion_rate.toFixed(1)}%`} accent="#3b82f6" />
        <StatCard label="Выручка" value={formatRub(stats.total_revenue)} accent="#3b82f6" />
        <StatCard label="Маржа" value={formatRub(stats.total_margin)} accent="#10b981" />
      </div>

      {/* Графики */}
      <div className="charts-grid">
        {/* Выручка по дням */}
        <div className="card chart-card">
          <h2 className="chart-title">Выручка и маржа по дням</h2>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={revenueData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={v => `${(v / 1000).toFixed(0)}к`} />
              <Tooltip formatter={(v: number) => formatRub(v)} />
              <Legend />
              <Line type="monotone" dataKey="revenue" name="Выручка" stroke="#3b82f6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="margin" name="Маржа" stroke="#10b981" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* По источникам */}
        <div className="card chart-card">
          <h2 className="chart-title">Источники заявок</h2>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={sourceData}
                dataKey="value"
                nameKey="name"
                cx="50%" cy="50%"
                outerRadius={80}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {sourceData.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* По статусам */}
        <div className="card chart-card chart-card--wide">
          <h2 className="chart-title">Заявки по статусам</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={statusData} margin={{ left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" name="Заявок">
                {statusData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

// Маленький компонент — числовая карточка
function StatCard({ label, value, accent = '#333' }: { label: string; value: string | number; accent?: string }) {
  return (
    <div className="stat-card card">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color: accent }}>{value}</div>
    </div>
  )
}
