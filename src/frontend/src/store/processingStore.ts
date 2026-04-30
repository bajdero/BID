/**
 * src/store/processingStore.ts
 * Zustand store for image processing queue state (P4-03).
 * Updated via WebSocket messages.
 */
import { create } from 'zustand'

export type PhotoStatus = 'new' | 'processing' | 'done' | 'error' | 'skipped'

export interface QueueItem {
  id: string
  photo: string
  folder: string
  status: PhotoStatus
  progress?: number
  error?: string
  startedAt?: string
  completedAt?: string
}

export interface QueueMetrics {
  queue_length: number
  active_workers: number
  max_workers: number
  completed_total: number
  failed_total: number
  utilization_pct: number
}

interface ProcessingState {
  queue: QueueItem[]
  metrics: QueueMetrics | null
  isProcessing: boolean
  upsertQueueItem: (item: QueueItem) => void
  updateQueueItem: (id: string, updates: Partial<QueueItem>) => void
  setMetrics: (metrics: QueueMetrics) => void
  setIsProcessing: (active: boolean) => void
  clearQueue: () => void
}

export const useProcessingStore = create<ProcessingState>((set) => ({
  queue: [],
  metrics: null,
  isProcessing: false,

  upsertQueueItem: (item) =>
    set((state) => {
      const idx = state.queue.findIndex((q) => q.id === item.id)
      if (idx >= 0) {
        const updated = [...state.queue]
        updated[idx] = item
        return { queue: updated }
      }
      return { queue: [...state.queue, item] }
    }),

  updateQueueItem: (id, updates) =>
    set((state) => ({
      queue: state.queue.map((item) =>
        item.id === id ? { ...item, ...updates } : item,
      ),
    })),

  setMetrics: (metrics) => set({ metrics }),
  setIsProcessing: (isProcessing) => set({ isProcessing }),
  clearQueue: () => set({ queue: [] }),
}))
