/**
 * src/pages/ProjectsPage.tsx
 * Project/session selector — lists projects and allows selection (P4-01).
 * Replaces bid/ui/project_selector.py
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FolderOpen, Plus, Trash2, Loader2, CheckCircle2 } from 'lucide-react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useProjectStore, type Project } from '@/store/projectStore'
import { projectsApi } from '@/lib/apiClient'
import { toast } from '@/hooks/useToast'
import { cn } from '@/lib/utils'

export default function ProjectsPage() {
  const { projects, selectedProject, setProjects, selectProject, isLoading, setLoading } =
    useProjectStore()
  const navigate = useNavigate()

  const [showCreateForm, setShowCreateForm] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newName, setNewName] = useState('')
  const [newSource, setNewSource] = useState('')
  const [newExport, setNewExport] = useState('')

  useEffect(() => {
    setLoading(true)
    projectsApi
      .list()
      .then((res) => setProjects(res.data))
      .catch(() => toast({ title: 'Error', description: 'Failed to load projects', variant: 'destructive' }))
      .finally(() => setLoading(false))
  }, [setLoading, setProjects])

  function handleSelect(project: Project) {
    selectProject(project)
    toast({ title: `Project selected`, description: project.name })
    navigate('/')
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setCreating(true)
    try {
      const res = await projectsApi.create({
        name: newName,
        source_folder: newSource,
        export_folder: newExport,
      })
      setProjects([...projects, res.data])
      setShowCreateForm(false)
      setNewName('')
      setNewSource('')
      setNewExport('')
      toast({ title: 'Project created', description: res.data.name })
    } catch {
      toast({ title: 'Error', description: 'Failed to create project', variant: 'destructive' })
    } finally {
      setCreating(false)
    }
  }

  async function handleDelete(project: Project) {
    try {
      await projectsApi.delete(project.id)
      const updated = projects.filter((p) => p.id !== project.id)
      setProjects(updated)
      if (selectedProject?.id === project.id) selectProject(null)
      toast({ title: 'Project deleted', description: project.name })
    } catch {
      toast({ title: 'Error', description: 'Failed to delete project', variant: 'destructive' })
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
          <p className="text-muted-foreground">Select or manage your BID projects</p>
        </div>
        <Button onClick={() => setShowCreateForm((v) => !v)}>
          <Plus className="h-4 w-4 mr-2" />
          New Project
        </Button>
      </div>

      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create Project</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="pname">Project name</Label>
                <Input
                  id="pname"
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="My Project"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="psource">Source folder path</Label>
                <Input
                  id="psource"
                  required
                  value={newSource}
                  onChange={(e) => setNewSource(e.target.value)}
                  placeholder="/data/source/my-project"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="pexport">Export folder path</Label>
                <Input
                  id="pexport"
                  required
                  value={newExport}
                  onChange={(e) => setNewExport(e.target.value)}
                  placeholder="/data/export/my-project"
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={creating}>
                  {creating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Create
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowCreateForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Card
              key={project.id}
              className={cn(
                'cursor-pointer transition-colors hover:border-primary/60',
                selectedProject?.id === project.id && 'border-primary ring-1 ring-primary',
              )}
            >
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <FolderOpen className="h-5 w-5 shrink-0" />
                    <CardTitle className="text-base">{project.name}</CardTitle>
                  </div>
                  {selectedProject?.id === project.id && (
                    <CheckCircle2 className="h-5 w-5 text-primary shrink-0" />
                  )}
                </div>
                <CardDescription className="truncate text-xs">
                  {project.source_folder}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex gap-2">
                <Button size="sm" onClick={() => handleSelect(project)} className="flex-1">
                  {selectedProject?.id === project.id ? 'Active' : 'Select'}
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => handleDelete(project)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          ))}

          {projects.length === 0 && (
            <div className="col-span-3 text-center py-12 text-muted-foreground">
              No projects yet. Create one to get started.
            </div>
          )}
        </div>
      )}
    </div>
  )
}
