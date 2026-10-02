import { useNavigate } from 'react-router-dom'
import { ClipboardList, RefreshCw } from 'lucide-react'
import { useInspections } from '@/hooks/useApi'
import { formatRelative } from '@/utils'
import type { Inspection } from '@/types'

export default function InspectionsPage() {
  const navigate = useNavigate()
  const { data, isLoading, refetch } = useInspections({ limit: 50 })
  const inspections: Inspection[] = data?.items ?? (Array.isArray(data) ? data : [])

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Inspections</h1>
          <p className="text-sm text-muted-foreground">{inspections.length} records</p>
        </div>
        <div className="flex gap-2">
          <button className="btn-primary" onClick={() => navigate('/inspections/new')}>
            <ClipboardList className="w-4 h-4" /> New Inspection
          </button>
          <button className="btn-secondary" onClick={() => refetch()}>
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Type</th>
                <th>Status</th>
                <th>Compliance Score</th>
                <th>Sync</th>
                <th>Started</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>{Array.from({ length: 6 }).map((_, j) => <td key={j}><div className="skeleton h-4 w-full" /></td>)}</tr>
                ))
              ) : inspections.map((ins) => (
                <tr key={ins.id} className="cursor-pointer" onClick={() => navigate(`/inspections/${ins.id}`)}>
                  <td className="font-mono text-xs text-primary">{ins.reference_number}</td>
                  <td className="capitalize text-sm">{ins.inspection_type}</td>
                  <td><span className={`badge-${ins.status === 'completed' ? 'low' : ins.status === 'in_progress' ? 'medium' : 'high'}`}>{ins.status}</span></td>
                  <td>
                    {ins.overall_compliance_score != null ? (
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-secondary rounded-full overflow-hidden">
                          <div className="h-full bg-primary rounded-full" style={{ width: `${ins.overall_compliance_score * 100}%` }} />
                        </div>
                        <span className="text-xs">{(ins.overall_compliance_score * 100).toFixed(0)}%</span>
                      </div>
                    ) : '—'}
                  </td>
                  <td><span className={`sync-${ins.sync_status ?? 'synced'} text-xs font-medium`}>{ins.sync_status ?? 'synced'}</span></td>
                  <td className="text-xs text-muted-foreground">{formatRelative(ins.started_at ?? ins.created_at)}</td>
                </tr>
              ))}
              {!isLoading && !inspections.length && (
                <tr><td colSpan={6} className="text-center py-8 text-muted-foreground">No inspections</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
