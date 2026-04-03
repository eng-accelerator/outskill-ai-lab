import { useEffect } from 'react'
import type { ThreatPhase, TimelineEvent } from '@/stores/threat-store'
import { useThreatStore } from '@/stores/threat-store'
import { getStreamUrl } from '@/lib/api'

export function useSSE(runId: string | undefined) {
  const { addEvent, setPhase, setReport, setStatus } = useThreatStore()

  useEffect(() => {
    if (!runId) return

    const es = new EventSource(getStreamUrl(runId))

    const handle = (type: string) => (e: MessageEvent) => {
      const data = JSON.parse(e.data) as Record<string, unknown>
      if (type === 'phase_change' && typeof data.phase === 'string') {
        setPhase(data.phase as ThreatPhase)
      }
      if (type === 'report' && typeof data.content === 'string') {
        setReport(data.content)
      }
      addEvent({ type, ...data, timestamp: Date.now() } as TimelineEvent)
    }

    for (const evt of [
      'phase_change',
      'agent_start',
      'agent_end',
      'tool_start',
      'tool_end',
      'handoff',
      'report',
    ]) {
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

    return () => {
      es.close()
    }
  }, [runId, addEvent, setPhase, setReport, setStatus])
}
