import type { LucideIcon } from 'lucide-react'
import { Package, CreditCard, Wrench, AlertTriangle, Flame } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ScenarioInfo } from '@/lib/api'

const ICON_BY_KEY: Record<string, LucideIcon> = {
  delayed_order: Package,
  refund_request: CreditCard,
  billing_dispute: AlertTriangle,
  technical_issue: Wrench,
  complex_escalation: Flame,
}

interface ScenarioPickerProps {
  scenarios: ScenarioInfo[]
  onSelect: (scenarioKey: string) => void
  disabled?: boolean
}

export function ScenarioPicker({ scenarios, onSelect, disabled }: ScenarioPickerProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-4xl">
      {scenarios.map((s) => {
        const Icon = ICON_BY_KEY[s.key] ?? Package
        return (
          <button
            key={s.key}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(s.key)}
            className={cn(
              'text-left rounded-xl border border-border bg-card p-4 transition-all',
              'hover:border-primary/50 hover:bg-primary/5',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
              disabled && 'opacity-50 pointer-events-none',
            )}
          >
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-primary/15 p-2.5 text-primary shrink-0">
                <Icon className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="font-semibold text-sm text-foreground">{s.name}</p>
                <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{s.description}</p>
              </div>
            </div>
          </button>
        )
      })}
    </div>
  )
}
