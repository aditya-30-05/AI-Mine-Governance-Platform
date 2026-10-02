import { useState, useEffect } from 'react'
import {
  LayoutDashboard, ClipboardList, AlertTriangle, CheckSquare,
  FileText, Map, Bell, Users, LogOut, ChevronDown, ShieldCheck,
  WifiOff, Wifi, RefreshCw, Menu, X, Building2, FileBarChart2
} from 'lucide-react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useMines } from '@/hooks/useApi'
import { useNotifications } from '@/hooks/useApi'
import { cn } from '@/utils'
import toast from 'react-hot-toast'
import { getPendingCount } from '@/offline/db'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/inspections', label: 'Inspections', icon: ClipboardList },
  { to: '/violations', label: 'Violations', icon: AlertTriangle },
  { to: '/tasks', label: 'Tasks', icon: CheckSquare },
  { to: '/documents', label: 'Documents', icon: FileText },
  { to: '/gis', label: 'GIS Map', icon: Map },
  { to: '/reports', label: 'Reports', icon: FileBarChart2 },
  { to: '/audit', label: 'Audit Trail', icon: ShieldCheck },
  { to: '/users', label: 'Users', icon: Users, adminOnly: true },
]

export default function AppLayout() {
  const navigate = useNavigate()
  const { user, selectedMineId, setMine, logout } = useAuthStore()
  const { data: mines } = useMines()
  const { data: notifData } = useNotifications()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [online, setOnline] = useState(navigator.onLine)
  const [pendingSync, setPendingSync] = useState(0)

  // Online/offline detection
  useEffect(() => {
    const onOnline = () => { setOnline(true); toast.success('Back online — syncing…') }
    const onOffline = () => { setOnline(false); toast.error('Offline mode — data saved locally') }
    window.addEventListener('online', onOnline)
    window.addEventListener('offline', onOffline)
    return () => { window.removeEventListener('online', onOnline); window.removeEventListener('offline', onOffline) }
  }, [])

  // Check pending sync
  useEffect(() => {
    const check = async () => setPendingSync(await getPendingCount())
    check()
    const interval = setInterval(check, 10_000)
    return () => clearInterval(interval)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const unreadCount = notifData?.unread_count ?? 0

  const filteredNav = NAV_ITEMS.filter(item =>
    !item.adminOnly || user?.role === 'admin'
  )

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className={cn(
        'flex flex-col border-r border-border bg-[hsl(222,47%,9%)] transition-all duration-200 z-20',
        sidebarOpen ? 'w-60' : 'w-14'
      )}>
        {/* Logo */}
        <div className="flex items-center gap-2 px-4 py-4 border-b border-border min-h-[57px]">
          <ShieldCheck className="w-6 h-6 text-primary shrink-0" />
          {sidebarOpen && (
            <div className="overflow-hidden">
              <p className="text-sm font-bold text-foreground truncate">CoalGov</p>
              <p className="text-xs text-muted-foreground truncate">Compliance System</p>
            </div>
          )}
          <button
            className="ml-auto text-muted-foreground hover:text-foreground"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>

        {/* Mine selector */}
        {sidebarOpen && mines && (
          <div className="px-3 py-2 border-b border-border">
            <label className="form-label text-xs">Active Mine</label>
            <select
              className="form-input text-xs py-1"
              value={selectedMineId ?? ''}
              onChange={(e) => setMine(e.target.value)}
            >
              <option value="">All Mines</option>
              {mines.map((m: { id: string; name: string }) => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Nav */}
        <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
          {filteredNav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn('sidebar-link', isActive && 'active', !sidebarOpen && 'justify-center px-2')
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              {sidebarOpen && <span className="truncate">{label}</span>}
              {!sidebarOpen && <span className="sr-only">{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Footer: sync status + user */}
        <div className="border-t border-border p-3 space-y-2">
          {/* Sync status */}
          <div className={cn('flex items-center gap-2 text-xs', online ? 'sync-synced' : 'sync-pending')}>
            {online ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
            {sidebarOpen && (
              <span>
                {online ? (pendingSync > 0 ? `Syncing ${pendingSync}…` : 'Online') : `Offline (${pendingSync} pending)`}
              </span>
            )}
          </div>

          {/* User */}
          {sidebarOpen ? (
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold text-primary shrink-0">
                {user?.full_name?.charAt(0) ?? '?'}
              </div>
              <div className="overflow-hidden flex-1 min-w-0">
                <p className="text-xs font-medium text-foreground truncate">{user?.full_name}</p>
                <p className="text-xs text-muted-foreground capitalize">{user?.role?.replace('_', ' ')}</p>
              </div>
              <button onClick={handleLogout} className="text-muted-foreground hover:text-foreground" title="Logout">
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button onClick={handleLogout} className="sidebar-link justify-center px-2 w-full" title="Logout">
              <LogOut className="w-4 h-4" />
            </button>
          )}
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex items-center justify-between px-5 py-3 border-b border-border bg-[hsl(222,47%,9%)] min-h-[57px]">
          <div className="flex items-center gap-3">
            <Building2 className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm text-foreground font-medium">
              {mines?.find((m: { id: string; name: string }) => m.id === selectedMineId)?.name ?? 'All Mines'}
            </span>
          </div>

          <div className="flex items-center gap-3">
            {/* Offline badge */}
            {!online && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-orange-950 text-orange-400 border border-orange-800">
                <WifiOff className="w-3 h-3" /> Offline
              </span>
            )}

            {/* Notifications */}
            <NavLink to="/notifications" className="relative text-muted-foreground hover:text-foreground">
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-600 rounded-full text-[10px] text-white flex items-center justify-center font-bold">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </NavLink>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-5">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
