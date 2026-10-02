import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckSquare, Filter, Clock, ArrowUpRight, AlertTriangle, RefreshCw } from 'lucide-react'
import { useTasks } from '@/hooks/useApi'
import { getTaskStatusClass, getSeverityClass, formatRelative, truncate, isOverdue } from '@/utils'
import type { Task } from '@/types'

export default function TasksPage() {
  const navigate = useNavigate()
  const [status, setStatus] = useState('')
  const [priority, setPriority] = useState('')
  const [overdueOnly, setOverdueOnly] = useState(false)

  const { data, isLoading, refetch } = useTasks({
    status: status || undefined,
    priority: priority || undefined,
    overdue_only: overdueOnly || undefined,
    limit: 50,
  })

  const tasks: Task[] = data?.items ?? []

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Tasks & Actions</h1>
          <p className="text-sm text-muted-foreground">{data?.total ?? 0} tasks</p>
        </div>
        <button className="btn-secondary" onClick={() => refetch()}>
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 items-center">
        <Filter className="w-4 h-4 text-muted-foreground" />
        <select className="form-input w-auto text-xs py-1" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All Status</option>
          {['open', 'assigned', 'in_progress', 'escalated', 'resolved', 'verified', 'closed'].map((s) => (
            <option key={s} value={s}>{s.replace('_', ' ')}</option>
          ))}
        </select>
        <select className="form-input w-auto text-xs py-1" value={priority} onChange={(e) => setPriority(e.target.value)}>
          <option value="">All Priority</option>
          {['critical', 'high', 'medium', 'low'].map((p) => (
            <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
          ))}
        </select>
        <label className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-pointer">
          <input type="checkbox" checked={overdueOnly} onChange={(e) => setOverdueOnly(e.target.checked)} className="rounded" />
          Overdue only
        </label>
        {(status || priority || overdueOnly) && (
          <button className="text-xs text-muted-foreground hover:text-foreground" onClick={() => { setStatus(''); setPriority(''); setOverdueOnly(false) }}>
            Clear
          </button>
        )}
      </div>

      {/* Task list */}
      <div className="space-y-2">
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="card card-body"><div className="skeleton h-16 w-full" /></div>
          ))
        ) : tasks.length === 0 ? (
          <div className="card card-body text-center text-muted-foreground py-12">No tasks match filters</div>
        ) : tasks.map((t) => {
          const overdue = isOverdue(t.due_date, t.status)
          return (
            <div
              key={t.id}
              className="card cursor-pointer hover:border-primary/30 transition-colors"
              onClick={() => navigate(`/tasks/${t.id}`)}
            >
              <div className="card-body flex items-start gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={getTaskStatusClass(t.status, overdue)}>
                      {overdue ? 'OVERDUE' : t.status?.replace('_', ' ')}
                    </span>
                    {t.priority && <span className={getSeverityClass(t.priority)}>{t.priority}</span>}
                    {t.escalation_count > 0 && (
                      <span className="badge-critical">
                        <AlertTriangle className="w-3 h-3" /> Escalated ×{t.escalation_count}
                      </span>
                    )}
                    <span className="font-mono text-xs text-muted-foreground">{t.reference_number}</span>
                  </div>
                  <p className="text-sm font-medium text-foreground">{t.title}</p>
                  {t.description && <p className="text-xs text-muted-foreground mt-1">{truncate(t.description, 100)}</p>}
                  <div className="flex flex-wrap gap-3 mt-2 text-xs text-muted-foreground">
                    {t.category && <span>Category: {t.category}</span>}
                    {t.due_date && (
                      <span className={`flex items-center gap-1 ${overdue ? 'text-red-400' : ''}`}>
                        <Clock className="w-3 h-3" /> Due {formatRelative(t.due_date)}
                      </span>
                    )}
                    <span>Created {formatRelative(t.created_at)}</span>
                  </div>
                </div>
                <ArrowUpRight className="w-4 h-4 text-muted-foreground shrink-0 mt-1" />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
