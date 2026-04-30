/**
 * src/lib/wsClient.ts
 * WebSocket client with heartbeat and auto-reconnect (P2-04, P3-05).
 * Connects to /api/v1/projects/{projectId}/ws?token=<jwt>
 */
import { useAuthStore } from '@/store/authStore'

export type WsMessageHandler = (msg: WsMessage) => void

export interface WsMessage {
  type: string
  [key: string]: unknown
}

export interface WsClientOptions {
  projectId: string
  onMessage: WsMessageHandler
  onConnect?: () => void
  onDisconnect?: () => void
  reconnectDelay?: number   // ms, default 3000
  maxReconnects?: number    // default unlimited
}

const WS_BASE =
  typeof window !== 'undefined'
    ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`
    : 'ws://localhost'

export class BidWebSocketClient {
  private ws: WebSocket | null = null
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private reconnectCount = 0
  private closed = false
  private pingTimer: ReturnType<typeof setInterval> | null = null

  constructor(private options: WsClientOptions) {}

  connect(): void {
    this.closed = false
    this._openSocket()
  }

  disconnect(): void {
    this.closed = true
    this._clearTimers()
    this.ws?.close()
    this.ws = null
  }

  private _buildUrl(): string {
    const { projectId } = this.options
    const token = useAuthStore.getState().accessToken ?? ''
    return `${WS_BASE}/api/v1/projects/${encodeURIComponent(projectId)}/ws?token=${encodeURIComponent(token)}`
  }

  private _openSocket(): void {
    try {
      this.ws = new WebSocket(this._buildUrl())
    } catch {
      this._scheduleReconnect()
      return
    }

    this.ws.onopen = () => {
      this.reconnectCount = 0
      this.options.onConnect?.()
      this._startPing()
    }

    this.ws.onmessage = (evt: MessageEvent<string>) => {
      try {
        const msg = JSON.parse(evt.data) as WsMessage
        if (msg.type === 'ping') {
          this.ws?.send(JSON.stringify({ type: 'pong' }))
          return
        }
        if (msg.type === 'server_closing') {
          const delay = typeof msg.reconnect_after === 'number'
            ? msg.reconnect_after * 1000
            : this.options.reconnectDelay ?? 3000
          this._scheduleReconnect(delay)
          return
        }
        this.options.onMessage(msg)
      } catch {
        // ignore parse errors
      }
    }

    this.ws.onerror = () => {
      // onclose will follow
    }

    this.ws.onclose = () => {
      this._clearTimers()
      this.options.onDisconnect?.()
      if (!this.closed) {
        this._scheduleReconnect()
      }
    }
  }

  private _startPing(): void {
    this.pingTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'pong' })) // respond to server pings
      }
    }, 25000)
  }

  private _clearTimers(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.pingTimer !== null) {
      clearInterval(this.pingTimer)
      this.pingTimer = null
    }
  }

  private _scheduleReconnect(delay?: number): void {
    const { maxReconnects, reconnectDelay = 3000 } = this.options
    if (maxReconnects !== undefined && this.reconnectCount >= maxReconnects) return
    const ms = delay ?? reconnectDelay
    this.reconnectTimer = setTimeout(() => {
      this.reconnectCount++
      this._openSocket()
    }, ms)
  }
}
