import {
  Bell,
  KeyRound,
  Network,
  Radar,
  Shield,
  FileText,
  CheckCircle2,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ThreatPhase } from '@/stores/threat-store'

const PHASES: { key: ThreatPhase; label: string; icon: typeof Bell }[] = [
  { key: 'alert_intake', label: 'Alert Intake', icon: Bell },
  { key: 'auth_analysis', label: 'Auth Analysis', icon: KeyRound },
  { key: 'network_analysis', label: 'Network Analysis', icon: Network },
  { key: 'threat_intel', label: 'Threat Intel', icon: Radar },
  { key: 'containment', label: 'Containment', icon: Shield },
  { key: 'soc_reporting', label: 'SOC Report', icon: FileText },
  { key: 'completed', label: 'Done', icon: CheckCircle2 },
]

interface PhaseBarProps {
  currentPhase: ThreatPhase
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
