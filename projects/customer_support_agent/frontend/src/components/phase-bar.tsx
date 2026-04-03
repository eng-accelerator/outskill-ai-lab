import {
  Inbox,
  Package,
  CreditCard,
  Wrench,
  AlertTriangle,
  LifeBuoy,
  CheckCircle2,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { SupportPhase } from '@/stores/support-store'

const PHASES: { key: SupportPhase; label: string; icon: typeof Inbox }[] = [
  { key: 'intake', label: 'Intake', icon: Inbox },
  { key: 'order_support', label: 'Orders', icon: Package },
  { key: 'billing_support', label: 'Billing', icon: CreditCard },
  { key: 'technical_support', label: 'Technical', icon: Wrench },
  { key: 'escalation', label: 'Escalation', icon: AlertTriangle },
  { key: 'resolution', label: 'Resolution', icon: LifeBuoy },
  { key: 'completed', label: 'Done', icon: CheckCircle2 },
]

interface PhaseBarProps {
  currentPhase: SupportPhase
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
