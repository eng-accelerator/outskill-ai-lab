import { ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FollowUpSuggestionsProps {
  query: string
  onSelect: (question: string) => void
}

function generateFollowUps(query: string): string[] {
  const q = query.toLowerCase()

  const suggestions = [
    `What are the key limitations and challenges of ${query}?`,
    `How does ${query} compare to alternatives?`,
    `What are the latest developments in ${query}?`,
    `What are practical applications of ${query}?`,
  ]

  if (q.includes('ai') || q.includes('machine learning')) {
    suggestions[2] = `What ethical concerns surround ${query}?`
  }

  return suggestions.slice(0, 4)
}

export function FollowUpSuggestions({ query, onSelect }: FollowUpSuggestionsProps) {
  const suggestions = generateFollowUps(query)

  return (
    <div className="w-full mt-8 pt-6 border-t border-border">
      <h4 className="text-sm font-medium text-muted-foreground mb-3">Related</h4>
      <div className="flex flex-col gap-2">
        {suggestions.map((suggestion, i) => (
          <button
            key={i}
            onClick={() => onSelect(suggestion)}
            className={cn(
              'group flex items-center justify-between px-4 py-3 rounded-lg',
              'border border-border bg-card hover:border-primary/40',
              'transition-all duration-200 text-left',
            )}
          >
            <span className="text-sm text-foreground/80 group-hover:text-foreground transition-colors">
              {suggestion}
            </span>
            <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors shrink-0 ml-3" />
          </button>
        ))}
      </div>
    </div>
  )
}
