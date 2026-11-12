import type { ApiError, ClipJob } from './types'

const JOB_STORAGE_KEY = 'clipJobId'

export function readStoredJobId(): string | null {
  return sessionStorage.getItem(JOB_STORAGE_KEY)
}

export function storeJobId(jobId: string): void {
  sessionStorage.setItem(JOB_STORAGE_KEY, jobId)
}

export function clearStoredJobId(): void {
  sessionStorage.removeItem(JOB_STORAGE_KEY)
}

async function readError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as ApiError
    if (body.error) {
      return body.error
    }
  } catch {
    // Fall through to status text.
  }
  return response.statusText || `Request failed (${response.status})`
}

export async function createJobFromUrl(url: string): Promise<string> {
  const response = await fetch('/clips/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })
  if (!response.ok) {
    throw new Error(await readError(response))
  }
  const body = (await response.json()) as { jobId: string }
  return body.jobId
}

export async function createJobFromFile(file: File): Promise<string> {
  const form = new FormData()
  form.append('file', file)
  const response = await fetch('/clips/jobs', {
    method: 'POST',
    body: form,
  })
  if (!response.ok) {
    throw new Error(await readError(response))
  }
  const body = (await response.json()) as { jobId: string }
  return body.jobId
}

export function isClipJob(value: unknown): value is ClipJob {
  if (!value || typeof value !== 'object') {
    return false
  }
  const job = value as Partial<ClipJob>
  return typeof job.jobId === 'string' && typeof job.status === 'string' && Array.isArray(job.clips)
}

export function watchClipJob(
  jobId: string,
  onJob: (job: ClipJob) => void,
  onLost: (message: string) => void,
): () => void {
  const source = new EventSource(`/clips/jobs/${jobId}/events`)

  source.onmessage = (event) => {
    let payload: unknown
    try {
      payload = JSON.parse(event.data) as unknown
    } catch {
      onLost('The job update could not be read.')
      source.close()
      return
    }

    if (payload && typeof payload === 'object' && 'error' in payload && !('jobId' in payload)) {
      onLost(String((payload as ApiError).error))
      source.close()
      return
    }

    if (!isClipJob(payload)) {
      onLost('The job update had an unexpected shape.')
      source.close()
      return
    }

    onJob(payload)
    if (payload.status === 'done' || payload.status === 'failed') {
      source.close()
    }
  }

  source.onerror = () => {
    if (source.readyState === EventSource.CLOSED) {
      return
    }
    source.close()
    onLost('Clip job not found.')
  }

  return () => source.close()
}
