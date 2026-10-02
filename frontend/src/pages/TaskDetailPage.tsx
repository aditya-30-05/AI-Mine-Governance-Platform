import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, CheckCircle, AlertTriangle, XCircle, ArrowUpRight, Clock, Shield } from 'lucide-react'
import { useTask, useResolveTask, useVerifyTask, useEscalateTask, useAuditTrail } from '@/hooks/useApi'
import { getTaskStatusClass, getSeverityClass, formatDateTime, formatRelative, isOverdue } from '@/utils'
import { useCanVerify, useIsMineManager } from '@/store/authStore'
import toast from 'react-hot-toast'
import type { TaskHistoryEntry } from '@/types'

export default function TaskDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: task, isLoading } = useTask(id ?? '')
  const { data: audit } = useAuditTrail('task', id ?? '')
  const canVerify = useCanVerify()
  const canEscalate = useIsMineManager()

  const resolveM = useResolveTask()
  const verifyM = useVerifyTask()
  const escalateM = useEscalateTask()

  const [note, setNote] = useState('')
  const [showAction, setShowAction] = useState<'resolve' | 'verify' | 'reject' | 'escalate' | null>(null)

  if (isLoading) {
    return <div className="space-y-4"><div className="skeleton h-8 w-64" /><div className="skeleton h-64 w-full" /></div>
  }
  if (!task) {
    return <div className="text-center text-muted-foreground py-12">Task not found</div>
  }

  const overdue = isOverdue(task.due_date, task.status)

  const handleAction = async () => {
    if (!note.trim()) { toast.error('Please enter a note'); return }
    try {
      if (showAction === 'resolve') {
        await resolveM.mutateAsync({ id: task.id, note })
        toast.success('Task resolved')
      } else if (showAction === 'verify') {
        await verifyM.mutateAsync({ id: task.id, note, approved: true })
        toast.success('Task verified')
      } else if (showAction === 'reject') {
        await verifyM.mutateAsync({ id: task.id, note, approved: false })
        toast.success('Verification rejected — sent back')
      } else if (showAction === 'escalate') {
        await escalateM.mutateAsync({ id: task.id, escalateToId: '', note })
        toast.success('Task escalated')
      }
      setShowAction(null)
      setNote('')
    } catch {
      toast.error('Action failed')
    }
  }

  return (
    <div className="space-y-4 animate-fade-in max-w-4xl">
      {/* Back */}
      <button className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground" onClick={() => navigate('/tasks')}>
        <ArrowLeft className="w-4 h-4" /> Back to Tasks
      </button>

      {/* Header */}
      <div className="card">
        <div className="card-body">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <span className={getTaskStatusClass(task.status, overdue)}>
                  {overdue ? 'OVERDUE' : task.status?.replace('_', ' ')}
                </span>
                {task.priority && <span className={getSeverityClass(task.priority)}>{task.priority}</span>}
                {task.escalation_count > 0 && (
                  <span className="badge-critical"><AlertTriangle className="w-3 h-3" /> Escalated ×{task.escalation_count}</span>
                )}
                <span className="font-mono text-xs text-muted-foreground">{task.reference_number}</span>
              </div>
              <h1 className="text-lg font-bold text-foreground">{task.title}</h1>
              {task.description && <p className="text-sm text-muted-foreground mt-2">{task.description}</p>}
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4 text-sm">
            <div><span className="text-xs text-muted-foreground block">Category</span><span className="text-foreground">{task.category ?? '—'}</span></div>
            <div><span className="text-xs text-muted-foreground block">Due Date</span><span className={overdue ? 'text-red-400' : 'text-foreground'}>{formatDateTime(task.due_date)}</span></div>
            <div><span className="text-xs text-muted-foreground block">Created</span><span className="text-foreground">{formatDateTime(task.created_at)}</span></div>
            <div><span className="text-xs text-muted-foreground block">Resolved</span><span className="text-foreground">{task.resolved_at ? formatDateTime(task.resolved_at) : '—'}</span></div>
          </div>

          {task.resolution_note && (
            <div className="mt-4 p-3 rounded-md bg-green-950/50 border border-green-800">
              <p className="text-xs text-green-400 font-semibold mb-1">Resolution Note</p>
              <p className="text-sm text-foreground">{task.resolution_note}</p>
            </div>
          )}
          {task.verification_note && (
            <div className="mt-2 p-3 rounded-md bg-blue-950/50 border border-blue-800">
              <p className="text-xs text-blue-400 font-semibold mb-1">Verification Note</p>
              <p className="text-sm text-foreground">{task.verification_note}</p>
            </div>
          )}
          {task.escalation_note && (
            <div className="mt-2 p-3 rounded-md bg-red-950/50 border border-red-800">
              <p className="text-xs text-red-400 font-semibold mb-1">Escalation Note</p>
              <p className="text-sm text-foreground">{task.escalation_note}</p>
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-2">
        {['open', 'assigned', 'in_progress', 'escalated'].includes(task.status ?? '') && (
          <button className="btn-primary" onClick={() => setShowAction('resolve')}>
            <CheckCircle className="w-4 h-4" /> Resolve
          </button>
        )}
        {task.status === 'resolved' && canVerify && (
          <>
            <button className="btn-primary" onClick={() => setShowAction('verify')}>
              <Shield className="w-4 h-4" /> Verify & Approve
            </button>
            <button className="btn-danger" onClick={() => setShowAction('reject')}>
              <XCircle className="w-4 h-4" /> Reject
            </button>
          </>
        )}
        {canEscalate && !['resolved', 'verified', 'closed'].includes(task.status ?? '') && (
          <button className="btn-danger" onClick={() => setShowAction('escalate')}>
            <ArrowUpRight className="w-4 h-4" /> Escalate
          </button>
        )}
      </div>

      {/* Action form */}
      {showAction && (
        <div className="card card-body space-y-3">
          <h3 className="text-sm font-semibold text-foreground capitalize">{showAction.replace('_', ' ')} Task</h3>
          <textarea
            className="form-input min-h-[80px]"
            placeholder={`Enter ${showAction} note…`}
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
          <div className="flex gap-2">
            <button className="btn-primary" onClick={handleAction} disabled={resolveM.isPending || verifyM.isPending || escalateM.isPending}>
              Submit
            </button>
            <button className="btn-secondary" onClick={() => { setShowAction(null); setNote('') }}>Cancel</button>
          </div>
        </div>
      )}

      {/* History Timeline */}
      {task.history && task.history.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="section-header"><Clock className="w-4 h-4 text-primary" />Task History</h2>
          </div>
          <div className="card-body">
            <div className="space-y-3">
              {task.history.map((h: TaskHistoryEntry, i: number) => (
                <div key={i} className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-primary mt-2 shrink-0" />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-foreground capitalize">{h.action.replace('_', ' ')}</span>
                      {h.new_status && <span className={getTaskStatusClass(h.new_status)}>{h.new_status.replace('_', ' ')}</span>}
                    </div>
                    {h.note && <p className="text-xs text-muted-foreground mt-0.5">{h.note}</p>}
                    <p className="text-xs text-muted-foreground mt-0.5">{formatDateTime(h.timestamp)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Audit Trail */}
      {audit && (
        <div className="card">
          <div className="card-header flex items-center justify-between">
            <h2 className="section-header mb-0"><Shield className="w-4 h-4 text-green-400" />Audit Trail</h2>
            <span className={audit.integrity?.verified ? 'audit-verified' : 'audit-violated'}>
              {audit.integrity?.verified ? '✓ Chain Verified' : '✗ Chain Broken'}
            </span>
          </div>
          <div className="card-body">
            <div className="space-y-2">
              {audit.entries?.slice(0, 10).map((entry: { id: string; action: string; timestamp: string; record_hash: string }) => (
                <div key={entry.id} className="flex items-center gap-3 text-xs border-b border-border/50 pb-2">
                  <span className="text-muted-foreground">{formatDateTime(entry.timestamp)}</span>
                  <span className="text-foreground font-medium capitalize">{entry.action}</span>
                  <span className="font-mono text-muted-foreground text-[10px] truncate max-w-[200px]">{entry.record_hash}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
