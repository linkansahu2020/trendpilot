import type { ApiError, InstagramAccount } from './types'

async function readError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as ApiError
    if (body.error) {
      return body.error
    }
  } catch {
    // Fall through.
  }
  return response.statusText || `Request failed (${response.status})`
}

export async function getAccount(): Promise<
  { ok: true; account: InstagramAccount } | { ok: false; status: number; error: string }
> {
  const response = await fetch('/instagram/me')
  if (response.status === 401) {
    return { ok: false, status: 401, error: 'Sign in at /instagram/login.' }
  }
  if (!response.ok) {
    return { ok: false, status: response.status, error: await readError(response) }
  }
  const account = (await response.json()) as InstagramAccount
  return { ok: true, account }
}
