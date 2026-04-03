const API_BASE = '/api/incident'

export interface StartIncidentResponse {
  run_id: string
  status: string
}

export interface ScenarioInfo {
  scenario_type: string
  description: string
}

export async function listScenarios(): Promise<ScenarioInfo[]> {
  const res = await fetch(`${API_BASE}/scenarios`)
  return res.json()
}

export async function startIncident(scenarioType: string): Promise<StartIncidentResponse> {
  const res = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario_type: scenarioType }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export function getStreamUrl(runId: string): string {
  return `${API_BASE}/${runId}/stream`
}
