import { ExternalLink, Globe } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { SourcePayload } from '@/lib/api'

const SOURCE_TYPE_COLORS: Record<string, string> = {
  web: 'bg-blue-500/15 text-blue-400',
  academic: 'bg-purple-500/15 text-purple-400',
  news: 'bg-amber-500/15 text-amber-400',
  wikipedia: 'bg-slate-500/15 text-slate-400',
  reddit: 'bg-orange-500/15 text-orange-400',
  github: 'bg-gray-500/15 text-gray-400',
  stackexchange: 'bg-emerald-500/15 text-emerald-400',
  youtube: 'bg-red-500/15 text-red-400',
}

function getDomain(url: string): string {
  try {
    return new URL(url).hostname.replace('www.', '')
  } catch {
    return url
  }
}

interface SourceCardProps {
  source: SourcePayload
  index: number
}

export function SourceCard({ source, index }: SourceCardProps) {
  const domain = getDomain(source.url)

  return (
    <a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        'group flex flex-col gap-2 p-3 rounded-lg border border-border',
        'bg-card hover:border-primary/40 transition-all duration-200',
        'min-w-[220px] max-w-[280px] shrink-0',
        'animate-fade-in-up',
      )}
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <div className="flex items-center gap-2">
        <div className="flex items-center justify-center w-5 h-5 rounded bg-muted">
          <Globe className="h-3 w-3 text-muted-foreground" />
        </div>
        <span className="text-[11px] font-mono text-muted-foreground uppercase tracking-wider truncate">
          {domain}
        </span>
        <ExternalLink className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity ml-auto shrink-0" />
      </div>

      <p className="text-sm font-medium text-foreground line-clamp-2 leading-snug">
        {source.title || domain}
      </p>

      {source.snippet && (
        <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
          {source.snippet}
        </p>
      )}

      <div className="flex items-center justify-between mt-auto">
        <span className={cn(
          'text-[10px] font-medium px-2 py-0.5 rounded-full',
          SOURCE_TYPE_COLORS[source.source_type] ?? 'bg-muted text-muted-foreground',
        )}>
          {source.source_type}
        </span>
        <span className="text-[10px] text-muted-foreground font-mono">
          [{index + 1}]
        </span>
      </div>
    </a>
  )
}

interface SourceCardListProps {
  sources: SourcePayload[]
}

export function SourceCardList({ sources }: SourceCardListProps) {
  if (sources.length === 0) return null

  return (
    <div className="w-full">
      <h3 className="text-sm font-medium text-muted-foreground mb-3 px-1">
        Sources ({sources.length})
      </h3>
      <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin">
        {sources.map((source, i) => (
          <SourceCard key={`${source.url}-${i}`} source={source} index={i} />
        ))}
      </div>
    </div>
  )
}
