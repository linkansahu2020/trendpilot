import { useRef, type FormEvent } from 'react'
import {
  Button,
  Input,
  LinkIcon,
  SparkleIcon,
  Text,
  UploadIcon,
} from '@/ui'
import { cn } from '@/lib/cn'
import { useClipSource, UPLOAD_EXTENSIONS } from './useClipSource'

const accept = [...UPLOAD_EXTENSIONS].join(',')

type ClipSourceHubProps = {
  className?: string
}

function ClipSourceHub({ className }: ClipSourceHubProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { url, file, error, canSubmit, setUrl, setFile, clear, submit } =
    useClipSource()

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    submit()
  }

  return (
    <form
      onSubmit={onSubmit}
      className={cn('flex w-full max-w-[680px] flex-col gap-3', className)}
    >
      <div
        className={cn(
          'flex w-full flex-col items-center gap-2 rounded-full bg-canvas p-2 pl-6 shadow-[var(--shadow-card)]',
          'transition duration-150 focus-within:shadow-[var(--shadow-cta)]',
          'sm:flex-row',
        )}
      >
        <div className="flex min-w-0 w-full flex-1 items-center gap-3">
          <LinkIcon className="size-[22px] shrink-0 text-secondary" />
          {file ? (
            <div className="flex min-w-0 flex-1 items-center gap-2">
              <Text
                variant="body-md"
                className="truncate text-on-surface"
                as="span"
              >
                {file.name}
              </Text>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="shrink-0 px-2"
                onClick={clear}
                aria-label="Clear selected file"
              >
                Clear
              </Button>
            </div>
          ) : (
            <Input
              variant="ghost"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              placeholder="Paste YouTube, Zoom, or Drive link..."
              aria-label="Video URL"
              autoComplete="off"
            />
          )}
        </div>

        <div className="flex w-full items-center justify-end gap-1 sm:w-auto">
          <input
            ref={fileInputRef}
            type="file"
            accept={accept}
            className="sr-only"
            onChange={(event) => {
              const next = event.target.files?.[0] ?? null
              setFile(next)
              event.target.value = ''
            }}
          />
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="hidden md:inline-flex"
            onClick={() => fileInputRef.current?.click()}
          >
            <UploadIcon className="size-[18px]" />
            Upload MP4
          </Button>
          <Button type="submit" variant="primary" size="md" disabled={!canSubmit}>
            Get Free Clips
            <SparkleIcon className="size-[18px]" />
          </Button>
        </div>
      </div>

      {error ? (
        <Text variant="body-sm" className="text-center text-error" role="alert">
          {error}
        </Text>
      ) : null}
    </form>
  )
}

export { ClipSourceHub, type ClipSourceHubProps }
