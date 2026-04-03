const API_BASE = '/api/automation'

export interface StartAutomationResponse {
  run_id: string
  status: string
}

export interface ScenarioInfo {
  key: string
  name: string
  task: string
}

export interface AutomationResult {
  run_id: string
  status: string
  task: string
  report: string
  urls_visited: string[]
  steps_completed: number
  total_steps: number
}

export async function listScenarios(): Promise<ScenarioInfo[]> {
  const res = await fetch(`${API_BASE}/scenarios`)
  return res.json()
}

export async function startAutomation(task: string, scenario?: string): Promise<StartAutomationResponse> {
  const res = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task, scenario }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export function getStreamUrl(runId: string): string {
  return `${API_BASE}/${runId}/stream`
}
