/**
 * src/components/layout/AppShell.tsx
 * Root layout wrapper — header + sidebar + main content area (P3-04).
 */
import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { Toaster } from '@/components/Toaster'

export function AppShell() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
      <Toaster />
    </div>
  )
}
