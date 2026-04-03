import { useState, type KeyboardEvent } from 'react'
import { ArrowRight, Search, X, Globe, GraduationCap, Newspaper, Code } from 'lucide-react'
import { cn } from '@/lib/utils'

const FOCUS_CHIPS = [
  { label: 'All', icon: Globe, active: true },
  { label: 'Academic', icon: GraduationCap, active: false },
  { label: 'News', icon: Newspaper, active: false },
  { label: 'Code', icon: Code, active: false },
] as const

interface SearchInputProps {
  onSubmit: (query: string) => void
  loading?: boolean
  initialQuery?: string
}

export function SearchInput({ onSubmit, loading = false, initialQuery = '' }: SearchInputProps) {
  const [query, setQuery] = useState(initialQuery)

  const handleSubmit = () => {
    const trimmed = query.trim()
    if (trimmed && !loading) {
      onSubmit(trimmed)
    }
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
        <Search className="absolute left-4 top-4 h-5 w-5 text-muted-foreground shrink-0" />

        <textarea
          className={cn(
            'w-full bg-transparent pl-12 pr-20 py-3.5 text-foreground',
            'placeholder:text-muted-foreground resize-none outline-none',
            'text-base leading-relaxed min-h-[52px] max-h-[200px]',
          )}
          placeholder="Ask anything..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={loading}
        />

        <div className="absolute right-3 top-3 flex items-center gap-1.5">
          {query && (
            <button
              onClick={() => setQuery('')}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          )}
          <button
            onClick={handleSubmit}
            disabled={!query.trim() || loading}
            className={cn(
              'p-2 rounded-lg transition-all duration-200',
              query.trim() && !loading
                ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                : 'bg-muted text-muted-foreground cursor-not-allowed',
            )}
          >
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2 mt-3 px-1">
        {FOCUS_CHIPS.map((chip) => (
          <button
            key={chip.label}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors',
              chip.active
                ? 'bg-primary/15 text-primary border border-primary/30'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted border border-transparent',
            )}
          >
            <chip.icon className="h-3.5 w-3.5" />
            {chip.label}
          </button>
        ))}
      </div>
    </div>
  )
}
