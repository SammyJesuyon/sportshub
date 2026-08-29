import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/context'

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const { token: accessToken, updateUser } = useAuth()
  const [state, setState] = useState<'working' | 'verified' | 'error'>('working')
  const [message, setMessage] = useState('Verifying your email address…')

  useEffect(() => {
    const verificationToken = searchParams.get('token')
    if (!verificationToken) {
      setState('error')
      setMessage('This verification link is incomplete.')
      return
    }
    api.verifyEmail(verificationToken)
      .then((verifiedUser) => {
        if (accessToken) updateUser(verifiedUser)
        setState('verified')
        setMessage(`Email verified for ${verifiedUser.email}.`)
      })
      .catch((error) => {
        setState('error')
        setMessage(error instanceof Error ? error.message : 'Could not verify this email address.')
      })
  }, [accessToken, searchParams, updateUser])

  return <section className="auth-layout verification-page">
    <div className="auth-message"><span className="eyebrow">Account security</span><h1>{state === 'verified' ? 'Email verified.' : state === 'error' ? 'Link not accepted.' : 'One moment.'}</h1><p>{message}</p></div>
    <div className="auth-card verification-card" role="status"><span className={`verification-mark ${state}`} aria-hidden="true">{state === 'verified' ? '✓' : state === 'error' ? '!' : '…'}</span><h2>{state === 'verified' ? 'You’re all set' : state === 'error' ? 'Verification failed' : 'Checking your link'}</h2><p>{state === 'verified' ? 'Your verified address is now active on SportsHub.' : state === 'error' ? 'Return to your profile to request another verification email.' : 'SportsHub is checking the signed verification token.'}</p>{state !== 'working' && <Link className="button primary full" to={accessToken ? '/profile' : '/login'}>{accessToken ? 'Return to profile' : 'Sign in'}</Link>}</div>
  </section>
}
