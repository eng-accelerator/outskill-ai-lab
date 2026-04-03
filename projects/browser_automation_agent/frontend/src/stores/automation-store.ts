import { create } from 'zustand'

export type Phase = 'planning' | 'navigating' | 'interacting' | 'extracting' | 'validating' | 'reporting' | 'completed'
export type RunStatus = 'idle' | 'pending' | 'running' | 'completed' | 'failed'

export interface TimelineEvent {
  type: string
  agent_name?: string
  detail?: string
  phase?: string
  message?: string
  timestamp: number
}

interface AutomationState {
  runId: string | null
  task: string
  status: RunStatus
  phase: Phase
  report: string
  events: TimelineEvent[]

  setRunId: (id: string) => void
  setTask: (task: string) => void
  setStatus: (status: RunStatus) => void
  setPhase: (phase: Phase) => void
  setReport: (report: string) => void
  addEvent: (event: TimelineEvent) => void
  reset: () => void
}

const initialState = {
  runId: null,
  task: '',
  status: 'idle' as RunStatus,
  phase: 'planning' as Phase,
  report: '',
  events: [] as TimelineEvent[],
}

export const useAutomationStore = create<AutomationState>((set) => ({
  ...initialState,
  setRunId: (runId) => set({ runId, status: 'pending' }),
  setTask: (task) => set({ task }),
  setStatus: (status) => set({ status }),
  setPhase: (phase) => set({ phase, status: phase === 'completed' ? 'completed' : 'running' }),
  setReport: (report) => set({ report }),
  addEvent: (event) => set((s) => ({ events: [...s.events, event] })),
  reset: () => set(initialState),
}))
