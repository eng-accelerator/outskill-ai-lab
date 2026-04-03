import { Search, BookOpen, PenTool, GitMerge, Lightbulb, CheckCircle2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Phase } from '@/stores/research-store'

const PHASES: { key: Phase; label: string; icon: typeof Search }[] = [
  { key: 'planning', label: 'Planning', icon: Lightbulb },
  { key: 'searching', label: 'Searching', icon: Search },
  { key: 'reading', label: 'Reading', icon: BookOpen },
  { key: 'synthesizing', label: 'Synthesizing', icon: GitMerge },
  { key: 'writing', label: 'Writing', icon: PenTool },
  { key: 'completed', label: 'Complete', icon: CheckCircle2 },
]

const PHASE_COLORS: Record<Phase, string> = {
  planning: 'text-phase-planning',
  searching: 'text-phase-searching',
  reading: 'text-phase-reading',
  synthesizing: 'text-phase-synthesizing',
  writing: 'text-phase-writing',
  completed: 'text-phase-completed',
}

const PHASE_BG: Record<Phase, string> = {
  planning: 'bg-phase-planning/15',
  searching: 'bg-phase-searching/15',
  reading: 'bg-phase-reading/15',
  synthesizing: 'bg-phase-synthesizing/15',
  writing: 'bg-phase-writing/15',
  completed: 'bg-phase-completed/15',
}

interface PhaseIndicatorProps {
  currentPhase: Phase
}

export function PhaseIndicator({ currentPhase }: PhaseIndicatorProps) {
  const currentIndex = PHASES.findIndex((p) => p.key === currentPhase)

  return (
    <div className="flex items-center gap-1 overflow-x-auto pb-1">
      {PHASES.map((phase, i) => {
        const isActive = phase.key === currentPhase
        const isPast = i < currentIndex
        const Icon = phase.icon

        return (
          <div key={phase.key} className="flex items-center gap-1 shrink-0">
            {i > 0 && (
              <div className={cn(
                'w-6 h-px',
                isPast ? 'bg-phase-completed/50' : 'bg-border',
              )} />
            )}
            <div
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-300',
                isActive && [PHASE_COLORS[phase.key], PHASE_BG[phase.key]],
                isPast && 'text-phase-completed/70 bg-phase-completed/10',
                !isActive && !isPast && 'text-muted-foreground/50',
              )}
            >
              <Icon className={cn('h-3.5 w-3.5', isActive && 'animate-pulse')} />
              <span>{phase.label}</span>
              {isActive && currentPhase !== 'completed' && <LoadingDots />}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function LoadingDots() {
  return (
    <span className="inline-flex gap-0.5 ml-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-1 h-1 rounded-full bg-current"
          style={{
            animation: 'pulse-dot 1.4s ease-in-out infinite',
            animationDelay: `${i * 0.2}s`,
          }}
        />
      ))}
    </span>
  )
}
