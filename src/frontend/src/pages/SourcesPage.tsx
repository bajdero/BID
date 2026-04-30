/**
 * src/pages/SourcesPage.tsx
 * Source tree panel — lists source photos for the selected project (P4-04).
 * Replaces bid/ui/source_tree.py
 */
import { useEffect, useState } from 'react'
import { Loader2, Image, FileImage, ChevronRight, ChevronDown } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useProjectStore } from '@/store/projectStore'
import { sourcesApi, type SourceTree, type PhotoEntry } from '@/lib/apiClient'
import { toast } from '@/hooks/useToast'
import { cn } from '@/lib/utils'

const STATE_COLOUR: Record<string, string> = {
  new: 'text-blue-500',
  processing: 'text-yellow-500',
  ok: 'text-green-500',
  ok_old: 'text-green-400',
  error: 'text-red-500',
  export_fail: 'text-orange-500',
  skip: 'text-muted-foreground',
  deleted: 'text-muted-foreground',
  downloading: 'text-yellow-400',
}

export default function SourcesPage() {
  const { selectedProject } = useProjectStore()
  const [tree, setTree] = useState<SourceTree>({ folders: {} })
  const [isLoading, setIsLoading] = useState(false)
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())
  const [selectedPhoto, setSelectedPhoto] = useState<PhotoEntry | null>(null)
  const [selectedPhotoName, setSelectedPhotoName] = useState<string>('')

  useEffect(() => {
    if (!selectedProject) return
    setIsLoading(true)
    sourcesApi
      .getTree(selectedProject.id)
      .then((res) => {
        setTree(res.data)
        const firstFolder = Object.keys(res.data.folders)[0]
        if (firstFolder) setExpandedFolders(new Set([firstFolder]))
      })
      .catch(() =>
        toast({ title: 'Error', description: 'Failed to load sources', variant: 'destructive' }),
      )
      .finally(() => setIsLoading(false))
  }, [selectedProject])

  if (!selectedProject) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[40vh] gap-2 text-center">
        <FileImage className="h-12 w-12 text-muted-foreground" />
        <p className="text-muted-foreground">Select a project to browse sources</p>
      </div>
    )
  }

  const folderNames = Object.keys(tree.folders)
  const totalPhotos = Object.values(tree.folders).reduce(
    (sum, folder) => sum + Object.keys(folder).length,
    0,
  )

  function toggleFolder(folder: string) {
    setExpandedFolders((prev) => {
      const next = new Set(prev)
      next.has(folder) ? next.delete(folder) : next.add(folder)
      return next
    })
  }

  function selectPhoto(entry: PhotoEntry, filename: string) {
    setSelectedPhoto(entry)
    setSelectedPhotoName(filename)
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Source Tree</h1>
        <p className="text-muted-foreground">
          {totalPhotos} photo{totalPhotos !== 1 ? 's' : ''} in {folderNames.length} folder
          {folderNames.length !== 1 ? 's' : ''}
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {/* Tree panel */}
        <div className="lg:col-span-2 space-y-1">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : folderNames.length === 0 ? (
            <p className="text-muted-foreground text-center py-12">
              No source photos found.
            </p>
          ) : (
            folderNames.map((folder) => {
              const items = tree.folders[folder]
              const expanded = expandedFolders.has(folder)
              const fileNames = Object.keys(items)
              return (
                <div key={folder}>
                  <button
                    type="button"
                    onClick={() => toggleFolder(folder)}
                    className="flex items-center gap-1.5 w-full text-left px-2 py-1.5 rounded-md hover:bg-accent text-sm font-medium"
                  >
                    {expanded ? (
                      <ChevronDown className="h-4 w-4 shrink-0" />
                    ) : (
                      <ChevronRight className="h-4 w-4 shrink-0" />
                    )}
                    <span className="truncate">{folder}</span>
                    <span className="ml-auto text-xs text-muted-foreground shrink-0">
                      {fileNames.length}
                    </span>
                  </button>
                  {expanded && (
                    <div className="ml-4 space-y-0.5">
                      {fileNames.map((filename) => {
                        const photo = items[filename]
                        return (
                          <button
                            type="button"
                            key={photo.hash_id}
                            onClick={() => selectPhoto(photo, filename)}
                            className={cn(
                              'flex items-center gap-2 w-full text-left px-2 py-1 rounded-md text-sm hover:bg-accent',
                              selectedPhoto?.hash_id === photo.hash_id && 'bg-accent',
                            )}
                          >
                            <Image className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                            <span className="flex-1 truncate">{filename}</span>
                            <span
                              className={cn(
                                'text-xs shrink-0',
                                STATE_COLOUR[photo.state] ?? 'text-muted-foreground',
                              )}
                            >
                              {photo.state}
                            </span>
                          </button>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>

        {/* Details panel (P4-05 preview) */}
        <div>
          {selectedPhoto ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm break-all">{selectedPhotoName}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">State</span>
                  <span className={cn('font-medium', STATE_COLOUR[selectedPhoto.state])}>
                    {selectedPhoto.state}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Path</span>
                  <span className="truncate ml-4 max-w-[160px]">{selectedPhoto.path}</span>
                </div>
                {selectedPhoto.size && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Size</span>
                    <span>{selectedPhoto.size}</span>
                  </div>
                )}
                {selectedPhoto.created && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Created</span>
                    <span className="text-xs">{selectedPhoto.created}</span>
                  </div>
                )}
                {selectedPhoto.event_name && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Event</span>
                    <span className="text-xs truncate ml-4">{selectedPhoto.event_name}</span>
                  </div>
                )}
                {selectedPhoto.error_msg && (
                  <div className="text-xs text-destructive mt-2">{selectedPhoto.error_msg}</div>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground text-sm">
                Select a photo to view details
              </CardContent>
            </Card>
          )}

          <div className="mt-3">
            <Button asChild className="w-full" variant="outline">
              <a href="/files" target="_blank" rel="noopener noreferrer">
                Open in FileBrowser
              </a>
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
