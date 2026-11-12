const LABELS: Record<string, string> = {
  queued: 'Waiting for the clip worker',
  downloading: 'Getting the video',
  transcribing: 'Transcribing speech',
  selecting: 'Choosing the best moments',
  rendering: 'Rendering vertical clips',
  done: 'Clips are ready',
  failed: 'The job failed',
}

export function statusLabel(status: string): string {
  return LABELS[status] ?? status
}

export const ACCEPTED_UPLOADS = '.mp4,.mov,.m4v,.mkv,.webm'
