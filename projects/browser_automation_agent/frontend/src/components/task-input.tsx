import { useState, type KeyboardEvent } from 'react'
import { Play, Globe, Terminal } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TaskInputProps {
  onSubmit: (task: string) => void
  loading?: boolean
}

export function TaskInput({ onSubmit, loading = false }: TaskInputProps) {
  const [task, setTask] = useState('')

  const handleSubmit = () => {
    const trimmed = task.trim()
    if (trimmed && !loading) onSubmit(trimmed)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className={cn(
        'relative flex items-start rounded-xl border border-border bg-card',
        'transition-all duration-200',
        'focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/20',
        'shadow-lg shadow-black/20',
      )}>
        <Terminal className="absolute left-4 top-4 h-5 w-5 text-muted-foreground" />
        <textarea
          className="w-full bg-transparent pl-12 pr-16 py-3.5 text-foreground placeholder:text-muted-foreground resize-none outline-none text-base min-h-[52px] max-h-[200px]"
          placeholder="Describe what you want to automate..."
          value={task}
          onChange={(e) => setTask(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={loading}
        />
        <button
          onClick={handleSubmit}
          disabled={!task.trim() || loading}
          className={cn(
            'absolute right-3 top-3 p-2 rounded-lg transition-all',
            task.trim() && !loading
              ? 'bg-primary text-primary-foreground hover:bg-primary/90'
              : 'bg-muted text-muted-foreground cursor-not-allowed',
          )}
        >
          <Play className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}

interface ScenarioCardProps {
  name: string
  task: string
  onSelect: () => void
}

export function ScenarioCard({ name, task, onSelect }: ScenarioCardProps) {
  return (
    <button
      onClick={onSelect}
      className="text-left p-4 rounded-lg border border-border bg-card hover:border-primary/40 transition-all group"
    >
      <div className="flex items-center gap-2 mb-2">
        <Globe className="h-4 w-4 text-primary" />
        <span className="text-sm font-medium">{name}</span>
      </div>
      <p className="text-xs text-muted-foreground group-hover:text-foreground/70 transition-colors">
        {task}
      </p>
    </button>
  )
}
