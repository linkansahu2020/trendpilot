import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from './cn'

export type CardProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode
  elevated?: boolean
}

export function Card({
  children,
  elevated = false,
  className,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        'rounded-lg border border-border bg-canvas p-8 shadow-[var(--shadow-card)]',
        elevated && 'shadow-[var(--shadow-cta)] ring-1 ring-primary/15',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  )
}
