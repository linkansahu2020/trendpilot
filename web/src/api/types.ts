export type Clip = {
  index: number
  start: number
  end: number
  duration: number
  hook: string
  title: string
  caption: string
  hashtags: string[]
  score: number
  url: string
}

export type ClipJob = {
  jobId: string
  status: string
  progress: number
  error: string | null
  clips: Clip[]
}

export type InstagramProfile = {
  id: string
  username?: string | null
  name?: string | null
  biography?: string | null
  website?: string | null
  followersCount?: number | null
  followsCount?: number | null
  mediaCount?: number | null
  profilePictureUrl?: string | null
}

export type InstagramMedia = {
  id: string
  caption?: string | null
  mediaType?: string | null
  mediaUrl?: string | null
  permalink?: string | null
  timestamp?: string | null
  likeCount?: number | null
  commentsCount?: number | null
}

export type InstagramAccount = {
  profile: InstagramProfile
  media: InstagramMedia[]
  nextCursor?: string | null
}

export type ApiError = {
  error: string
}
