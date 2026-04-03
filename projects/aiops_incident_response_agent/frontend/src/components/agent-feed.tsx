import {
  Activity,
  Cpu,
  Wrench,
  ArrowRightLeft,
  CheckCircle2,
  AlertCircle,
  CircleDot,
  FileText,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { TimelineEvent } from '@/stores/incident-store'

const ICON_MAP: Record<string, typeof Cpu> = {
  agent_start: Cpu,
  agent_end: CheckCircle2,
  tool_start: Wrench,
  tool_end: Wrench,
  handoff: ArrowRightLeft,
  phase_change: CircleDot,
  report: FileText,
  done: CheckCircle2,
  error: AlertCircle,
}

const COLOR_MAP: Record<string, string> = {
  agent_start: 'text-orange-400',
  agent_end: 'text-green-400',
  tool_start: 'text-amber-400',
  tool_end: 'text-amber-400/50',
  handoff: 'text-orange-300',
  phase_change: 'text-orange-500',
  report: 'text-green-400',
  done: 'text-green-500',
  error: 'text-red-400',
}

function eventLabel(e: TimelineEvent): string {
  switch (e.type) {
    case 'agent_start':
      return `${e.agent_name ?? 'Agent'} started`
    case 'agent_end':
      return `${e.agent_name ?? 'Agent'} completed`
    case 'tool_start':
      return `${e.agent_name ?? 'Agent'} → ${e.detail ?? 'tool'}`
    case 'tool_end':
      return `${e.detail ?? 'Tool'} done`
    case 'handoff':
      return e.detail ?? 'Handoff'
    case 'phase_change':
      return `Phase: ${e.phase ?? '—'}`
    case 'done':
      return 'Pipeline complete'
    case 'error':
      return e.message ?? 'Error'
    default:
      return e.type
  }
}

interface AgentFeedProps {
  events: TimelineEvent[]
}

export function AgentFeed({ events }: AgentFeedProps) {
  return (
    <div className="border border-border rounded-lg bg-card overflow-hidden">
      <div className="px-4 py-3 border-b border-border flex items-center gap-2">
        <Activity className="h-4 w-4 text-primary" />
        <span className="text-sm font-medium">Agent activity</span>
        <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full ml-auto">
          {events.length}
        </span>
      </div>
      <div className="max-h-[500px] overflow-y-auto p-4">
        <div className="relative pl-6 space-y-1">
          <div className="absolute left-2.5 top-2 bottom-2 w-px bg-border" />
          {events.map((event, i) => {
            const Icon = ICON_MAP[event.type] ?? CircleDot
            const color = COLOR_MAP[event.type] ?? 'text-muted-foreground'
            return (
              <div key={i} className="relative flex items-center gap-2 py-1 animate-fade-in-up">
                <div className="absolute -left-6 w-5 h-5 rounded-full bg-background flex items-center justify-center border border-border">
                  <Icon className={cn('h-3 w-3', color)} />
                </div>
                <span className={cn('text-xs', color)}>{eventLabel(event)}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
