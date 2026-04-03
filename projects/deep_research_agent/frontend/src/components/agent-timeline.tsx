import { useState } from 'react'
import {
  ChevronDown,
  ChevronRight,
  Cpu,
  Wrench,
  ArrowRightLeft,
  CircleDot,
  AlertCircle,
  CheckCircle2,
  Layers,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { TimelineEvent } from '@/stores/research-store'

const EVENT_CONFIG: Record<string, { icon: typeof Cpu; color: string; label: (e: TimelineEvent) => string }> = {
  agent_start: {
    icon: Cpu,
    color: 'text-blue-400',
    label: (e) => `${e.agent_name} started`,
  },
  agent_end: {
    icon: CheckCircle2,
    color: 'text-green-400',
    label: (e) => `${e.agent_name} completed`,
  },
  tool_start: {
    icon: Wrench,
    color: 'text-amber-400',
    label: (e) => `${e.agent_name} → ${e.detail}`,
  },
  tool_end: {
    icon: Wrench,
    color: 'text-amber-400/50',
    label: (e) => `${e.detail} done`,
  },
  handoff: {
    icon: ArrowRightLeft,
    color: 'text-purple-400',
    label: (e) => e.detail ?? 'Handoff',
  },
  phase_change: {
    icon: CircleDot,
    color: 'text-cyan-400',
    label: (e) => `Phase: ${e.phase}`,
  },
  report: {
    icon: Layers,
    color: 'text-green-400',
    label: () => 'Report generated',
  },
  done: {
    icon: CheckCircle2,
    color: 'text-green-500',
    label: () => 'Pipeline complete',
  },
  error: {
    icon: AlertCircle,
    color: 'text-red-400',
    label: (e) => e.message ?? 'Error occurred',
  },
}

interface AgentTimelineProps {
  events: TimelineEvent[]
}

export function AgentTimeline({ events }: AgentTimelineProps) {
  const [expanded, setExpanded] = useState(true)

  return (
    <div className="border border-border rounded-lg bg-card overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">Agent Activity</span>
          <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
            {events.length}
          </span>
        </div>
        {expanded ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        )}
      </button>

      {expanded && (
        <div className="px-4 pb-3 max-h-[400px] overflow-y-auto">
          <div className="relative pl-6 space-y-0.5">
            <div className="absolute left-2.5 top-2 bottom-2 w-px bg-border" />

            {events.map((event, i) => {
              const config = EVENT_CONFIG[event.type]
              if (!config) return null
              const Icon = config.icon

              return (
                <div
                  key={i}
                  className="relative flex items-center gap-2 py-1 animate-fade-in-up"
                  style={{ animationDelay: `${Math.min(i * 30, 300)}ms` }}
                >
                  <div className={cn(
                    'absolute -left-6 w-5 h-5 rounded-full bg-background flex items-center justify-center',
                    'border border-border',
                  )}>
                    <Icon className={cn('h-3 w-3', config.color)} />
                  </div>
                  <span className={cn('text-xs', config.color)}>
                    {config.label(event)}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
