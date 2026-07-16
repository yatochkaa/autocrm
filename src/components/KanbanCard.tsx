import { useDraggable } from '@dnd-kit/core'
import { Link } from 'react-router-dom'
import type { Order } from '../types'
import { SOURCE_LABELS } from '../utils/constants'
import { formatRub } from '../utils/format'
import './KanbanCard.css'

interface Props { order: Order }

export default function KanbanCard({ order }: Props) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: order.id,
  })

  const style = transform
    ? { transform: `translate(${transform.x}px, ${transform.y}px)` }
    : undefined

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`kanban-card${isDragging ? ' kanban-card--dragging' : ''}`}
      {...attributes}
      {...listeners}
    >
      <div className="kanban-card-id">
        <Link to={`/orders/${order.id}`} onClick={e => e.stopPropagation()}>#{order.id}</Link>
        <span className="kanban-card-source">{SOURCE_LABELS[order.source]}</span>
      </div>
      <div className="kanban-card-client">{order.client_name}</div>
      {order.car_model && <div className="kanban-card-car">{order.car_model}</div>}
      {order.total_sell > 0 && <div className="kanban-card-sum">{formatRub(order.total_sell)}</div>}
      {order.manager && <div className="kanban-card-manager">{order.manager.full_name}</div>}
    </div>
  )
}
