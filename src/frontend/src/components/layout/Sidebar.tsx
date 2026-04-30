/**
 * src/components/layout/Sidebar.tsx
 * Navigation sidebar (P3-04).
 */
import { NavLink } from 'react-router-dom'
import {
  FolderOpen,
  ImagePlus,
  LayoutDashboard,
  Settings,
  TreePine,
  Download,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useProjectStore } from '@/store/projectStore'

interface NavItem {
  to: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  requiresProject?: boolean
}

const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/projects', label: 'Projects', icon: FolderOpen },
  { to: '/sources', label: 'Source Tree', icon: TreePine, requiresProject: true },
  { to: '/processing', label: 'Processing', icon: ImagePlus, requiresProject: true },
  { to: '/exports', label: 'Export', icon: Download, requiresProject: true },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export function Sidebar() {
  const { selectedProject } = useProjectStore()

  return (
    <aside className="hidden md:flex w-56 flex-col border-r bg-card">
      <nav className="flex flex-col gap-1 p-3 pt-4">
        {NAV_ITEMS.map(({ to, label, icon: Icon, requiresProject }) => {
          const disabled = requiresProject && !selectedProject
          return (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-accent text-accent-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                  disabled && 'pointer-events-none opacity-40',
                )
              }
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </NavLink>
          )
        })}
      </nav>

      {selectedProject && (
        <div className="mt-auto p-3 border-t">
          <p className="text-xs text-muted-foreground mb-1">Active project</p>
          <p className="text-sm font-medium truncate">{selectedProject.name}</p>
        </div>
      )}
    </aside>
  )
}
