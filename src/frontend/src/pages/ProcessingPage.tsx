/**
 * src/pages/ProcessingPage.tsx
 * Image processing queue with real-time WebSocket status updates (P4-03).
 * Replaces bid/ui/preview.py queue functionality.
 */
import { useEffect, useRef, useState } from 'react'
import { Play, RotateCcw, Loader2, Wifi, WifiOff } from 'lucide-react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { useProjectStore } from '@/store/projectStore'
import { useProcessingStore, type PhotoStatus } from '@/store/processingStore'
import { processingApi } from '@/lib/apiClient'
import { BidWebSocketClient, type WsMessage } from '@/lib/wsClient'
import { toast } from '@/hooks/useToast'
import { cn } from '@/lib/utils'

const STATUS_LABEL: Record<PhotoStatus, string> = {
  new: 'Pending',
  processing: 'Processing…',
  done: 'Done',
  error: 'Error',
  skipped: 'Skipped',
}

const STATUS_COLOUR: Record<PhotoStatus, string> = {
  new: 'text-muted-foreground',
  processing: 'text-yellow-500',
  done: 'text-green-500',
  error: 'text-red-500',
  skipped: 'text-muted-foreground',
}

export default function ProcessingPage() {
  const { selectedProject } = useProjectStore()
  const { queue, metrics, upsertQueueItem, updateQueueItem, setMetrics, setIsProcessing, isProcessing, clearQueue } =
    useProcessingStore()

  const [wsConnected, setWsConnected] = useState(false)
  const [isEnqueuing, setIsEnqueuing] = useState(false)
  const wsRef = useRef<BidWebSocketClient | null>(null)

  // Connect WebSocket when a project is selected
  useEffect(() => {
    if (!selectedProject) return

    const client = new BidWebSocketClient({
      projectId: selectedProject.id,
      reconnectDelay: 3000,
      onConnect: () => setWsConnected(true),
      onDisconnect: () => setWsConnected(false),
      onMessage: (msg: WsMessage) => {
        switch (msg.type) {
          case 'state_change': {
            const { photo, folder, new_state } = msg as {
              photo: string
              folder: string
              new_state: string
            }
            upsertQueueItem({
              id: `${folder}/${photo}`,
              photo: photo as string,
              folder: folder as string,
              status: new_state as PhotoStatus,
            })
            if (new_state === 'processing') setIsProcessing(true)
            break
          }
          case 'progress': {
            const { photo, folder, status } = msg as {
              photo: string
              folder: string
              status: string
            }
            updateQueueItem(`${folder}/${photo}`, { status: status as PhotoStatus })
            if (status === 'completed' || status === 'failed') {
              // Check if all done
              const allDone = queue.every((q) => q.status === 'done' || q.status === 'error' || q.status === 'skipped')
              if (allDone) setIsProcessing(false)
            }
            break
          }
          case 'queue_metrics': {
            setMetrics(msg as unknown as typeof metrics)
            break
          }
          case 'error': {
            toast({
              title: 'Processing error',
              description: String(msg.message ?? 'Unknown error'),
              variant: 'destructive',
            })
            break
          }
        }
      },
    })

    wsRef.current = client
    client.connect()

    return () => {
      client.disconnect()
      wsRef.current = null
    }
  }, [selectedProject, upsertQueueItem, updateQueueItem, setMetrics, setIsProcessing, queue])

  async function handleEnqueueAll() {
    if (!selectedProject) return
    setIsEnqueuing(true)
    clearQueue()
    try {
      const res = await processingApi.enqueueAll(selectedProject.id)
      setIsProcessing(true)
      toast({
        title: 'Processing started',
        description: `${res.data.queued} photo(s) enqueued`,
      })
    } catch {
      toast({ title: 'Error', description: 'Failed to start processing', variant: 'destructive' })
    } finally {
      setIsEnqueuing(false)
    }
  }

  async function handleReset() {
    if (!selectedProject) return
    clearQueue()
    setIsProcessing(false)
    toast({ title: 'Queue cleared', description: 'Client queue cleared (photos keep their state)' })
  }

  if (!selectedProject) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[40vh] gap-2 text-center">
        <p className="text-muted-foreground">Select a project to start processing</p>
      </div>
    )
  }

  const doneCount = queue.filter((q) => q.status === 'done').length
  const totalCount = queue.length
  const progress = totalCount > 0 ? (doneCount / totalCount) * 100 : 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Processing</h1>
          <p className="text-muted-foreground">{selectedProject.name}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={cn('flex items-center gap-1 text-xs', wsConnected ? 'text-green-500' : 'text-muted-foreground')}>
            {wsConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
            {wsConnected ? 'Live' : 'Offline'}
          </span>
          <Button variant="outline" size="sm" onClick={handleReset} disabled={isProcessing}>
            <RotateCcw className="h-4 w-4 mr-1" />
            Reset
          </Button>
          <Button size="sm" onClick={handleEnqueueAll} disabled={isEnqueuing || isProcessing}>
            {isEnqueuing ? (
              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <Play className="h-4 w-4 mr-1" />
            )}
            {isProcessing ? 'Processing…' : 'Start Processing'}
          </Button>
        </div>
      </div>

      {/* Metrics */}
      {metrics && (
        <div className="grid gap-4 md:grid-cols-4">
          {[
            { label: 'Queue', value: metrics.queue_length },
            { label: 'Active', value: metrics.active_workers },
            { label: 'Completed', value: metrics.completed_total },
            { label: 'Failed', value: metrics.failed_total },
          ].map(({ label, value }) => (
            <Card key={label}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">{label}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{value}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Progress bar */}
      {totalCount > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>
              {doneCount} / {totalCount} completed
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Progress value={progress} className="h-3" />
          </CardContent>
        </Card>
      )}

      {/* Queue table */}
      <Card>
        <CardHeader>
          <CardTitle>Queue</CardTitle>
          <CardDescription>
            {queue.length === 0
              ? 'No items in queue. Click "Start Processing" to enqueue photos.'
              : `${queue.length} item(s)`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {queue.length > 0 && (
            <div className="rounded-md border overflow-auto max-h-[500px]">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-background">
                  <tr className="border-b">
                    <th className="text-left py-2 px-3 font-medium text-muted-foreground">Photo</th>
                    <th className="text-left py-2 px-3 font-medium text-muted-foreground">Folder</th>
                    <th className="text-right py-2 px-3 font-medium text-muted-foreground">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {queue.map((item) => (
                    <tr key={item.id} className="border-b last:border-0">
                      <td className="py-2 px-3 truncate max-w-[200px]">{item.photo}</td>
                      <td className="py-2 px-3 truncate max-w-[160px] text-muted-foreground">
                        {item.folder}
                      </td>
                      <td
                        className={cn(
                          'py-2 px-3 text-right font-medium',
                          STATUS_COLOUR[item.status],
                        )}
                      >
                        {item.status === 'processing' ? (
                          <span className="flex items-center justify-end gap-1">
                            <Loader2 className="h-3 w-3 animate-spin" />
                            {STATUS_LABEL[item.status]}
                          </span>
                        ) : (
                          STATUS_LABEL[item.status]
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
