/**
 * src/pages/ExportsPage.tsx
 * Export profile configuration (P4-02).
 * Replaces bid/ui/export_wizard.py
 *
 * Loads profiles from GET /projects/{id}/export-profiles, lets the user
 * add / edit / delete profiles, and saves with PUT.
 */
import { useEffect, useState } from 'react'
import { Plus, Trash2, Save, Loader2 } from 'lucide-react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useProjectStore } from '@/store/projectStore'
import { exportsApi, type ExportProfile } from '@/lib/apiClient'
import { useToast } from '@/hooks/useToast'

const DEFAULT_PROFILE: ExportProfile = {
  size_type: 'longer',
  size: 1200,
  format: 'JPEG',
  quality: 85,
  ratio: null,
  logo: null,
  logo_required: false,
}

export default function ExportsPage() {
  const { selectedProject } = useProjectStore()
  const { toast: addToast } = useToast()
  const [profiles, setProfiles] = useState<Record<string, ExportProfile>>({})
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [newName, setNewName] = useState('')

  useEffect(() => {
    if (!selectedProject) return
    setLoading(true)
    exportsApi
      .getProfiles(selectedProject.id)
      .then((res) => setProfiles(res.data.profiles))
      .catch(() => addToast({ title: 'Failed to load export profiles', variant: 'destructive' }))
      .finally(() => setLoading(false))
  }, [selectedProject])

  function updateField<K extends keyof ExportProfile>(
    name: string,
    key: K,
    value: ExportProfile[K],
  ) {
    setProfiles((prev) => ({
      ...prev,
      [name]: { ...prev[name], [key]: value },
    }))
  }

  function addProfile() {
    const trimmed = newName.trim()
    if (!trimmed) return
    if (profiles[trimmed]) {
      addToast({ title: `Profile "${trimmed}" already exists`, variant: 'destructive' })
      return
    }
    setProfiles((prev) => ({ ...prev, [trimmed]: { ...DEFAULT_PROFILE } }))
    setNewName('')
  }

  function removeProfile(name: string) {
    setProfiles((prev) => {
      const copy = { ...prev }
      delete copy[name]
      return copy
    })
  }

  async function saveProfiles() {
    if (!selectedProject) return
    setSaving(true)
    try {
      await exportsApi.updateProfiles(selectedProject.id, { profiles })
      addToast({ title: 'Export profiles saved' })
    } catch {
      addToast({ title: 'Failed to save export profiles', variant: 'destructive' })
    } finally {
      setSaving(false)
    }
  }

  if (!selectedProject) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 text-muted-foreground">
        <p>No project selected. Select a project first.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Export Profiles</h1>
          <p className="text-muted-foreground">
            Configure output size, format, and quality for {selectedProject.name}
          </p>
        </div>
        <Button onClick={saveProfiles} disabled={saving}>
          {saving ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          {saving ? 'Savingâ€¦' : 'Save All'}
        </Button>
      </div>

      {loading && (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Profile cards */}
      {Object.entries(profiles).map(([name, profile]) => (
        <Card key={name}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg">{name}</CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => removeProfile(name)}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              {/* size_type */}
              <div className="space-y-1.5">
                <Label>Size Type</Label>
                <select
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={profile.size_type}
                  onChange={(e) =>
                    updateField(name, 'size_type', e.target.value as ExportProfile['size_type'])
                  }
                >
                  {(['longer', 'shorter', 'width', 'height'] as const).map((v) => (
                    <option key={v} value={v}>
                      {v}
                    </option>
                  ))}
                </select>
              </div>

              {/* size */}
              <div className="space-y-1.5">
                <Label>Size (px)</Label>
                <Input
                  type="number"
                  min={100}
                  max={10000}
                  value={profile.size}
                  onChange={(e) => updateField(name, 'size', Number(e.target.value))}
                />
              </div>

              {/* format */}
              <div className="space-y-1.5">
                <Label>Format</Label>
                <select
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={profile.format}
                  onChange={(e) =>
                    updateField(name, 'format', e.target.value as ExportProfile['format'])
                  }
                >
                  <option value="JPEG">JPEG</option>
                  <option value="PNG">PNG</option>
                </select>
              </div>

              {/* quality */}
              <div className="space-y-1.5">
                <Label>Quality (1â€“100)</Label>
                <Input
                  type="number"
                  min={1}
                  max={100}
                  value={profile.quality}
                  onChange={(e) => updateField(name, 'quality', Number(e.target.value))}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}

      {!loading && Object.keys(profiles).length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          No export profiles configured. Add one below.
        </div>
      )}

      {/* Add new profile */}
      <Card className="border-dashed">
        <CardContent className="pt-6">
          <div className="flex gap-2">
            <Input
              placeholder="New profile name (e.g. web)"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addProfile()}
              className="max-w-xs"
            />
            <Button variant="outline" onClick={addProfile} disabled={!newName.trim()}>
              <Plus className="mr-2 h-4 w-4" />
              Add Profile
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
