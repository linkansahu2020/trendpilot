import { useState } from 'react'

const YOUTUBE_HOSTS = new Set([
  'youtube.com',
  'www.youtube.com',
  'm.youtube.com',
  'youtu.be',
])

const UPLOAD_EXTENSIONS = new Set([
  '.mp4',
  '.mov',
  '.m4v',
  '.mkv',
  '.webm',
])

type ClipSource =
  | { kind: 'url'; url: string }
  | { kind: 'file'; file: File }

function isYoutubeUrl(value: string): boolean {
  try {
    const parsed = new URL(value.trim())
    return (
      (parsed.protocol === 'http:' || parsed.protocol === 'https:') &&
      YOUTUBE_HOSTS.has(parsed.hostname.toLowerCase())
    )
  } catch {
    return false
  }
}

function fileExtension(name: string): string {
  const dot = name.lastIndexOf('.')
  return dot >= 0 ? name.slice(dot).toLowerCase() : ''
}

function isAllowedUpload(file: File): boolean {
  return UPLOAD_EXTENSIONS.has(fileExtension(file.name))
}

function useClipSource() {
  const [url, setUrlState] = useState('')
  const [file, setFileState] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)

  const hasValidUrl = isYoutubeUrl(url)
  const hasValidFile = file !== null && isAllowedUpload(file)
  const canSubmit = hasValidUrl || hasValidFile

  function setUrl(value: string) {
    setUrlState(value)
    setFileState(null)
    setError(null)
  }

  function setFile(next: File | null) {
    if (next && !isAllowedUpload(next)) {
      setError('Use an .mp4, .mov, .m4v, .mkv, or .webm video.')
      return
    }
    setFileState(next)
    setUrlState('')
    setError(null)
  }

  function clear() {
    setUrlState('')
    setFileState(null)
    setError(null)
  }

  function submit(): ClipSource | null {
    if (file) {
      if (!isAllowedUpload(file)) {
        setError('Use an .mp4, .mov, .m4v, .mkv, or .webm video.')
        return null
      }
      setError(null)
      return { kind: 'file', file }
    }

    const trimmed = url.trim()
    if (!trimmed) {
      setError('Paste a YouTube link or upload a video.')
      return null
    }
    if (!isYoutubeUrl(trimmed)) {
      setError('Send a YouTube link (youtube.com or youtu.be).')
      return null
    }
    setError(null)
    return { kind: 'url', url: trimmed }
  }

  return {
    url,
    file,
    error,
    canSubmit,
    setUrl,
    setFile,
    clear,
    submit,
  }
}

export {
  useClipSource,
  isYoutubeUrl,
  UPLOAD_EXTENSIONS,
  type ClipSource,
}
