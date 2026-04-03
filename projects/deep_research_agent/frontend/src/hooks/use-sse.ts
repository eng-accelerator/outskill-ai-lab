import { useEffect, useRef } from 'react'
import { useResearchStore } from '@/stores/research-store'
import { getStreamUrl } from '@/lib/api'

export function useSSE(runId: string | undefined) {
  const sourceRef = useRef<EventSource | null>(null)
  const {
    addEvent,
    setPhase,
    setReport,
    setSources,
    setStatus,
  } = useResearchStore()

  useEffect(() => {
    if (!runId) return

    const url = getStreamUrl(runId)
    const es = new EventSource(url)
    sourceRef.current = es

    es.addEventListener('phase_change', (e) => {
      const data = JSON.parse(e.data)
      setPhase(data.phase)
      addEvent({ type: 'phase_change', ...data, timestamp: Date.now() })
    })

    es.addEventListener('agent_start', (e) => {
      const data = JSON.parse(e.data)
      addEvent({ type: 'agent_start', ...data, timestamp: Date.now() })
    })

    es.addEventListener('agent_end', (e) => {
      const data = JSON.parse(e.data)
      addEvent({ type: 'agent_end', ...data, timestamp: Date.now() })
    })

    es.addEventListener('tool_start', (e) => {
      const data = JSON.parse(e.data)
      addEvent({ type: 'tool_start', ...data, timestamp: Date.now() })
    })

    es.addEventListener('tool_end', (e) => {
      const data = JSON.parse(e.data)
      addEvent({ type: 'tool_end', ...data, timestamp: Date.now() })
    })

    es.addEventListener('handoff', (e) => {
      const data = JSON.parse(e.data)
      addEvent({ type: 'handoff', ...data, timestamp: Date.now() })
    })

    es.addEventListener('report', (e) => {
      const data = JSON.parse(e.data)
      setReport(data.content)
      setSources(data.sources ?? [])
      addEvent({ type: 'report', timestamp: Date.now() })
    })

    es.addEventListener('done', () => {
      setStatus('completed')
      setPhase('completed')
      addEvent({ type: 'done', timestamp: Date.now() })
      es.close()
    })

    es.addEventListener('error', (e) => {
      if (es.readyState === EventSource.CLOSED) return
      const data = e instanceof MessageEvent ? JSON.parse(e.data) : {}
      setStatus('failed')
      addEvent({ type: 'error', message: data.message ?? 'Connection lost', timestamp: Date.now() })
      es.close()
    })

    return () => {
      es.close()
      sourceRef.current = null
    }
  }, [runId, addEvent, setPhase, setReport, setSources, setStatus])
}
