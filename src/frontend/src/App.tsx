/**
 * src/App.tsx
 * Application root — React Router v6 client-side routing (P3-01, P3-02, P3-03).
 *
 * Route structure:
 *   /login          — public login page
 *   /               — protected: dashboard
 *   /projects       — protected: project selector
 *   /sources        — protected: source tree (requires active project)
 *   /processing     — protected: processing queue with WebSocket
 *   /exports        — protected: export profile wizard
 *   /settings       — protected: settings & preferences
 *   *               — 404 page
 */
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { RequireAuth } from '@/components/auth/RequireAuth'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import ProjectsPage from '@/pages/ProjectsPage'
import SourcesPage from '@/pages/SourcesPage'
import ProcessingPage from '@/pages/ProcessingPage'
import ExportsPage from '@/pages/ExportsPage'
import SettingsPage from '@/pages/SettingsPage'
import NotFoundPage from '@/pages/NotFoundPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected routes wrapped in AppShell + RequireAuth */}
        <Route element={<RequireAuth />}>
          <Route element={<AppShell />}>
            <Route index element={<DashboardPage />} />
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="sources" element={<SourcesPage />} />
            <Route path="processing" element={<ProcessingPage />} />
            <Route path="exports" element={<ExportsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Route>

        {/* 404 — catches all unmatched routes */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}
