import { useDroppable } from '@dnd-kit/core'
import type { Order, OrderStatus } from '../types'
import KanbanCard from './KanbanCard'
import './KanbanColumn.css'

interface Props {
  status: OrderStatus
  label: string
  color: string
  orders: Order[]
}

export default function KanbanColumn({ status, label, color, orders }: Props) {
  const { setNodeRef, isOver } = useDroppable({ id: status })

  return (
    <div className={`kanban-column${isOver ? ' kanban-column--over' : ''}`} ref={setNodeRef}>
      <div className="kanban-column-header" style={{ borderTopColor: color }}>
        <span className="kanban-column-title" style={{ color }}>{label}</span>
        <span className="kanban-column-count">{orders.length}</span>
      </div>
      <div className="kanban-column-body">
        {orders.map(order => (
          <KanbanCard key={order.id} order={order} />
        ))}
        {orders.length === 0 && (
          <div className="kanban-empty">Пусто</div>
        )}
      </div>
    </div>
  )
}
