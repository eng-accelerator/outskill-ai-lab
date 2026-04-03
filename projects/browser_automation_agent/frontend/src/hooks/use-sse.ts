import { useEffect, useRef } from 'react'
import { useAutomationStore } from '@/stores/automation-store'
import { getStreamUrl } from '@/lib/api'

export function useSSE(runId: string | undefined) {
  const sourceRef = useRef<EventSource | null>(null)
  const { addEvent, setPhase, setReport, setStatus } = useAutomationStore()

  useEffect(() => {
    if (!runId) return

    const es = new EventSource(getStreamUrl(runId))
    sourceRef.current = es

    const handle = (type: string) => (e: MessageEvent) => {
      const data = JSON.parse(e.data)
      if (type === 'phase_change') setPhase(data.phase)
      if (type === 'report') setReport(data.content)
      addEvent({ type, ...data, timestamp: Date.now() })
    }

    for (const evt of ['phase_change', 'agent_start', 'agent_end', 'tool_start', 'tool_end', 'handoff', 'report']) {
      es.addEventListener(evt, handle(evt))
    }

    es.addEventListener('done', () => {
      setStatus('completed')
      setPhase('completed')
      addEvent({ type: 'done', timestamp: Date.now() })
      es.close()
    })

    es.addEventListener('error', () => {
      if (es.readyState === EventSource.CLOSED) return
      setStatus('failed')
      es.close()
    })

    return () => { es.close(); sourceRef.current = null }
  }, [runId, addEvent, setPhase, setReport, setStatus])
}
