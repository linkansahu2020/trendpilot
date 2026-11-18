import type { ElementType, HTMLAttributes, ReactNode } from 'react'
import { cn } from '@/lib/cn'

const variants = {
  display:
    'font-display text-[38px] font-extrabold leading-[44px] tracking-[-0.025em] text-on-surface md:text-[64px] md:leading-[72px] md:tracking-[-0.03em]',
  'headline-lg':
    'font-display text-[30px] font-bold leading-[38px] tracking-[-0.02em] text-on-surface md:text-[44px] md:leading-[52px] md:tracking-[-0.025em]',
  'headline-md':
    'font-display text-2xl font-semibold leading-8 tracking-[-0.015em] text-on-surface md:text-[32px] md:font-bold md:leading-10 md:tracking-[-0.02em]',
  'headline-sm':
    'font-display text-[22px] font-semibold leading-7 tracking-[-0.01em] text-on-surface',
  'body-lg':
    'font-sans text-lg font-normal leading-7 tracking-[-0.01em] text-muted',
  'body-md': 'font-sans text-[15px] font-normal leading-6 text-muted',
  'body-sm': 'font-sans text-[13px] font-normal leading-5 text-muted',
  label:
    'font-sans text-sm font-semibold leading-5 tracking-[0.01em] text-on-surface',
  caption:
    'font-sans text-[11px] font-medium leading-[14px] tracking-[0.03em] text-muted',
} as const

const defaultTags = {
  display: 'h1',
  'headline-lg': 'h2',
  'headline-md': 'h3',
  'headline-sm': 'h4',
  'body-lg': 'p',
  'body-md': 'p',
  'body-sm': 'p',
  label: 'span',
  caption: 'span',
} as const satisfies Record<keyof typeof variants, ElementType>

type TextProps = HTMLAttributes<HTMLElement> & {
  variant?: keyof typeof variants
  as?: ElementType
  children: ReactNode
}

function Text({
  variant = 'body-md',
  as,
  className,
  children,
  ...props
}: TextProps) {
  const Component = as ?? defaultTags[variant]

  return (
    <Component className={cn(variants[variant], className)} {...props}>
      {children}
    </Component>
  )
}

export { Text, type TextProps }
