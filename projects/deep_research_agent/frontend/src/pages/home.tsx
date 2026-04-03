import { useNavigate } from 'react-router-dom'
import { Sparkles } from 'lucide-react'
import { SearchInput } from '@/components/search-input'
import { useResearchStore } from '@/stores/research-store'
import { startResearch } from '@/lib/api'
import { useState } from 'react'

const EXAMPLE_QUERIES = [
  'What are the latest advances in quantum computing?',
  'Compare transformer vs. diffusion architectures for AI',
  'How does CRISPR gene editing work and what are its applications?',
  'Explain the economic impact of AI automation on employment',
]

export function HomePage() {
  const navigate = useNavigate()
  const { reset, setRunId, setQuery } = useResearchStore()
  const [loading, setLoading] = useState(false)

  const handleSearch = async (query: string) => {
    setLoading(true)
    reset()
    setQuery(query)

    const { run_id } = await startResearch(query)
    setRunId(run_id)
    navigate(`/research/${run_id}`)
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          <span className="text-sm font-semibold tracking-tight">Deep Research Agent</span>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-6 pb-32">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold tracking-tight mb-3">
            Research anything.
          </h1>
          <p className="text-muted-foreground text-lg max-w-md mx-auto">
            Get comprehensive, citation-backed answers from multiple sources across the web.
          </p>
        </div>

        <SearchInput onSubmit={handleSearch} loading={loading} />

        <div className="mt-12 w-full max-w-2xl">
          <p className="text-xs text-muted-foreground mb-3 px-1">Try asking</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {EXAMPLE_QUERIES.map((q) => (
              <button
                key={q}
                onClick={() => handleSearch(q)}
                disabled={loading}
                className="text-left text-sm text-muted-foreground hover:text-foreground px-4 py-3 rounded-lg border border-border hover:border-primary/30 bg-card hover:bg-muted/50 transition-all duration-200"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </main>

      <footer className="text-center py-4 text-xs text-muted-foreground">
        Outskill AI Lab &middot; Deep Research Agent
      </footer>
    </div>
  )
}
