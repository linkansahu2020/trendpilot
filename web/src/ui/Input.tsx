import type { InputHTMLAttributes } from 'react'
import { cn } from '@/lib/cn'

const variants = {
  default:
    'h-11 rounded-md border border-border bg-canvas px-4 focus:border-primary focus:ring-[3px] focus:ring-primary/15',
  ghost:
    'h-10 rounded-none border-0 bg-transparent px-0 focus:ring-0',
} as const

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  variant?: keyof typeof variants
}

function Input({
  className,
  type = 'text',
  variant = 'default',
  ...props
}: InputProps) {
  return (
    <input
      {...props}
      type={type}
      className={cn(
        'w-full text-sm text-on-surface placeholder:text-muted',
        'transition duration-150 focus:outline-none',
        'disabled:cursor-not-allowed disabled:opacity-50',
        variants[variant],
        className,
      )}
    />
  )
}

export { Input, type InputProps }
