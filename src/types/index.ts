// ---- Основные типы, соответствующие схемам FastAPI-бэкенда ----

export type OrderStatus =
  | 'new'
  | 'in_progress'
  | 'selection'
  | 'invoice'
  | 'sold'
  | 'rejected'

export type OrderSource = 'telegram' | 'manual' | 'website'

export interface User {
  id: number
  username: string
  full_name: string
  role: 'admin' | 'manager'
}

export interface OrderItem {
  id: number
  part_name: string
  part_number: string
  quantity: number
  buy_price: number   // закупочная цена
  sell_price: number  // цена продажи
}

export interface Order {
  id: number
  status: OrderStatus
  source: OrderSource
  client_name: string
  client_phone: string
  vin: string
  car_model: string
  comment: string
  manager: User | null
  items: OrderItem[]
  total_sell: number
  total_margin: number
  created_at: string
  updated_at: string
}

// Пагинированный список заявок
export interface OrdersPage {
  items: Order[]
  total: number
  page: number
  size: number
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface DashboardStats {
  total_orders: number
  sold_orders: number
  rejected_orders: number
  conversion_rate: number   // %
  total_revenue: number
  total_margin: number
  by_source: { source: OrderSource; count: number }[]
  by_status: { status: OrderStatus; count: number }[]
  revenue_by_day: { date: string; revenue: number; margin: number }[]
}

// Фильтры для списка заявок
export interface OrderFilters {
  status?: OrderStatus | ''
  source?: OrderSource | ''
  manager_id?: number | ''
  page: number
  size: number
}
