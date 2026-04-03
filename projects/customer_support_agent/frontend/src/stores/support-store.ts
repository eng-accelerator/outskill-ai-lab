import { create } from 'zustand'

export type SupportPhase =
  | 'intake'
  | 'order_support'
  | 'billing_support'
  | 'technical_support'
  | 'escalation'
  | 'resolution'
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

interface SupportState {
  runId: string | null
  scenario: string
  status: RunStatus
  phase: SupportPhase
  report: string
  events: TimelineEvent[]

  setRunId: (id: string) => void
  setScenario: (scenario: string) => void
  setStatus: (status: RunStatus) => void
  setPhase: (phase: SupportPhase) => void
  setReport: (report: string) => void
  addEvent: (event: TimelineEvent) => void
  reset: () => void
}

const initialState = {
  runId: null,
  scenario: '',
  status: 'idle' as RunStatus,
  phase: 'intake' as SupportPhase,
  report: '',
  events: [] as TimelineEvent[],
}

export const useSupportStore = create<SupportState>((set) => ({
  ...initialState,
  setRunId: (runId) => set({ runId, status: 'pending' }),
  setScenario: (scenario) => set({ scenario }),
  setStatus: (status) => set({ status }),
  setPhase: (phase) =>
    set({ phase, status: phase === 'completed' ? 'completed' : 'running' }),
  setReport: (report) => set({ report }),
  addEvent: (event) => set((s) => ({ events: [...s.events, event] })),
  reset: () => set(initialState),
}))
