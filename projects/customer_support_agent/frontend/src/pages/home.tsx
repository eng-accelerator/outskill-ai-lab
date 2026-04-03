import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Headphones } from 'lucide-react'
import { ScenarioPicker } from '@/components/scenario-picker'
import { useSupportStore } from '@/stores/support-store'
import { listScenarios, startSupport } from '@/lib/api'

function scenarioTitle(key: string): string {
  if (!key) return ''
  return key
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

export function HomePage() {
  const navigate = useNavigate()
  const { reset, setRunId, setScenario } = useSupportStore()
  const [loading, setLoading] = useState(false)

  const { data: scenarios = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['support-scenarios'],
    queryFn: listScenarios,
    select: (rows) =>
      rows.map((s) => ({
        ...s,
        name: s.name || scenarioTitle(s.key),
      })),
  })

  const handleSelect = async (scenarioKey: string) => {
    setLoading(true)
    reset()
    setScenario(scenarioKey)
    const { run_id } = await startSupport(scenarioKey)
    setRunId(run_id)
    navigate(`/run/${run_id}`)
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="border-b border-border bg-card/40">
        <div className="max-w-5xl mx-auto px-6 py-5 flex items-center gap-3">
          <div className="rounded-lg bg-primary/15 p-2.5 text-primary">
            <Headphones className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-foreground">Customer Support Agent</h1>
            <p className="text-xs text-muted-foreground">Simulated tickets · multi-agent resolution</p>
          </div>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center px-6 py-12">
        <div className="text-center mb-10 max-w-xl">
          <h2 className="text-3xl font-bold tracking-tight mb-2">Pick a scenario</h2>
          <p className="text-muted-foreground text-sm leading-relaxed">
            Each card starts a support run with intake, specialized agents, and a streamed resolution report.
          </p>
        </div>

        {isLoading && (
          <p className="text-sm text-muted-foreground">Loading scenarios…</p>
        )}

        {isError && (
          <div className="text-center max-w-md">
            <p className="text-sm text-destructive mb-3">Could not load scenarios from the API.</p>
            <button
              type="button"
              onClick={() => refetch()}
              className="text-sm text-primary underline-offset-4 hover:underline"
            >
              Retry
            </button>
          </div>
        )}

        {!isLoading && !isError && (
          <ScenarioPicker scenarios={scenarios} onSelect={handleSelect} disabled={loading} />
        )}
      </main>

      <footer className="text-center py-6 text-xs text-muted-foreground border-t border-border">
        Outskill AI Lab · Customer Support Agent
      </footer>
    </div>
  )
}
