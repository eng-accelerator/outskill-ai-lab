const API_BASE = '/api/research'

export interface StartResearchResponse {
  run_id: string
  status: string
}

export interface SourcePayload {
  url: string
  title: string
  source_type: string
  snippet: string
  relevance_score: number
}

export interface ResearchResult {
  run_id: string
  status: string
  query: string
  report: string
  sources: SourcePayload[]
}

export async function startResearch(query: string): Promise<StartResearchResponse> {
  const res = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(`Failed to start research: ${err}`)
  }
  return res.json()
}

export async function getResearchResult(runId: string): Promise<ResearchResult> {
  const res = await fetch(`${API_BASE}/${runId}`)
  if (!res.ok) {
    const err = await res.text()
    throw new Error(`Failed to get result: ${err}`)
  }
  return res.json()
}

export function getStreamUrl(runId: string): string {
  return `${API_BASE}/${runId}/stream`
}
