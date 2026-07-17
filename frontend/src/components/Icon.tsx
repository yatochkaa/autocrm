import type { ReactNode } from 'react'
import type { LeadSource } from '../types'

export type IconName = 'logo'|'leads'|'kanban'|'dashboard'|'settings'|'moon'|'sun'|'logout'|'telegram'|'manual'|'site'|'car'|'phone'|'download'|'plus'|'reset'

const drawings: Record<IconName, ReactNode> = {
  logo: <><path d="M12 3l7 4v10l-7 4-7-4V7z"/><path d="M9 9h6v6H9z"/></>,
  leads: <><path d="M8 6h11M8 12h11M8 18h11"/><path d="M4 6h.01M4 12h.01M4 18h.01"/></>,
  kanban: <><rect x="4" y="5" width="4" height="14" rx="1"/><rect x="10" y="5" width="4" height="9" rx="1"/><rect x="16" y="5" width="4" height="12" rx="1"/></>,
  dashboard: <><rect x="4" y="13" width="3" height="7" rx="1"/><rect x="10.5" y="8" width="3" height="12" rx="1"/><rect x="17" y="4" width="3" height="16" rx="1"/></>,
  settings: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 00.3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 00-1.9-.3 1.7 1.7 0 00-1 1.6v.2h-4V21a1.7 1.7 0 00-1-1.6 1.7 1.7 0 00-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 00.3-1.9A1.7 1.7 0 003 14H2.8v-4H3a1.7 1.7 0 001.6-1 1.7 1.7 0 00-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 001.9.3A1.7 1.7 0 0010 3V2.8h4V3a1.7 1.7 0 001 1.6 1.7 1.7 0 001.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 00-.3 1.9 1.7 1.7 0 001.6 1h.2v4H21a1.7 1.7 0 00-1.6 1z"/></>,
  moon: <path d="M20 15.5A8.5 8.5 0 018.5 4 8.5 8.5 0 1020 15.5z"/>,
  sun: <><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></>,
  logout: <><path d="M10 4H5v16h5M14 8l4 4-4 4M18 12H9"/></>,
  telegram: <path d="M21 4L3 11l7 2 2 7 3-5 4 3z"/>,
  manual: <><path d="M4 20l5-1 10-10-4-4L5 15z"/><path d="M13 7l4 4"/></>,
  site: <><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 010 18M12 3a15 15 0 000 18"/></>,
  car: <><path d="M5 16l1-5 2-3h8l2 3 1 5"/><path d="M4 16h16v3H4z"/><circle cx="7" cy="19" r="1"/><circle cx="17" cy="19" r="1"/></>,
  phone: <path d="M7 3h3l1 5-2 1a14 14 0 006 6l1-2 5 1v3c0 2-2 4-4 3A18 18 0 014 7c-1-2 1-4 3-4z"/>,
  download: <><path d="M12 3v12M7 10l5 5 5-5"/><path d="M4 20h16"/></>,
  plus: <path d="M12 5v14M5 12h14"/>,
  reset: <><path d="M4 12a8 8 0 101.8-5"/><path d="M4 4v5h5"/></>,
}

export function Icon({ name, size=18, className='' }: { name:IconName; size?:number; className?:string }) {
  return <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{drawings[name]}</svg>
}

export function SourceIcon({ source, size=14 }: { source:LeadSource; size?:number }) {
  const name: IconName = source === 'telegram' ? 'telegram' : source === 'site' ? 'site' : 'manual'
  return <Icon name={name} size={size}/>
}
