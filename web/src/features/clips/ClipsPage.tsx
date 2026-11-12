import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  clearStoredJobId,
  createJobFromFile,
  createJobFromUrl,
  readStoredJobId,
  storeJobId,
  watchClipJob,
} from '../../api/clips'
import type { ClipJob } from '../../api/types'
import { ACCEPTED_UPLOADS, statusLabel } from './statusLabels'

type SourceMode = 'url' | 'file'

export function ClipsPage() {
  const [mode, setMode] = useState<SourceMode>('url')
  const [url, setUrl] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [jobId, setJobId] = useState<string | null>(() => readStoredJobId())
  const [job, setJob] = useState<ClipJob | null>(null)

  useEffect(() => {
    if (!jobId) {
      return
    }
    const stop = watchClipJob(
      jobId,
      (next) => {
        setJob(next)
        setFormError(null)
      },
      (message) => {
        clearStoredJobId()
        setJobId(null)
        setJob(null)
        setFormError(message)
      },
    )
    return stop
  }, [jobId])

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      const nextId =
        mode === 'url'
          ? await createJobFromUrl(url.trim())
          : await createJobFromFile(file as File)
      storeJobId(nextId)
      setJob({
        jobId: nextId,
        status: 'queued',
        progress: 0,
        error: null,
        clips: [],
      })
      setJobId(nextId)
    } catch (error) {
      setFormError(error instanceof Error ? error.message : 'Could not start the clip job.')
    } finally {
      setSubmitting(false)
    }
  }

  function startOver() {
    clearStoredJobId()
    setJobId(null)
    setJob(null)
    setFormError(null)
  }

  const running = Boolean(job && job.status !== 'done' && job.status !== 'failed')
  const showForm = !job || job.status === 'failed'

  return (
    <section className="clips">
      <header className="clips__hero">
        <p className="brand">TrendPilot</p>
        <h1>Turn long video into short clips</h1>
        <p className="lede">
          Send a YouTube link or upload a file. Watch the job live, then download the vertical cuts.
        </p>
      </header>

      {showForm ? (
        <form className="source-form" onSubmit={onSubmit}>
          <div className="source-form__modes" role="tablist" aria-label="Source type">
            <button
              type="button"
              role="tab"
              aria-selected={mode === 'url'}
              className={mode === 'url' ? 'is-active' : undefined}
              onClick={() => setMode('url')}
              disabled={running || submitting}
            >
              YouTube link
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={mode === 'file'}
              className={mode === 'file' ? 'is-active' : undefined}
              onClick={() => setMode('file')}
              disabled={running || submitting}
            >
              Upload file
            </button>
          </div>

          {mode === 'url' ? (
            <label className="field">
              <span>YouTube URL</span>
              <input
                type="url"
                name="url"
                placeholder="https://www.youtube.com/watch?v=..."
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                required
                disabled={submitting}
              />
            </label>
          ) : (
            <label className="field">
              <span>Video file</span>
              <input
                type="file"
                name="file"
                accept={ACCEPTED_UPLOADS}
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                required
                disabled={submitting}
              />
            </label>
          )}

          {formError ? <p className="message message--error">{formError}</p> : null}

          <button type="submit" className="button" disabled={submitting || (mode === 'file' && !file)}>
            {submitting ? 'Starting…' : 'Make clips'}
          </button>
        </form>
      ) : null}

      {job ? (
        <div className="job">
          <div className="job__status">
            <p className="job__label">{statusLabel(job.status)}</p>
            <p className="job__meta">
              {Math.round(job.progress * 100)}% · {job.jobId.slice(0, 8)}
            </p>
            <div className="job__bar" aria-hidden="true">
              <span style={{ width: `${Math.max(4, Math.round(job.progress * 100))}%` }} />
            </div>
            {job.status === 'failed' && job.error ? (
              <p className="message message--error">{job.error}</p>
            ) : null}
            {job.status === 'done' || job.status === 'failed' ? (
              <button type="button" className="button button--ghost" onClick={startOver}>
                Start another
              </button>
            ) : null}
          </div>

          {job.clips.length > 0 ? (
            <ul className="clip-list">
              {job.clips.map((clip) => (
                <li key={clip.index} className="clip-card">
                  <video controls preload="metadata" src={clip.url} />
                  <div className="clip-card__body">
                    <p className="clip-card__score">{clip.score}</p>
                    <h2>{clip.title}</h2>
                    <p className="clip-card__hook">{clip.hook}</p>
                    <p>{clip.caption}</p>
                    <p className="clip-card__tags">
                      {clip.hashtags.map((tag) => `#${tag}`).join(' ')}
                    </p>
                    <p className="clip-card__meta">
                      {clip.duration.toFixed(1)}s · {clip.start.toFixed(1)}–{clip.end.toFixed(1)}
                    </p>
                    <a className="button button--ghost" href={clip.url} download={`clip-${clip.index}.mp4`}>
                      Download
                    </a>
                  </div>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </section>
  )
}
