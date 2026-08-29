import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/context'

const MAIL_INBOX_URL = import.meta.env.VITE_MAIL_INBOX_URL as string | undefined

export function ProfilePage() {
  const { user, token, updateUser, logout } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState(user?.email ?? '')
  const [username, setUsername] = useState(user?.username ?? '')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [resending, setResending] = useState(false)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [changingPassword, setChangingPassword] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [password, setPassword] = useState('')
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (!user) return
    setEmail(user.email)
    setUsername(user.username)
  }, [user])

  if (!user || !token) return null

  const changed = email.trim() !== user.email || username.trim() !== user.username

  const saveProfile = async (event: FormEvent) => {
    event.preventDefault()
    if (!changed) return
    setSaving(true)
    setMessage('')
    setError('')
    try {
      const updated = await api.updateProfile(token, {
        email: email.trim(),
        username: username.trim(),
      })
      updateUser(updated)
      setMessage(updated.pending_email
        ? `Verification email sent to ${updated.pending_email}. Your current sign-in email remains active until verification.`
        : 'Your profile has been updated.')
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not update your profile.')
    } finally {
      setSaving(false)
    }
  }

  const resendVerification = async () => {
    setResending(true)
    setMessage('')
    setError('')
    try {
      await api.resendEmailVerification(token)
      setMessage(`Verification email sent to ${user.pending_email ?? user.email}.`)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not send the verification email.')
    } finally {
      setResending(false)
    }
  }

  const changePassword = async (event: FormEvent) => {
    event.preventDefault()
    setMessage('')
    setError('')
    if (newPassword !== confirmPassword) {
      setError('New password confirmation does not match.')
      return
    }
    setChangingPassword(true)
    try {
      await api.changePassword(token, currentPassword, newPassword)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setMessage('Your password has been changed. A security email was sent to your current address.')
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not change your password.')
    } finally {
      setChangingPassword(false)
    }
  }

  const deleteAccount = async (event: FormEvent) => {
    event.preventDefault()
    setDeleting(true)
    setMessage('')
    setError('')
    try {
      await api.deleteAccount(token, password)
      logout()
      navigate('/', { replace: true })
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not delete your account.')
      setDeleting(false)
    }
  }

  return <section className="workspace-page profile-page">
    <div className="profile-heading"><span className="eyebrow">Account settings</span><h1>Your profile</h1><p>Update the identity shown throughout SportsHub or permanently remove your account and its saved data.</p></div>
    {message && <div className="success-message" role="status">{message}</div>}
    {error && <div className="error-message" role="alert">{error}</div>}
    <div className="profile-grid">
      <form className="panel profile-card" onSubmit={saveProfile}>
        <div><span className="eyebrow">Profile details</span><h2>Account identity</h2><p>Your username appears in the SportsHub header. A new email becomes your sign-in address only after verification.</p></div>
        <div className={`email-status ${user.pending_email ? 'pending' : user.email_verified ? 'verified' : 'unverified'}`}><strong>{user.pending_email ? 'Email change pending' : user.email_verified ? 'Email verified' : 'Email verification required'}</strong><span>{user.pending_email ? `${user.pending_email} is waiting for confirmation.` : user.email_verified ? `${user.email} is verified.` : `Check ${user.email} for the verification link.`}</span>{(user.pending_email || !user.email_verified) && <div className="email-status-actions"><button className="text-button" type="button" disabled={resending} onClick={resendVerification}>{resending ? 'Sending…' : 'Resend verification email'}</button>{MAIL_INBOX_URL && <a className="text-button" href={MAIL_INBOX_URL} target="_blank" rel="noreferrer">Open local mailbox</a>}</div>}</div>
        <label>Email address<input required type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} /></label>
        <label>Username<input required minLength={3} maxLength={50} pattern="[A-Za-z0-9_.-]+" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} /></label>
        <button className="button primary" disabled={!changed || saving}>{saving ? 'Saving…' : 'Save profile'}</button>
      </form>
      <form className="panel profile-card password-card" onSubmit={changePassword}>
        <div><span className="eyebrow">Account security</span><h2>Change password</h2><p>Confirm your current password, then choose a new password with at least eight characters.</p></div>
        <label>Current password<input required minLength={8} type="password" autoComplete="current-password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} /></label>
        <label>New password<input required minLength={8} type="password" autoComplete="new-password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} /></label>
        <label>Confirm new password<input required minLength={8} type="password" autoComplete="new-password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} /></label>
        <button className="button secondary" disabled={changingPassword}>{changingPassword ? 'Changing…' : 'Change password'}</button>
      </form>
      <section className="panel danger-zone" aria-labelledby="delete-account-heading">
        <span className="eyebrow">Danger zone</span><h2 id="delete-account-heading">Delete account</h2><p>This permanently deletes your profile, followed teams, notification preferences, registered devices, and alert history.</p>
        {!confirmDelete ? <button className="button danger" type="button" onClick={() => { setConfirmDelete(true); setMessage(''); setError('') }}>Delete user account</button> : <form onSubmit={deleteAccount} className="delete-confirmation"><label>Enter your current password<input required minLength={8} type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} /></label><div><button className="button danger" disabled={deleting}>{deleting ? 'Deleting…' : 'Permanently delete account'}</button><button className="button secondary" type="button" disabled={deleting} onClick={() => { setConfirmDelete(false); setPassword(''); setError('') }}>Cancel</button></div></form>}
      </section>
    </div>
  </section>
}
