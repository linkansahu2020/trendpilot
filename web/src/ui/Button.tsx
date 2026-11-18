import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { cn } from '@/lib/cn'

const variants = {
  primary:
    'bg-linear-to-r from-primary to-secondary text-on-primary shadow-[var(--shadow-cta)] hover:scale-[1.02] hover:shadow-[var(--shadow-cta-hover)]',
  secondary:
    'bg-canvas text-ink border border-border hover:border-border-hover hover:bg-surface-subtle',
  ghost:
    'bg-transparent text-ink border border-transparent hover:bg-surface-subtle',
  badge:
    'bg-primary-soft text-primary border border-transparent hover:border-primary/20',
} as const

const sizes = {
  sm: 'h-8 px-3 text-sm font-semibold gap-1.5',
  md: 'h-10 px-5 text-sm font-semibold gap-2',
  lg: 'h-12 px-6 text-base font-semibold gap-2',
} as const

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: keyof typeof variants
  size?: keyof typeof sizes
  children: ReactNode
}

function Button({
  variant = 'primary',
  size = 'md',
  className,
  type = 'button',
  disabled,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled}
      className={cn(
        'inline-flex items-center justify-center rounded-full transition duration-150 ease-out cursor-pointer',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2',
        'disabled:pointer-events-none disabled:opacity-50',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}

export { Button, type ButtonProps }
