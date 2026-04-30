/**
 * src/store/projectStore.ts
 * Zustand store for project/session state (P3-05, P4-01).
 */
import { create } from 'zustand'

export interface Project {
  id: string
  name: string
  source_folder: string
  export_folder: string
  created_at: string
}

interface ProjectState {
  projects: Project[]
  selectedProject: Project | null
  isLoading: boolean
  error: string | null
  setProjects: (projects: Project[]) => void
  selectProject: (project: Project | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useProjectStore = create<ProjectState>((set) => ({
  projects: [],
  selectedProject: null,
  isLoading: false,
  error: null,

  setProjects: (projects) => set({ projects }),
  selectProject: (project) => set({ selectedProject: project }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}))
