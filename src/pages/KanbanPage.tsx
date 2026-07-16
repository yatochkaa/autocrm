import { useState, useEffect } from 'react'
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import { getOrders, updateOrderStatus } from '../api/orders'
import type { Order, OrderStatus } from '../types'
import { KANBAN_COLUMNS, STATUS_LABELS, STATUS_COLORS } from '../utils/constants'
import { formatRub } from '../utils/format'
import KanbanColumn from '../components/KanbanColumn'
import KanbanCard from '../components/KanbanCard'
import './KanbanPage.css'

export default function KanbanPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [activeOrder, setActiveOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(false)

  // Загружаем все заявки (без пагинации — канбан показывает все)
  useEffect(() => {
    setLoading(true)
    getOrders({ page: 1, size: 200 })
      .then(res => setOrders(res.items))
      .finally(() => setLoading(false))
  }, [])

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }))

  const handleDragStart = (e: DragStartEvent) => {
    const order = orders.find(o => o.id === Number(e.active.id))
    setActiveOrder(order ?? null)
  }

  const handleDragEnd = async (e: DragEndEvent) => {
    setActiveOrder(null)
    const { active, over } = e
    if (!over) return
    const orderId = Number(active.id)
    const newStatus = over.id as OrderStatus
    const order = orders.find(o => o.id === orderId)
    if (!order || order.status === newStatus) return

    // Оптимистично обновляем локально, затем синх с бэкендом
    setOrders(prev => prev.map(o => o.id === orderId ? { ...o, status: newStatus } : o))
    try {
      await updateOrderStatus(orderId, newStatus)
    } catch {
      // Откатываем при ошибке
      setOrders(prev => prev.map(o => o.id === orderId ? { ...o, status: order.status } : o))
    }
  }

  const getColumnOrders = (status: OrderStatus) => orders.filter(o => o.status === status)

  return (
    <div>
      <h1 className="page-title">Канбан</h1>
      {loading ? <div className="loading">Загрузка...</div> : (
        <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
          <div className="kanban-board">
            {KANBAN_COLUMNS.map(status => (
              <KanbanColumn
                key={status}
                status={status}
                label={STATUS_LABELS[status]}
                color={STATUS_COLORS[status]}
                orders={getColumnOrders(status)}
              />
            ))}
          </div>
          <DragOverlay>
            {activeOrder && (
              <div className="drag-overlay-card">
                <strong>#{activeOrder.id}</strong> {activeOrder.client_name}
                <div className="muted">{formatRub(activeOrder.total_sell)}</div>
              </div>
            )}
          </DragOverlay>
        </DndContext>
      )}
    </div>
  )
}
