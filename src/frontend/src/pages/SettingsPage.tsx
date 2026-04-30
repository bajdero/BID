/**
 * src/pages/SettingsPage.tsx
 * Settings and preferences panel (P4-04).
 * Replaces bid/ui/setup_wizard.py
 */
import { useState } from 'react'
import { Moon, Sun, Monitor } from 'lucide-react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/store/authStore'

type Theme = 'light' | 'dark' | 'system'

export default function SettingsPage() {
  const { user } = useAuthStore()
  const [theme, setTheme] = useState<Theme>('system')

  function applyTheme(t: Theme) {
    setTheme(t)
    const root = document.documentElement
    if (t === 'dark') root.classList.add('dark')
    else if (t === 'light') root.classList.remove('dark')
    else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      prefersDark ? root.classList.add('dark') : root.classList.remove('dark')
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Application preferences and account info</p>
      </div>

      {/* Account */}
      <Card>
        <CardHeader>
          <CardTitle>Account</CardTitle>
          <CardDescription>Your profile information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Username</span>
            <span className="font-medium">{user?.username ?? '—'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Email</span>
            <span className="font-medium">{user?.email ?? '—'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Role</span>
            <span className="font-medium">{user?.is_admin ? 'Admin' : 'User'}</span>
          </div>
        </CardContent>
      </Card>

      {/* Theme — P4-06 */}
      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>Choose your preferred colour scheme</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            {([
              ['light', 'Light', Sun],
              ['dark', 'Dark', Moon],
              ['system', 'System', Monitor],
            ] as const).map(([value, label, Icon]) => (
              <Button
                key={value}
                variant={theme === value ? 'default' : 'outline'}
                size="sm"
                onClick={() => applyTheme(value)}
                className="flex items-center gap-1.5"
              >
                <Icon className="h-4 w-4" />
                {label}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* FileBrowser */}
      <Card>
        <CardHeader>
          <CardTitle>File Management</CardTitle>
          <CardDescription>
            Browse, upload, and manage files using the integrated FileBrowser.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild variant="outline">
            <a href="/files" target="_blank" rel="noopener noreferrer">
              Open FileBrowser
            </a>
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
