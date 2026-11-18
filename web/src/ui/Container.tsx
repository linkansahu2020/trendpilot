import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '@/lib/cn'

type ContainerProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode
}

function Container({ children, className, ...props }: ContainerProps) {
  return (
    <div
      className={cn(
        'mx-auto w-full max-w-[1200px]',
        'px-[var(--spacing-margin)] md:px-[var(--spacing-margin-tablet)] lg:px-[var(--spacing-margin-desktop)]',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export { Container, type ContainerProps }
