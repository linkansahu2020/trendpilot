import type { IconProps } from './IconProps'

function SparkleIcon({ className, ...props }: IconProps) {
  return (
    <svg
      aria-hidden
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
      {...props}
    >
      <path d="M12 2.5 13.6 8.4 19.5 10 13.6 11.6 12 17.5 10.4 11.6 4.5 10 10.4 8.4 12 2.5Z" />
      <path d="M18.5 14.5 19.3 17.2 22 18 19.3 18.8 18.5 21.5 17.7 18.8 15 18 17.7 17.2 18.5 14.5Z" />
    </svg>
  )
}

export { SparkleIcon }
