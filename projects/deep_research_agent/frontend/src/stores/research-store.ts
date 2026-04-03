import { create } from 'zustand'
import type { SourcePayload } from '@/lib/api'

export type Phase =
  | 'planning'
  | 'searching'
  | 'reading'
  | 'synthesizing'
  | 'writing'
  | 'completed'

export type RunStatus = 'idle' | 'pending' | 'running' | 'completed' | 'failed'

export interface TimelineEvent {
  type: string
  agent_name?: string
  detail?: string
  phase?: string
  message?: string
  timestamp: number
}

interface ResearchState {
  runId: string | null
  query: string
  status: RunStatus
  phase: Phase
  report: string
  sources: SourcePayload[]
  events: TimelineEvent[]

  setRunId: (id: string) => void
  setQuery: (query: string) => void
  setStatus: (status: RunStatus) => void
  setPhase: (phase: Phase) => void
  setReport: (report: string) => void
  setSources: (sources: SourcePayload[]) => void
  addEvent: (event: TimelineEvent) => void
  reset: () => void
}

const initialState = {
  runId: null,
  query: '',
  status: 'idle' as RunStatus,
  phase: 'planning' as Phase,
  report: '',
  sources: [] as SourcePayload[],
  events: [] as TimelineEvent[],
}

export const useResearchStore = create<ResearchState>((set) => ({
  ...initialState,
  setRunId: (runId) => set({ runId, status: 'pending' }),
  setQuery: (query) => set({ query }),
  setStatus: (status) => set({ status }),
  setPhase: (phase) => set({ phase, status: phase === 'completed' ? 'completed' : 'running' }),
  setReport: (report) => set({ report }),
  setSources: (sources) => set({ sources }),
  addEvent: (event) => set((s) => ({ events: [...s.events, event] })),
  reset: () => set(initialState),
}))
