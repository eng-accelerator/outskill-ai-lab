import { useNavigate } from 'react-router-dom'
import { Monitor, Globe, FormInput } from 'lucide-react'
import { TaskInput, ScenarioCard } from '@/components/task-input'
import { useAutomationStore } from '@/stores/automation-store'
import { startAutomation } from '@/lib/api'
import { useState } from 'react'

const SCENARIOS = [
  { key: '1', name: 'Web Scraping -- Hacker News', task: 'Extract the top 10 posts from Hacker News including title, URL, and points for each post.', icon: Globe },
  { key: '2', name: 'Form Automation -- Google Search', task: "Go to Google, search for 'Python browser automation', and extract the first 5 search results with title and URL.", icon: FormInput },
]

export function HomePage() {
  const navigate = useNavigate()
  const { reset, setRunId, setTask } = useAutomationStore()
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (task: string, scenario?: string) => {
    setLoading(true)
    reset()
    setTask(task)
    const { run_id } = await startAutomation(task, scenario)
    setRunId(run_id)
    navigate(`/run/${run_id}`)
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-2">
          <Monitor className="h-5 w-5 text-primary" />
          <span className="text-sm font-semibold tracking-tight">Browser Automation Agent</span>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-6 pb-32">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold tracking-tight mb-3">Automate the browser.</h1>
          <p className="text-muted-foreground text-lg max-w-md mx-auto">
            Describe a task and let AI agents navigate, interact, and extract data for you.
          </p>
        </div>

        <TaskInput onSubmit={handleSubmit} loading={loading} />

        <div className="mt-12 w-full max-w-2xl">
          <p className="text-xs text-muted-foreground mb-3 px-1">Predefined scenarios</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {SCENARIOS.map((s) => (
              <ScenarioCard
                key={s.key}
                name={s.name}
                task={s.task}
                onSelect={() => handleSubmit(s.task, s.key)}
              />
            ))}
          </div>
        </div>
      </main>

      <footer className="text-center py-4 text-xs text-muted-foreground">
        Outskill AI Lab &middot; Browser Automation Agent
      </footer>
    </div>
  )
}
