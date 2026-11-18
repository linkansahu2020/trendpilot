import type { ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/cn'

type ToggleProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'onChange'> & {
  checked?: boolean
  onCheckedChange: (checked: boolean) => void
}

function Toggle({
  checked = false,
  onCheckedChange,
  className,
  ...props
}: ToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      {...props}
      onClick={() => onCheckedChange(!checked)}
      className={cn(
        'relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition duration-150',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30 focus-visible:ring-offset-2',
        'disabled:cursor-not-allowed disabled:opacity-50',
        checked ? 'bg-primary' : 'bg-border',
        className,
      )}
    >
      <span
        aria-hidden
        className={cn(
          'pointer-events-none size-5 rounded-full bg-canvas shadow-sm transition duration-150',
          checked ? 'translate-x-[22px]' : 'translate-x-0.5',
        )}
      />
    </button>
  )
}

export { Toggle, type ToggleProps }
