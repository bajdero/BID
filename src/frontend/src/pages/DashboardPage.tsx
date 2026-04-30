/**
 * src/pages/DashboardPage.tsx
 * Main dashboard — shows active project summary and quick actions.
 */
import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { FolderOpen, ImagePlus, Loader2 } from 'lucide-react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useProjectStore } from '@/store/projectStore'
import { useAuthStore } from '@/store/authStore'
import { projectsApi } from '@/lib/apiClient'

export default function DashboardPage() {
  const { user } = useAuthStore()
  const { projects, selectedProject, setProjects, setLoading, isLoading } = useProjectStore()

  useEffect(() => {
    setLoading(true)
    projectsApi
      .list()
      .then((res) => setProjects(res.data))
      .catch(() => {/* ignore */})
      .finally(() => setLoading(false))
  }, [setLoading, setProjects])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome back, {user?.username ?? 'User'}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Project</CardTitle>
            <FolderOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {selectedProject ? (
              <>
                <p className="text-2xl font-bold">{selectedProject.name}</p>
                <p className="text-xs text-muted-foreground truncate mt-1">
                  {selectedProject.source_folder}
                </p>
              </>
            ) : (
              <>
                <p className="text-sm text-muted-foreground">No project selected</p>
                <Button asChild size="sm" className="mt-2">
                  <Link to="/projects">Select a project</Link>
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Projects</CardTitle>
            <FolderOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <p className="text-2xl font-bold">{projects.length}</p>
            )}
            <p className="text-xs text-muted-foreground mt-1">Total projects</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Quick Actions</CardTitle>
            <ImagePlus className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent className="space-y-2">
            <Button asChild variant="outline" size="sm" className="w-full">
              <Link to="/projects">Manage Projects</Link>
            </Button>
            {selectedProject && (
              <Button asChild size="sm" className="w-full">
                <Link to="/processing">Start Processing</Link>
              </Button>
            )}
          </CardContent>
        </Card>
      </div>

      {selectedProject && (
        <Card>
          <CardHeader>
            <CardTitle>Project: {selectedProject.name}</CardTitle>
            <CardDescription>
              Source: {selectedProject.source_folder} → Export:{' '}
              {selectedProject.export_folder}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex gap-2">
            <Button asChild>
              <Link to="/sources">Browse Sources</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link to="/exports">Export Config</Link>
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
