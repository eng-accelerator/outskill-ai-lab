import { create } from 'zustand'

export type IncidentPhase =
  | 'triage'
  | 'log_analysis'
  | 'metrics_analysis'
  | 'root_cause_analysis'
  | 'remediation'
  | 'reporting'
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

interface IncidentState {
  runId: string | null
  scenario: string
  status: RunStatus
  phase: IncidentPhase
  report: string
  events: TimelineEvent[]

  setRunId: (id: string) => void
  setScenario: (scenario: string) => void
  setStatus: (status: RunStatus) => void
  setPhase: (phase: IncidentPhase) => void
  setReport: (report: string) => void
  addEvent: (event: TimelineEvent) => void
  reset: () => void
}

const initialState = {
  runId: null,
  scenario: '',
  status: 'idle' as RunStatus,
  phase: 'triage' as IncidentPhase,
  report: '',
  events: [] as TimelineEvent[],
}

export const useIncidentStore = create<IncidentState>((set) => ({
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
