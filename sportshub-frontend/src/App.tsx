import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import { AppShell } from './components/AppShell'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AlertsPage } from './pages/AlertsPage'
import { AuthPage } from './pages/AuthPage'
import { HomePage } from './pages/HomePage'
import { FixtureDetailPage } from './pages/FixtureDetailPage'
import { ProfilePage } from './pages/ProfilePage'
import { ExploreTeamsPage, MyTeamsPage } from './pages/TeamsPage'
import { VerifyEmailPage } from './pages/VerifyEmailPage'

function App() {
  return <Routes><Route element={<AppShell />}><Route index element={<HomePage />} /><Route path="fixtures/:fixtureId" element={<FixtureDetailPage />} /><Route path="explore/teams" element={<ExploreTeamsPage />} /><Route path="login" element={<AuthPage mode="login" />} /><Route path="register" element={<AuthPage mode="register" />} /><Route path="verify-email" element={<VerifyEmailPage />} /><Route element={<ProtectedRoute />}><Route path="my/teams" element={<MyTeamsPage />} /><Route path="alerts" element={<AlertsPage />} /><Route path="profile" element={<ProfilePage />} /></Route><Route path="teams" element={<Navigate to="/explore/teams" replace />} /><Route path="*" element={<Navigate to="/" replace />} /></Route></Routes>
}

export default App
