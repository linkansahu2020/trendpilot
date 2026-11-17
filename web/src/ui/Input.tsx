import type { InputHTMLAttributes } from 'react'
import { cn } from './cn'

export type InputProps = InputHTMLAttributes<HTMLInputElement>

export function Input({ className, type = 'text', ...props }: InputProps) {
  return (
    <input
      type={type}
      className={cn(
        'h-11 w-full rounded-md border border-border bg-canvas px-4 text-sm text-on-surface',
        'placeholder:text-muted',
        'transition duration-150',
        'focus:border-primary focus:outline-none focus:ring-[3px] focus:ring-primary/15',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...props}
    />
  )
}
