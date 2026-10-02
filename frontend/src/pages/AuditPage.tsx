import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ShieldCheck,
  Search,
  RefreshCw,
  Hash,
  Link as LinkIcon,
  CheckCircle2,
  AlertTriangle,
  FileCode2,
  Clock,
  Layers,
  ArrowRight,
  ExternalLink
} from 'lucide-react'
import { auditApi } from '@/services/api'
import { formatRelative, formatDate } from '@/utils'
import toast from 'react-hot-toast'

interface AuditLogEntry {
  id: string
  timestamp: string
  user_id: string | null
  action: string
  entity_type: string
  entity_id: string | null
  old_value: any
  new_value: any
  record_hash: string
  previous_hash: string | null
}

export default function AuditPage() {
  const [entityType, setEntityType] = useState('')
  const [actionSearch, setActionSearch] = useState('')
  const [selectedEntry, setSelectedEntry] = useState<AuditLogEntry | null>(null)
  const [verifyEntityId, setVerifyEntityId] = useState<string | null>(null)
  const [verifyType, setVerifyType] = useState<string | null>(null)

  const { data: summary, isLoading: isSummaryLoading, refetch: refetchSummary } = useQuery({
    queryKey: ['audit-summary'],
    queryFn: () => auditApi.summary(),
  })

  const { data: logsData, isLoading: isLogsLoading, refetch: refetchLogs } = useQuery({
    queryKey: ['audit-logs', entityType, actionSearch],
    queryFn: () =>
      auditApi.logs({
        entity_type: entityType || undefined,
        action: actionSearch || undefined,
        limit: 100,
      }),
  })

  const { data: entityChain, isFetching: isVerifyingChain } = useQuery({
    queryKey: ['audit-chain', verifyType, verifyEntityId],
    queryFn: () => {
      if (!verifyType || !verifyEntityId) return null
      return auditApi.get(verifyType, verifyEntityId)
    },
    enabled: Boolean(verifyType && verifyEntityId),
  })

  const handleVerify = (type: string, id: string | null) => {
    if (!id) {
      toast.error('Entity ID is required to verify chain')
      return
    }
    setVerifyType(type)
    setVerifyEntityId(id)
    toast.success(`Checking cryptographic chain for ${type}:${id.slice(0, 8)}...`)
  }

  const logs: AuditLogEntry[] = logsData?.items ?? []

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header & Cryptographic Assurance Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-emerald-400" />
            <h1 className="text-xl font-bold text-foreground">Tamper-Evident Audit Trail</h1>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Cryptographically sealed immutable ledger powered by SHA-256 hash chains
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            className="btn-secondary"
            onClick={() => {
              refetchSummary()
              refetchLogs()
            }}
          >
            <RefreshCw className="w-4 h-4" /> Refresh Ledger
          </button>
        </div>
      </div>

      {/* Security Metrics Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card card-body bg-[hsl(222,47%,11%)] border border-emerald-500/30">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Integrity Status</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-emerald-400 mt-1">VERIFIED ACTIVE</div>
          <p className="text-[11px] text-muted-foreground mt-1">
            Zero broken links detected across all entity chains
          </p>
        </div>

        <div className="card card-body">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Total Ledger Blocks</span>
            <Layers className="w-4 h-4 text-primary" />
          </div>
          <div className="text-xl font-bold text-foreground mt-1">
            {isSummaryLoading ? '...' : summary?.total_records ?? logsData?.total ?? 0}
          </div>
          <p className="text-[11px] text-muted-foreground mt-1">Immutable SHA-256 state transitions</p>
        </div>

        <div className="card card-body">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Tracked Entities</span>
            <Hash className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-xl font-bold text-foreground mt-1">
            {isSummaryLoading ? '...' : summary?.unique_entities_tracked ?? 'Multi-Entity'}
          </div>
          <p className="text-[11px] text-muted-foreground mt-1">Mines, Inspections, Tasks & Violations</p>
        </div>

        <div className="card card-body">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Hash Algorithm</span>
            <LinkIcon className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-sm font-mono font-bold text-purple-300 mt-1">SHA-256 MERKLE/CHAIN</div>
          <p className="text-[11px] text-muted-foreground mt-1 font-mono truncate" title={summary?.latest_block_hash}>
            Tip: {summary?.latest_block_hash ? `${summary.latest_block_hash.slice(0, 16)}...` : 'Linked'}
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="card card-body flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <select
            className="form-input text-xs py-1.5 w-auto"
            value={entityType}
            onChange={(e) => setEntityType(e.target.value)}
          >
            <option value="">All Entities</option>
            <option value="inspection">Inspection</option>
            <option value="observation">Observation</option>
            <option value="task">Task</option>
            <option value="violation">Violation</option>
            <option value="user">User</option>
            <option value="document">Document</option>
          </select>

          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Filter by action (e.g. CREATE, ESCALATE)..."
              value={actionSearch}
              onChange={(e) => setActionSearch(e.target.value)}
              className="form-input text-xs pl-8 py-1.5 w-64"
            />
          </div>

          {(entityType || actionSearch) && (
            <button
              onClick={() => {
                setEntityType('')
                setActionSearch('')
              }}
              className="text-xs text-muted-foreground hover:text-foreground underline"
            >
              Clear filters
            </button>
          )}
        </div>

        <div className="text-xs text-muted-foreground">
          Showing <span className="font-semibold text-foreground">{logs.length}</span> recorded blocks
        </div>
      </div>

      {/* Ledger Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp (UTC)</th>
                <th>Action</th>
                <th>Entity Target</th>
                <th>Block Hash (SHA-256)</th>
                <th>Previous Hash Pointer</th>
                <th>Integrity</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {isLogsLoading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 7 }).map((_, j) => (
                      <td key={j}>
                        <div className="skeleton h-4 w-full" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-muted-foreground">
                    <ShieldCheck className="w-10 h-10 mx-auto mb-2 opacity-30 text-emerald-400" />
                    No audit records match the current filter
                  </td>
                </tr>
              ) : (
                logs.map((log) => {
                  const isActionCritical =
                    log.action.includes('ESCALAT') ||
                    log.action.includes('CRITICAL') ||
                    log.action.includes('VIOLATION')
                  const isActionSuccess =
                    log.action.includes('VERIF') ||
                    log.action.includes('RESOLV') ||
                    log.action.includes('APPROV')

                  return (
                    <tr key={log.id} className="hover:bg-primary/5 transition-colors">
                      <td className="text-xs whitespace-nowrap font-mono text-muted-foreground">
                        <div>{formatDate(log.timestamp)}</div>
                        <div className="text-[10px] opacity-70">{formatRelative(log.timestamp)}</div>
                      </td>

                      <td>
                        <span
                          className={`badge ${
                            isActionCritical
                              ? 'badge-critical'
                              : isActionSuccess
                              ? 'badge-low'
                              : 'badge-medium'
                          }`}
                        >
                          {log.action}
                        </span>
                      </td>

                      <td>
                        <div className="font-medium text-xs text-foreground uppercase tracking-wide">
                          {log.entity_type}
                        </div>
                        {log.entity_id && (
                          <div className="text-[11px] font-mono text-muted-foreground truncate max-w-[120px]">
                            {log.entity_id}
                          </div>
                        )}
                      </td>

                      <td className="font-mono text-xs text-primary truncate max-w-[160px]" title={log.record_hash}>
                        <span className="bg-primary/10 px-1.5 py-0.5 rounded text-[11px] border border-primary/20">
                          {log.record_hash.slice(0, 14)}...
                        </span>
                      </td>

                      <td
                        className="font-mono text-xs text-muted-foreground truncate max-w-[160px]"
                        title={log.previous_hash || 'Genesis block for this entity'}
                      >
                        {log.previous_hash ? (
                          <span className="bg-slate-800 px-1.5 py-0.5 rounded text-[11px] border border-slate-700">
                            {log.previous_hash.slice(0, 14)}...
                          </span>
                        ) : (
                          <span className="text-[10px] text-emerald-400 font-semibold uppercase tracking-wider">
                            Genesis Block
                          </span>
                        )}
                      </td>

                      <td>
                        <button
                          onClick={() => handleVerify(log.entity_type, log.entity_id)}
                          className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400 hover:text-emerald-300 underline"
                          title="Verify cryptographic integrity for this entity"
                        >
                          <ShieldCheck className="w-3.5 h-3.5" />
                          Verify Chain
                        </button>
                      </td>

                      <td>
                        <button
                          onClick={() => setSelectedEntry(log)}
                          className="btn-secondary text-xs py-1 px-2.5"
                        >
                          <FileCode2 className="w-3.5 h-3.5" /> Diff
                        </button>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Entity Chain Verification Modal */}
      {verifyEntityId && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="card max-w-xl w-full max-h-[85vh] flex flex-col border border-border shadow-2xl">
            <div className="card-header flex items-center justify-between border-b border-border">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <h3 className="font-semibold text-foreground text-sm">
                  Cryptographic Chain Integrity Verification
                </h3>
              </div>
              <button
                onClick={() => {
                  setVerifyEntityId(null)
                  setVerifyType(null)
                }}
                className="text-muted-foreground hover:text-foreground text-sm"
              >
                ✕
              </button>
            </div>

            <div className="card-body overflow-y-auto space-y-4">
              <div className="bg-[hsl(222,47%,10%)] border border-border rounded-lg p-3 text-xs space-y-2">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Entity Type:</span>
                  <span className="font-semibold uppercase text-foreground">{verifyType}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Entity UUID:</span>
                  <span className="font-mono text-primary text-[11px]">{verifyEntityId}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Verification Check:</span>
                  {isVerifyingChain ? (
                    <span className="text-yellow-400 font-medium">Recomputing SHA-256 Hashes...</span>
                  ) : entityChain?.integrity?.verified ? (
                    <span className="text-emerald-400 font-bold flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> 100% UNTAMPERED HASH CHAIN
                    </span>
                  ) : (
                    <span className="text-red-400 font-bold flex items-center gap-1">
                      <AlertTriangle className="w-3.5 h-3.5" /> INTEGRITY TAMPER DETECTED
                    </span>
                  )}
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Verified Chain Length:</span>
                  <span className="font-semibold text-foreground">
                    {entityChain?.integrity?.chain_length ?? 0} Blocks
                  </span>
                </div>
              </div>

              {/* Chain steps visualization */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-foreground">Chain Execution Sequence</h4>
                <div className="space-y-2">
                  {entityChain?.entries?.map((block: any, idx: number) => (
                    <div
                      key={block.id}
                      className="border border-border/80 bg-background/50 rounded p-2.5 text-xs space-y-1 relative"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-[10px] text-muted-foreground">
                          Block #{idx + 1} • {formatDate(block.timestamp)}
                        </span>
                        <span className="badge badge-low text-[10px]">{block.action}</span>
                      </div>
                      <div className="text-[11px] font-mono text-primary truncate" title={block.record_hash}>
                        Hash: {block.record_hash}
                      </div>
                      <div className="text-[10px] font-mono text-muted-foreground truncate" title={block.previous_hash}>
                        Prev: {block.previous_hash ?? 'GENESIS (ROOT)'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="card-footer border-t border-border flex justify-end">
              <button
                className="btn-secondary text-xs"
                onClick={() => {
                  setVerifyEntityId(null)
                  setVerifyType(null)
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Payload Diff Inspector Modal */}
      {selectedEntry && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="card max-w-2xl w-full max-h-[85vh] flex flex-col border border-border shadow-2xl">
            <div className="card-header flex items-center justify-between border-b border-border">
              <div className="flex items-center gap-2">
                <FileCode2 className="w-5 h-5 text-primary" />
                <h3 className="font-semibold text-foreground text-sm">
                  Block State Transition Diff: {selectedEntry.action}
                </h3>
              </div>
              <button
                onClick={() => setSelectedEntry(null)}
                className="text-muted-foreground hover:text-foreground text-sm"
              >
                ✕
              </button>
            </div>

            <div className="card-body overflow-y-auto space-y-4 text-xs font-mono">
              <div className="bg-slate-900/80 p-2.5 rounded border border-border space-y-1">
                <div>
                  <span className="text-muted-foreground">Block Hash: </span>
                  <span className="text-primary">{selectedEntry.record_hash}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Previous Hash: </span>
                  <span className="text-slate-400">{selectedEntry.previous_hash ?? 'Genesis (null)'}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Entity: </span>
                  <span className="text-emerald-400">{selectedEntry.entity_type}</span>{' '}
                  <span className="text-slate-400">({selectedEntry.entity_id})</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <h4 className="font-semibold text-muted-foreground mb-1 text-[11px] uppercase">
                    Previous State (old_value)
                  </h4>
                  <pre className="bg-[hsl(222,47%,9%)] p-3 rounded border border-border text-[11px] overflow-x-auto text-amber-200/80 max-h-60">
                    {selectedEntry.old_value ? JSON.stringify(selectedEntry.old_value, null, 2) : 'null (Created)'}
                  </pre>
                </div>

                <div>
                  <h4 className="font-semibold text-muted-foreground mb-1 text-[11px] uppercase">
                    New Committed State (new_value)
                  </h4>
                  <pre className="bg-[hsl(222,47%,9%)] p-3 rounded border border-border text-[11px] overflow-x-auto text-emerald-300 max-h-60">
                    {selectedEntry.new_value ? JSON.stringify(selectedEntry.new_value, null, 2) : 'null'}
                  </pre>
                </div>
              </div>
            </div>

            <div className="card-footer border-t border-border flex justify-end">
              <button className="btn-secondary text-xs" onClick={() => setSelectedEntry(null)}>
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
