import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/context'

export function ProtectedRoute() {
  const { token, loading } = useAuth()
  const location = useLocation()
  if (loading) return <div className="page-state">Restoring your SportsHub session...</div>
  if (!token) return <Navigate to="/login" state={{ from: location }} replace />
  return <Outlet />
}
