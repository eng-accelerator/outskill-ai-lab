import { Lightbulb, Navigation, MousePointer, Eye, CheckCircle2, FileText, Shield } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Phase } from '@/stores/automation-store'

const PHASES: { key: Phase; label: string; icon: typeof Lightbulb }[] = [
  { key: 'planning', label: 'Plan', icon: Lightbulb },
  { key: 'navigating', label: 'Navigate', icon: Navigation },
  { key: 'interacting', label: 'Interact', icon: MousePointer },
  { key: 'extracting', label: 'Extract', icon: Eye },
  { key: 'validating', label: 'Validate', icon: Shield },
  { key: 'reporting', label: 'Report', icon: FileText },
  { key: 'completed', label: 'Done', icon: CheckCircle2 },
]

interface PhaseBarProps {
  currentPhase: Phase
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
            <div className={cn(
              'flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs font-medium transition-all',
              isActive && 'text-primary bg-primary/15',
              isPast && 'text-primary/60 bg-primary/5',
              !isActive && !isPast && 'text-muted-foreground/50',
            )}>
              <Icon className={cn('h-3.5 w-3.5', isActive && 'animate-pulse')} />
              <span>{phase.label}</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
