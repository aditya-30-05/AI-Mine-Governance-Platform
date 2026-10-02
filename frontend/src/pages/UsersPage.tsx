import { Users } from 'lucide-react'
import { useUsers } from '@/hooks/useApi'

export default function UsersPage() {
  const { data, isLoading } = useUsers()
  const users = Array.isArray(data) ? data : []

  return (
    <div className="space-y-4 animate-fade-in">
      <div>
        <h1 className="text-xl font-bold text-foreground">Users</h1>
        <p className="text-sm text-muted-foreground">{users.length} registered users</p>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr><th>Name</th><th>Employee ID</th><th>Email</th><th>Role</th><th>Department</th><th>Status</th></tr>
            </thead>
            <tbody>
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>{Array.from({ length: 6 }).map((_, j) => <td key={j}><div className="skeleton h-4 w-full" /></td>)}</tr>
                ))
              ) : users.map((u: any) => (
                <tr key={u.id}>
                  <td className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold text-primary shrink-0">
                      {u.full_name?.charAt(0) ?? '?'}
                    </div>
                    {u.full_name}
                  </td>
                  <td className="font-mono text-xs">{u.employee_id}</td>
                  <td className="text-xs">{u.email}</td>
                  <td><span className="badge-verified capitalize">{u.role?.replace('_', ' ')}</span></td>
                  <td className="text-sm">{u.department ?? '—'}</td>
                  <td><span className={u.is_active ? 'badge-low' : 'badge-critical'}>{u.is_active ? 'Active' : 'Inactive'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
