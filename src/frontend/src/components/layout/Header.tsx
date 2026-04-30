/**
 * src/components/layout/Header.tsx
 * Application header with user menu (P3-04).
 */
import { Link, useNavigate } from 'react-router-dom'
import { LogOut, User, Settings, LayoutDashboard } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/store/authStore'
import { toast } from '@/hooks/useToast'

export function Header() {
  const { user, logout, isAuthenticated } = useAuthStore()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    toast({ title: 'Logged out', description: 'You have been signed out.' })
    navigate('/login')
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center px-4 gap-4">
        <Link to="/" className="flex items-center gap-2 font-bold text-lg">
          <LayoutDashboard className="h-5 w-5" />
          <span>BID</span>
        </Link>

        <div className="flex-1" />

        {isAuthenticated() && (
          <div className="flex items-center gap-2">
            <Link to="/settings">
              <Button variant="ghost" size="icon" title="Settings">
                <Settings className="h-4 w-4" />
              </Button>
            </Link>

            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <User className="h-4 w-4" />
              <span>{user?.username ?? 'User'}</span>
            </div>

            <Button variant="ghost" size="sm" onClick={handleLogout}>
              <LogOut className="h-4 w-4 mr-1" />
              Logout
            </Button>
          </div>
        )}
      </div>
    </header>
  )
}
