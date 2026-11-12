import { useEffect, useState } from 'react'
import { getAccount } from '../../api/instagram'
import type { InstagramAccount } from '../../api/types'

export function AccountPage() {
  const [account, setAccount] = useState<InstagramAccount | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [needsSignIn, setNeedsSignIn] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    void (async () => {
      const result = await getAccount()
      if (cancelled) {
        return
      }
      setLoading(false)
      if (result.ok) {
        setAccount(result.account)
        setNeedsSignIn(false)
        setError(null)
        return
      }
      setAccount(null)
      if (result.status === 401) {
        setNeedsSignIn(true)
        setError(null)
        return
      }
      setNeedsSignIn(false)
      setError(result.error)
    })()
    return () => {
      cancelled = true
    }
  }, [])

  if (loading) {
    return (
      <section className="account">
        <p className="brand">TrendPilot</p>
        <h1>Instagram</h1>
        <p className="lede">Checking the signed-in account…</p>
      </section>
    )
  }

  if (needsSignIn) {
    return (
      <section className="account">
        <p className="brand">TrendPilot</p>
        <h1>Connect Instagram</h1>
        <p className="lede">
          Sign in with an Instagram Business or Creator account. The API keeps one login in memory for
          this machine.
        </p>
        <a className="button" href="/instagram/login">
          Sign in with Instagram
        </a>
      </section>
    )
  }

  if (error) {
    return (
      <section className="account">
        <p className="brand">TrendPilot</p>
        <h1>Instagram</h1>
        <p className="message message--error">{error}</p>
        <a className="button" href="/instagram/login">
          Try signing in again
        </a>
      </section>
    )
  }

  if (!account) {
    return null
  }

  const { profile, media } = account

  return (
    <section className="account">
      <header className="account__hero">
        <p className="brand">TrendPilot</p>
        <h1>{profile.name || profile.username || 'Instagram account'}</h1>
        <p className="lede">
          @{profile.username}
          {profile.followersCount != null ? ` · ${profile.followersCount} followers` : ''}
        </p>
        {profile.biography ? <p className="account__bio">{profile.biography}</p> : null}
      </header>

      {profile.profilePictureUrl ? (
        <img
          className="account__avatar"
          src={profile.profilePictureUrl}
          alt=""
          width={96}
          height={96}
        />
      ) : null}

      <h2 className="account__media-title">Recent media</h2>
      <ul className="media-list">
        {media.map((item) => (
          <li key={item.id} className="media-card">
            {item.mediaUrl && item.mediaType === 'VIDEO' ? (
              <video controls preload="metadata" src={item.mediaUrl} />
            ) : item.mediaUrl ? (
              <img src={item.mediaUrl} alt="" />
            ) : (
              <div className="media-card__empty">No preview</div>
            )}
            <div className="media-card__body">
              <p>{item.caption || 'Untitled'}</p>
              {item.permalink ? (
                <a href={item.permalink} target="_blank" rel="noreferrer">
                  Open on Instagram
                </a>
              ) : null}
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
