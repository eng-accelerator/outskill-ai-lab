import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Monitor } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { useSSE } from '@/hooks/use-sse'
import { useAutomationStore } from '@/stores/automation-store'
import { PhaseBar } from '@/components/phase-bar'
import { StepTimeline } from '@/components/step-timeline'

export function RunPage() {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const { task, status, phase, report, events, reset } = useAutomationStore()

  useSSE(runId)

  const isStreaming = status === 'running' || status === 'pending'

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-background/80 border-b border-border">
        <div className="flex items-center justify-between px-6 py-3">
          <div className="flex items-center gap-3">
            <button onClick={() => { reset(); navigate('/') }} className="p-1.5 rounded-lg hover:bg-muted transition-colors">
              <ArrowLeft className="h-4 w-4" />
            </button>
            <Monitor className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold tracking-tight">Browser Automation Agent</span>
          </div>
        </div>
        <div className="px-6 pb-3"><PhaseBar currentPhase={phase} /></div>
      </header>

      <main className="flex-1 flex gap-6 px-6 py-6 max-w-7xl mx-auto w-full">
        <div className="hidden lg:block w-80 shrink-0">
          <div className="sticky top-32"><StepTimeline events={events} /></div>
        </div>

        <div className="flex-1 min-w-0 max-w-3xl">
          <div className="mb-6">
            <h1 className="text-xl font-semibold mb-1">{task}</h1>
            <p className="text-sm text-muted-foreground">
              {isStreaming ? 'Automating...' : status === 'completed' ? 'Automation complete' : 'Starting...'}
            </p>
          </div>

          {report && (
            <article className="prose prose-invert prose-sm max-w-none prose-headings:text-foreground prose-p:text-foreground/90 prose-a:text-primary prose-code:text-primary prose-code:bg-primary/10 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-pre:bg-muted prose-pre:border prose-pre:border-border">
              <ReactMarkdown>{report}</ReactMarkdown>
            </article>
          )}

          {!report && isStreaming && (
            <div className="flex items-center gap-3 py-12 text-muted-foreground">
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="w-2 h-2 rounded-full bg-primary/60" style={{ animation: 'pulse-dot 1.4s ease-in-out infinite', animationDelay: `${i * 0.2}s` }} />
                ))}
              </div>
              <span className="text-sm">Browser agents are working on your task...</span>
            </div>
          )}

          {status === 'failed' && (
            <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3">
              <p className="text-sm text-destructive">Something went wrong. Please try again.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
