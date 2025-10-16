import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'

type User = {
  id: number
  username: string
  email?: string | null
  full_name?: string | null
  is_active: boolean
  is_admin: boolean
}

type AuthContextValue = {
  user: User | null
  token: string | null
  loading: boolean
  error: string | null
  login: (username: string, password: string) => Promise<boolean>
  register: (payload: { username: string; email: string; full_name?: string; password: string }) => Promise<boolean>
  logout: () => void
  refreshMe: () => Promise<void>
  health: () => Promise<boolean>
  listUsers: () => Promise<User[]>
  updateUser: (userId: number, payload: Partial<Pick<User, 'email' | 'full_name' | 'is_active' | 'is_admin'>>) => Promise<User>
  deleteUser: (userId: number) => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

const USER_API = (import.meta.env.VITE_USER_API_URL as string) || 'http://localhost:8002'

function getStoredToken(): string | null {
  try {
    return localStorage.getItem('user_jwt')
  } catch {
    return null
  }
}

function setStoredToken(token: string | null) {
  try {
    if (token) localStorage.setItem('user_jwt', token)
    else localStorage.removeItem('user_jwt')
  } catch {}
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(getStoredToken())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setStoredToken(token)
  }, [token])

  const authHeader = useMemo(() => ({ Authorization: token ? `Bearer ${token}` : '' }), [token])

  const refreshMe = async () => {
    if (!token) {
      setUser(null)
      return
    }
    try {
      setLoading(true)
      setError(null)
      const resp = await fetch(`${USER_API}/users/me`, { headers: { ...authHeader } })
      if (!resp.ok) throw new Error('Unauthorized')
      const data = await resp.json()
      setUser(data)
    } catch (e: any) {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refreshMe()
  }, [])

  const health = async () => {
    try {
      const resp = await fetch(`${USER_API}/health`)
      return resp.ok
    } catch {
      return false
    }
  }

  const login = async (username: string, password: string) => {
    try {
      setLoading(true)
      setError(null)
      const form = new URLSearchParams()
      form.append('username', username)
      form.append('password', password)
      const resp = await fetch(`${USER_API}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: form.toString(),
      })
      if (!resp.ok) {
        let detail = ''
        try { detail = (await resp.json())?.detail || '' } catch { try { detail = await resp.text() } catch {}
        }
        throw new Error(detail || `Login failed (${resp.status})`)
      }
      const data = await resp.json()
      setToken(data.access_token)
      await refreshMe()
      return true
    } catch (e: any) {
      setError(e.message || 'Login failed')
      return false
    } finally {
      setLoading(false)
    }
  }

  const register = async (payload: { username: string; email: string; full_name?: string; password: string }) => {
    try {
      setLoading(true)
      setError(null)
      const resp = await fetch(`${USER_API}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...payload }),
      })
      if (!resp.ok) {
        let detail = ''
        try { detail = (await resp.json())?.detail || '' } catch { try { detail = await resp.text() } catch {}
        }
        throw new Error(detail || `Register failed (${resp.status})`)
      }
      return true
    } catch (e: any) {
      setError(e.message || 'Register failed')
      return false
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
  }

  const listUsers = async () => {
    const resp = await fetch(`${USER_API}/users`, { headers: { ...authHeader } })
    if (!resp.ok) throw new Error('Failed to load users')
    return await resp.json()
  }

  const updateUser = async (userId: number, payload: Partial<Pick<User, 'email' | 'full_name' | 'is_active' | 'is_admin'>>) => {
    const resp = await fetch(`${USER_API}/users/${userId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeader },
      body: JSON.stringify(payload),
    })
    if (!resp.ok) throw new Error('Failed to update user')
    return await resp.json()
  }

  const deleteUser = async (userId: number) => {
    const resp = await fetch(`${USER_API}/users/${userId}`, { method: 'DELETE', headers: { ...authHeader } })
    if (!resp.ok && resp.status !== 204) throw new Error('Failed to delete user')
  }

  const value = useMemo<AuthContextValue>(() => ({
    user,
    token,
    loading,
    error,
    login,
    register,
    logout,
    refreshMe,
    health,
    listUsers,
    updateUser,
    deleteUser,
  }), [user, token, loading, error])

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}


