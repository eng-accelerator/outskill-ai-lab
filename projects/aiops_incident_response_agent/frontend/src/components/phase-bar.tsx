import {
  Siren,
  ScrollText,
  BarChart3,
  GitBranch,
  Wrench,
  FileText,
  CheckCircle2,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { IncidentPhase } from '@/stores/incident-store'

const PHASES: { key: IncidentPhase; label: string; icon: typeof Siren }[] = [
  { key: 'triage', label: 'Triage', icon: Siren },
  { key: 'log_analysis', label: 'Log Analysis', icon: ScrollText },
  { key: 'metrics_analysis', label: 'Metrics Analysis', icon: BarChart3 },
  { key: 'root_cause_analysis', label: 'Root Cause Analysis', icon: GitBranch },
  { key: 'remediation', label: 'Remediation', icon: Wrench },
  { key: 'reporting', label: 'Reporting', icon: FileText },
  { key: 'completed', label: 'Done', icon: CheckCircle2 },
]

interface PhaseBarProps {
  currentPhase: IncidentPhase
}

export function PhaseBar({ currentPhase }: PhaseBarProps) {
  const currentIndex = PHASES.findIndex((p) => p.key === currentPhase)

  return (
    <div className="flex items-center gap-1 overflow-x-auto pb-1">
      {PHASES.map((phase, i) => {
        const isActive = phase.key === currentPhase
        const isPast = i < currentIndex
        const Icon = phase.icon
        return (
          <div key={phase.key} className="flex items-center gap-1 shrink-0">
            {i > 0 && <div className={cn('w-5 h-px', isPast ? 'bg-primary/50' : 'bg-border')} />}
            <div
              className={cn(
                'flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs font-medium transition-all',
                isActive && 'text-primary bg-primary/15',
                isPast && 'text-primary/60 bg-primary/5',
                !isActive && !isPast && 'text-muted-foreground/50',
              )}
            >
              <Icon className={cn('h-3.5 w-3.5', isActive && 'animate-pulse')} />
              <span>{phase.label}</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
