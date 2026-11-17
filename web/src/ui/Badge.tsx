import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from './cn'

export type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  children: ReactNode
  tone?: 'default' | 'accent'
  showDot?: boolean
}

export function Badge({
  children,
  tone = 'default',
  showDot = false,
  className,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium tracking-wide',
        tone === 'accent'
          ? 'border-primary/20 bg-primary-soft text-primary'
          : 'border-primary/20 bg-canvas text-muted',
        className,
      )}
      {...props}
    >
      {showDot ? (
        <span
          aria-hidden
          className="size-1.5 rounded-full bg-primary"
        />
      ) : null}
      {children}
    </span>
  )
}
