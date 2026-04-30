/**
 * src/lib/apiClient.ts
 * Axios-based API client that automatically injects the JWT Bearer token
 * from the Zustand auth store and handles token refresh (P3-05).
 */
import axios, {
  type AxiosError,
  type InternalAxiosRequestConfig,
} from 'axios'
import { useAuthStore } from '@/store/authStore'

const BASE_URL = '/api/v1'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ---- Request interceptor: attach access token ----
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ---- Response interceptor: handle 401 with silent refresh ----
let isRefreshing = false
let pendingRequests: Array<(token: string) => void> = []

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retried?: boolean
    }

    if (error.response?.status === 401 && !originalRequest._retried) {
      originalRequest._retried = true

      if (!isRefreshing) {
        isRefreshing = true
        const { refreshToken, setTokens, logout } = useAuthStore.getState()

        try {
          const res = await axios.post(`${BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })
          const { access_token, refresh_token } = res.data
          setTokens(access_token, refresh_token)
          pendingRequests.forEach((cb) => cb(access_token))
          pendingRequests = []
          isRefreshing = false
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return apiClient(originalRequest)
        } catch {
          logout()
          isRefreshing = false
          pendingRequests = []
          return Promise.reject(error)
        }
      }

      // Queue concurrent requests until refresh completes
      return new Promise((resolve) => {
        pendingRequests.push((token: string) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          resolve(apiClient(originalRequest))
        })
      })
    }

    return Promise.reject(error)
  },
)

// ---- Typed API helpers ----

export interface LoginPayload {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export const authApi = {
  login: (payload: LoginPayload) =>
    apiClient.post<TokenResponse>('/auth/login', payload),
  refresh: (refreshToken: string) =>
    apiClient.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    }),
}

export interface ProjectResponse {
  id: string
  name: string
  path: string
  last_modified: string
  photo_count: number
  source_folder: string
  export_folder: string
}

export const projectsApi = {
  list: () => apiClient.get<ProjectResponse[]>('/projects'),
  get: (id: string) => apiClient.get<ProjectResponse>(`/projects/${id}`),
  create: (data: { name: string; source_folder: string; export_folder: string }) =>
    apiClient.post<ProjectResponse>('/projects', data),
  delete: (id: string) => apiClient.delete(`/projects/${id}`),
}

export interface PhotoEntry {
  hash_id: string
  path: string
  state: 'downloading' | 'new' | 'processing' | 'ok' | 'ok_old' | 'error' | 'export_fail' | 'deleted' | 'skip'
  exported: Record<string, string>
  description: string
  tags: string[]
  size: string
  size_bytes: number
  created: string
  mtime: number
  exif: Record<string, string>
  quality_score: number | null
  quality_model: 'exif_rules' | 'ml' | null
  error_msg: string | null
  duration_sec: number | null
  event_folder: string | null
  event_id: string | null
  event_name: string | null
}

export interface SourceTree {
  folders: Record<string, Record<string, PhotoEntry>>
}

export const sourcesApi = {
  getTree: (projectId: string) =>
    apiClient.get<SourceTree>(`/projects/${projectId}/sources`),
  getPhoto: (projectId: string, folder: string, photo: string) =>
    apiClient.get<PhotoEntry>(`/projects/${projectId}/sources/${folder}/${photo}`),
}

export interface ExportProfile {
  size_type: 'longer' | 'width' | 'height' | 'shorter'
  size: number
  format: 'JPEG' | 'PNG'
  quality: number
  ratio: [number, number] | null
  logo: Record<string, unknown> | null
  logo_required: boolean
}

export interface ExportProfilesResponse {
  profiles: Record<string, ExportProfile>
}

export const exportsApi = {
  getProfiles: (projectId: string) =>
    apiClient.get<ExportProfilesResponse>(`/projects/${projectId}/export-profiles`),
  updateProfiles: (projectId: string, data: ExportProfilesResponse) =>
    apiClient.put<ExportProfilesResponse>(`/projects/${projectId}/export-profiles`, data),
  validateProfile: (projectId: string, name: string, profile: ExportProfile) =>
    apiClient.post<{ valid: boolean; errors: string[] }>(
      `/projects/${projectId}/export-profiles/validate`,
      { name, profile },
    ),
}

export interface ProcessResponse {
  task_id: string
  queued: number
  skipped: number
  message: string
}

export interface ProcessStatusResponse {
  queue_length: number
  active: Array<{ folder: string; photo: string; state: string; profile: string | null }>
  completed: number
  failed: number
}

export const processingApi = {
  enqueue: (projectId: string, photos: Array<[string, string]>, profiles?: string[]) =>
    apiClient.post<ProcessResponse>(`/projects/${projectId}/process`, {
      photos,
      profiles: profiles ?? null,
    }),
  enqueueAll: (projectId: string) =>
    apiClient.post<ProcessResponse>(`/projects/${projectId}/process/all`),
  getStatus: (projectId: string) =>
    apiClient.get<ProcessStatusResponse>(`/projects/${projectId}/process/status`),
  resetPhoto: (projectId: string, folder: string, photo: string) =>
    apiClient.delete(`/projects/${projectId}/process/${folder}/${photo}`),
}

export const systemApi = {
  health: () => apiClient.get<{ status: string }>('/health'),
  version: () => apiClient.get<{ api_version: string; bid_version: string }>('/version'),
}
