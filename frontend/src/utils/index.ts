import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { formatDistanceToNow, format, isPast } from 'date-fns'
import type { SeverityLevel, TaskStatus } from '@/types'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// ─── Severity helpers ──────────────────────────────────
export function getSeverityClass(severity: SeverityLevel | null | undefined): string {
  switch (severity) {
    case 'critical': return 'badge-critical'
    case 'high': return 'badge-high'
    case 'medium': return 'badge-medium'
    case 'low': return 'badge-low'
    default: return 'badge-medium'
  }
}

export function getSeverityColor(severity: SeverityLevel | null | undefined): string {
  switch (severity) {
    case 'critical': return '#dc2626'
    case 'high': return '#ea580c'
    case 'medium': return '#ca8a04'
    case 'low': return '#16a34a'
    default: return '#64748b'
  }
}

export function getSeverityLabel(severity: SeverityLevel | null | undefined): string {
  if (!severity) return 'Unknown'
  return severity.charAt(0).toUpperCase() + severity.slice(1)
}

// ─── Task Status helpers ───────────────────────────────
export function getTaskStatusClass(status: TaskStatus | null | undefined, isOverdue?: boolean): string {
  if (isOverdue) return 'badge-overdue'
  switch (status) {
    case 'open': return 'badge-open'
    case 'assigned': return 'badge-assigned'
    case 'in_progress': return 'badge-in-progress'
    case 'escalated': return 'badge-escalated'
    case 'resolved': return 'badge-resolved'
    case 'verified': return 'badge-verified'
    case 'closed': return 'badge-closed'
    default: return 'badge-open'
  }
}

// ─── Date helpers ──────────────────────────────────────
export function formatRelative(date: string | null | undefined): string {
  if (!date) return '—'
  try {
    return formatDistanceToNow(new Date(date), { addSuffix: true })
  } catch {
    return '—'
  }
}

export function formatDate(date: string | null | undefined, fmt = 'dd MMM yyyy'): string {
  if (!date) return '—'
  try {
    return format(new Date(date), fmt)
  } catch {
    return '—'
  }
}

export function formatDateTime(date: string | null | undefined): string {
  return formatDate(date, 'dd MMM yyyy HH:mm')
}

export function isOverdue(dueDate: string | null | undefined, status: TaskStatus | null | undefined): boolean {
  if (!dueDate || !status) return false
  const closedStatuses = ['resolved', 'verified', 'closed']
  if (closedStatuses.includes(status)) return false
  return isPast(new Date(dueDate))
}

// ─── Compliance color ──────────────────────────────────
export function getComplianceColor(pct: number): string {
  if (pct >= 90) return '#16a34a'
  if (pct >= 75) return '#ca8a04'
  if (pct >= 60) return '#ea580c'
  return '#dc2626'
}

// ─── Truncate ─────────────────────────────────────────
export function truncate(str: string | null | undefined, maxLen = 80): string {
  if (!str) return '—'
  return str.length > maxLen ? str.slice(0, maxLen) + '…' : str
}

// ─── Reference number display ─────────────────────────
export function shortRef(ref: string | null | undefined): string {
  if (!ref) return '—'
  const parts = ref.split('-')
  return parts.slice(-2).join('-')
}

// ─── Sync status label ────────────────────────────────
export function syncLabel(status: string | null | undefined): string {
  switch (status) {
    case 'pending': return 'Pending'
    case 'syncing': return 'Syncing…'
    case 'synced': return 'Synced'
    case 'failed': return 'Sync Failed'
    case 'conflict': return 'Conflict'
    default: return '—'
  }
}

// ─── Category Icon label ──────────────────────────────
export function categoryLabel(cat: string | null | undefined): string {
  if (!cat) return '—'
  return cat.replace(/_/g, ' ')
}

// ─── Risk score bar ───────────────────────────────────
export function riskScoreWidth(score: number): string {
  return `${Math.round(score * 100)}%`
}

// ─── Inspect device fingerprint ───────────────────────
export function deviceId(): string {
  const stored = localStorage.getItem('device_id')
  if (stored) return stored
  const id = `DEV-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
  localStorage.setItem('device_id', id)
  return id
}
