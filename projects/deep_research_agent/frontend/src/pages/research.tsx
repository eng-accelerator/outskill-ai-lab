import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Sparkles } from 'lucide-react'
import { useSSE } from '@/hooks/use-sse'
import { useResearchStore } from '@/stores/research-store'
import { PhaseIndicator } from '@/components/phase-indicator'
import { SourceCardList } from '@/components/source-card'
import { AgentTimeline } from '@/components/agent-timeline'
import { ResearchReport } from '@/components/research-report'
import { FollowUpSuggestions } from '@/components/follow-up-suggestions'
import { startResearch } from '@/lib/api'

export function ResearchPage() {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const {
    query,
    status,
    phase,
    report,
    sources,
    events,
    reset,
    setRunId,
    setQuery,
  } = useResearchStore()

  useSSE(runId)

  const isStreaming = status === 'running' || status === 'pending'
  const isCompleted = status === 'completed'

  const handleFollowUp = async (newQuery: string) => {
    reset()
    setQuery(newQuery)
    const { run_id } = await startResearch(newQuery)
    setRunId(run_id)
    navigate(`/research/${run_id}`)
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-background/80 border-b border-border">
        <div className="flex items-center justify-between px-6 py-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => { reset(); navigate('/') }}
              className="p-1.5 rounded-lg hover:bg-muted transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <span className="text-sm font-semibold tracking-tight">Deep Research Agent</span>
            </div>
          </div>
        </div>

        <div className="px-6 pb-3">
          <PhaseIndicator currentPhase={phase} />
        </div>
      </header>

      <main className="flex-1 flex gap-6 px-6 py-6 max-w-7xl mx-auto w-full">
        <div className="hidden lg:block w-80 shrink-0">
          <div className="sticky top-32 space-y-4">
            <AgentTimeline events={events} />
          </div>
        </div>

        <div className="flex-1 min-w-0 max-w-3xl">
          <div className="mb-6">
            <h1 className="text-xl font-semibold text-foreground mb-1">{query}</h1>
            <p className="text-sm text-muted-foreground">
              {isStreaming ? 'Researching...' : isCompleted ? 'Research complete' : 'Starting...'}
            </p>
          </div>

          {sources.length > 0 && (
            <div className="mb-8">
              <SourceCardList sources={sources} />
            </div>
          )}

          {(report || isStreaming) && (
            <ResearchReport
              content={report}
              isStreaming={isStreaming && !report}
            />
          )}

          {!report && isStreaming && (
            <div className="flex items-center gap-3 py-12 text-muted-foreground">
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    className="w-2 h-2 rounded-full bg-primary/60"
                    style={{
                      animation: 'pulse-dot 1.4s ease-in-out infinite',
                      animationDelay: `${i * 0.2}s`,
                    }}
                  />
                ))}
              </div>
              <span className="text-sm">Agents are working on your research...</span>
            </div>
          )}

          {status === 'failed' && (
            <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3">
              <p className="text-sm text-destructive">
                Something went wrong. Please try again.
              </p>
            </div>
          )}

          {isCompleted && report && (
            <FollowUpSuggestions query={query} onSelect={handleFollowUp} />
          )}
        </div>
      </main>

      <div className="lg:hidden fixed bottom-0 left-0 right-0 bg-background/80 backdrop-blur-xl border-t border-border p-4">
        <details className="text-sm">
          <summary className="cursor-pointer text-muted-foreground font-medium">
            Agent Activity ({events.length})
          </summary>
          <div className="mt-2 max-h-48 overflow-y-auto">
            <AgentTimeline events={events} />
          </div>
        </details>
      </div>
    </div>
  )
}
