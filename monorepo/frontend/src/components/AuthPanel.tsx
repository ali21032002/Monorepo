import React, { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

type Mode = 'login' | 'register' | 'profile' | 'admin'

const AuthPanel: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  const { user, loading, error, login, register, logout, listUsers, updateUser, deleteUser } = useAuth()
  const [mode, setMode] = useState<Mode>('login')
  const [form, setForm] = useState<any>({ username: '', email: '', full_name: '', password: '' })
  const [users, setUsers] = useState<any[]>([])
  const [usersLoading, setUsersLoading] = useState(false)
  const [usersError, setUsersError] = useState<string | null>(null)

  useEffect(() => {
    if (user) setMode(user.is_admin ? 'admin' : 'profile')
    else setMode('login')
  }, [user, isOpen])

  const canSeeAdmin = user?.is_admin

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    await login(form.username, form.password)
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    const ok = await register({ username: form.username, email: form.email, full_name: form.full_name, password: form.password })
    if (ok) setMode('login')
  }

  const refreshUsers = async () => {
    if (!canSeeAdmin) return
    try {
      setUsersLoading(true)
      setUsersError(null)
      const data = await listUsers()
      setUsers(data)
    } catch (e: any) {
      setUsersError(e.message || 'Failed to load users')
    } finally {
      setUsersLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen && canSeeAdmin) refreshUsers()
  }, [isOpen, canSeeAdmin])

  const onUpdateUser = async (u: any) => {
    const payload: any = { email: u.email, full_name: u.full_name }
    if (u.is_active !== undefined) payload.is_active = u.is_active
    if (u.is_admin !== undefined) payload.is_admin = u.is_admin
    await updateUser(u.id, payload)
    await refreshUsers()
  }

  const onDeleteUser = async (u: any) => {
    if (!confirm('حذف کاربر؟')) return
    await deleteUser(u.id)
    await refreshUsers()
  }

  if (!isOpen) return null

  return (
    <div className="auth-overlay" onClick={onClose}>
      <div className="auth-panel" onClick={(e) => e.stopPropagation()}>
        <div className="auth-header">
          <h3>{user ? (canSeeAdmin ? 'مدیریت کاربران' : 'پروفایل کاربری') : (mode === 'login' ? 'ورود' : 'ثبت‌نام')}</h3>
          <button className="auth-close" onClick={onClose}>✕</button>
        </div>

        {!user && (
          <div className="auth-tabs">
            <button className={`auth-tab ${mode === 'login' ? 'active' : ''}`} onClick={() => setMode('login')}>ورود</button>
            <button className={`auth-tab ${mode === 'register' ? 'active' : ''}`} onClick={() => setMode('register')}>ثبت‌نام</button>
          </div>
        )}

        {/* Login */}
        {!user && mode === 'login' && (
          <form className="auth-form" onSubmit={handleLogin}>
            <label>
              نام کاربری
              <input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
            </label>
            <label>
              رمز عبور
              <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
            </label>
            {error && <p className="auth-error">{error}</p>}
            <button className="btn btn-primary" disabled={loading} type="submit">{loading ? '...' : 'ورود'}</button>
          </form>
        )}

        {/* Register */}
        {!user && mode === 'register' && (
          <form className="auth-form" onSubmit={handleRegister}>
            <label>
              نام کاربری
              <input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
            </label>
            <label>
              ایمیل
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
            </label>
            <label>
              نام کامل
              <input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
            </label>
            <label>
              رمز عبور
              <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
            </label>
            {error && <p className="auth-error">{error}</p>}
            <button className="btn btn-primary" disabled={loading} type="submit">{loading ? '...' : 'ثبت‌نام'}</button>
          </form>
        )}

        {/* Profile */}
        {user && !canSeeAdmin && (
          <div className="profile-view">
            <div className="profile-row"><span>نام کاربری:</span><b>{user.username}</b></div>
            <div className="profile-row"><span>نام:</span><b>{user.full_name || '-'}</b></div>
            <div className="profile-row"><span>ایمیل:</span><b>{user.email || '-'}</b></div>
            <div className="profile-row"><span>وضعیت:</span><b>{user.is_active ? 'فعال' : 'غیرفعال'}</b></div>
            <div className="profile-actions">
              <button className="btn" onClick={logout}>خروج</button>
            </div>
          </div>
        )}

        {/* Admin Users */}
        {user && canSeeAdmin && (
          <div className="admin-users">
            <div className="admin-toolbar">
              <button className="btn" onClick={refreshUsers} disabled={usersLoading}>بروزرسانی</button>
              <button className="btn" onClick={logout}>خروج</button>
            </div>
            {usersError && <p className="auth-error">{usersError}</p>}
            <div className="users-table">
              <div className="users-header">
                <span>ID</span>
                <span>نام کاربری</span>
                <span>نام</span>
                <span>ایمیل</span>
                <span>فعال</span>
                <span>ادمین</span>
                <span>اقدامات</span>
              </div>
              {users.map((u) => (
                <div className="users-row" key={u.id}>
                  <span>{u.id}</span>
                  <span>{u.username}</span>
                  <input value={u.full_name || ''} onChange={(e) => setUsers((prev) => prev.map(p => p.id === u.id ? { ...p, full_name: e.target.value } : p))} />
                  <input value={u.email || ''} onChange={(e) => setUsers((prev) => prev.map(p => p.id === u.id ? { ...p, email: e.target.value } : p))} />
                  <input type="checkbox" checked={!!u.is_active} onChange={(e) => setUsers((prev) => prev.map(p => p.id === u.id ? { ...p, is_active: e.target.checked } : p))} />
                  <input type="checkbox" checked={!!u.is_admin} onChange={(e) => setUsers((prev) => prev.map(p => p.id === u.id ? { ...p, is_admin: e.target.checked } : p))} />
                  <div className="row-actions">
                    <button className="btn btn-primary" onClick={() => onUpdateUser(u)} disabled={usersLoading}>ذخیره</button>
                    <button className="btn btn-danger" onClick={() => onDeleteUser(u)} disabled={usersLoading}>حذف</button>
                  </div>
                </div>
              ))}
              {users.length === 0 && !usersLoading && <div className="empty">کاربری وجود ندارد</div>}
            </div>
          </div>
        )}

        <style>{`
          .auth-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:1000; }
          .auth-panel { background: white; width: 96%; max-width: 760px; border-radius: 12px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
          .auth-header { display:flex; align-items:center; justify-content:space-between; padding: 1rem 1.25rem; border-bottom: 1px solid #eee; }
          .auth-close { background: transparent; border: none; font-size: 1.25rem; cursor: pointer; }
          .auth-tabs { display:flex; gap: 8px; padding: 12px; border-bottom: 1px solid #f3f4f6; }
          .auth-tab { background: #f3f4f6; border: 1px solid #e5e7eb; padding: 6px 12px; border-radius: 6px; cursor: pointer; }
          .auth-tab.active { background: #e5e7eb; }
          .auth-form { display:flex; flex-direction:column; gap: 12px; padding: 16px; }
          .auth-form label { display:flex; flex-direction:column; gap:6px; font-size: 0.9rem; }
          .auth-form input { border: 1px solid #d1d5db; border-radius: 6px; padding: 8px 10px; }
          .auth-error { color: #ef4444; padding: 0 16px; }
          .btn { padding: 8px 12px; border-radius: 6px; border: 1px solid #cbd5e1; background: #f8fafc; cursor: pointer; }
          .btn-primary { background: #3b82f6; border-color: #3b82f6; color: white; }
          .btn-danger { background: #ef4444; border-color: #ef4444; color: white; }
          .profile-view { padding: 16px; display: grid; gap: 8px; }
          .profile-row { display:flex; gap:8px; align-items:center; }
          .profile-actions { margin-top: 8px; }
          .admin-users { padding: 12px; }
          .admin-toolbar { display:flex; gap:8px; margin-bottom: 8px; }
          .users-table { border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
          .users-header, .users-row { display: grid; grid-template-columns: 60px 1fr 1.2fr 1.4fr 80px 80px 200px; gap: 8px; align-items: center; padding: 8px 10px; }
          .users-header { background: #f3f4f6; font-weight: 600; }
          .users-row { border-top: 1px solid #f1f5f9; }
          .row-actions { display:flex; gap: 8px; justify-content:flex-end; }
          .empty { padding: 16px; text-align:center; color: #64748b; }
          .dark-mode .auth-panel { background: #0f172a; color: #e2e8f0; border: 1px solid #1f2937; }
          .dark-mode .auth-header { border-bottom-color: #1f2937; }
          .dark-mode .auth-tab { background: #1f2937; border-color: #334155; color: #e2e8f0; }
          .dark-mode .auth-tab.active { background: #334155; }
          .dark-mode .auth-form input { background: #0b1220; border-color: #334155; color: #e2e8f0; }
          .dark-mode .users-header { background: #111827; }
          .dark-mode .users-table { border-color: #1f2937; }
          .dark-mode .users-row { border-top-color: #1f2937; }
        `}</style>
      </div>
    </div>
  )
}

export default AuthPanel


