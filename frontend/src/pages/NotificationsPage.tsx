import { Bell, Check, CheckCheck } from 'lucide-react'
import { useNotifications, useMarkNotificationRead } from '@/hooks/useApi'
import { notificationsApi } from '@/services/api'
import { formatRelative, getSeverityClass } from '@/utils'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import type { Notification } from '@/types'
import toast from 'react-hot-toast'

export default function NotificationsPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { data, isLoading } = useNotifications()
  const markRead = useMarkNotificationRead()
  const notifications: Notification[] = data?.items ?? []

  const markAll = async () => {
    await notificationsApi.markAllRead()
    qc.invalidateQueries({ queryKey: ['notifications'] })
    toast.success('All marked read')
  }

  return (
    <div className="space-y-4 animate-fade-in max-w-2xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Notifications</h1>
          <p className="text-sm text-muted-foreground">{data?.unread_count ?? 0} unread</p>
        </div>
        <button className="btn-secondary" onClick={markAll}>
          <CheckCheck className="w-4 h-4" /> Mark all read
        </button>
      </div>

      <div className="space-y-2">
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => <div key={i} className="card card-body"><div className="skeleton h-12 w-full" /></div>)
        ) : notifications.length === 0 ? (
          <div className="card card-body text-center text-muted-foreground py-12">
            <Bell className="w-8 h-8 mx-auto mb-2 opacity-30" />
            No notifications
          </div>
        ) : notifications.map((n) => (
          <div
            key={n.id}
            className={`card cursor-pointer transition-colors ${!n.is_read ? 'border-primary/30 bg-primary/5' : ''}`}
            onClick={() => {
              if (!n.is_read) markRead.mutate(n.id)
              if (n.action_url) navigate(n.action_url)
            }}
          >
            <div className="card-body flex items-start gap-3">
              {!n.is_read && <div className="w-2 h-2 rounded-full bg-primary mt-1.5 shrink-0" />}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-foreground">{n.title}</span>
                  {n.severity && <span className={getSeverityClass(n.severity)}>{n.severity}</span>}
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">{n.message}</p>
                <p className="text-xs text-muted-foreground mt-1">{formatRelative(n.created_at)}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
