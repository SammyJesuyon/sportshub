import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import { AppShell } from './components/AppShell'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AlertsPage } from './pages/AlertsPage'
import { AuthPage } from './pages/AuthPage'
import { HomePage } from './pages/HomePage'
import { TeamsPage } from './pages/TeamsPage'

function App() {
  return <Routes><Route element={<AppShell />}><Route index element={<HomePage />} /><Route path="login" element={<AuthPage mode="login" />} /><Route path="register" element={<AuthPage mode="register" />} /><Route element={<ProtectedRoute />}><Route path="teams" element={<TeamsPage />} /><Route path="alerts" element={<AlertsPage />} /></Route><Route path="*" element={<Navigate to="/" replace />} /></Route></Routes>
}

export default App
