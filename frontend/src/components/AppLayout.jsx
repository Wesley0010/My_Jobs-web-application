import { useEffect, useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { getUser, apiMe, apiLogout, isAuthenticated } from '../lib/auth';
import './AppLayout.css';

function AppLayout({ children }) {
  const navigate = useNavigate();
  const [user, setUser] = useState(getUser());

  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login', { replace: true });
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const fresh = await apiMe();
        if (!cancelled) setUser((prev) => ({ ...prev, ...fresh }));
      } catch {
        navigate('/login', { replace: true });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [navigate]);

  const handleLogout = async () => {
    if (!window.confirm('Sign out of your account?')) return;
    await apiLogout();
    navigate('/login', { replace: true });
  };

  if (!user) return null;

  const initials = (user.name || user.email || '?')
    .split(' ')
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/dashboard" className="brand">
          My<span>Jobs</span>
        </Link>

        <nav className="app-header-nav">
          <NavLink to="/dashboard" className="header-link">
            Dashboard
          </NavLink>
          <NavLink to="/profile" className="header-link">
            Profile
          </NavLink>
          <div className="header-user">
            <div className="mini-avatar">{initials}</div>
            <div className="header-user-meta">
              <strong>{user.name || 'User'}</strong>
              <small>{user.email}</small>
            </div>
          </div>
        </nav>
      </header>

      <div className="app-body">
        <aside className="app-sidebar">
          <div className="sidebar-profile">
            <div className="avatar">{initials}</div>
            <h3>{user.name || 'Unnamed User'}</h3>
            <p>{user.email}</p>
          </div>

          <ul className="sidebar-nav">
            <li>
              <NavLink
                to="/dashboard"
                className={({ isActive }) => (isActive ? 'active' : '')}
                end
              >
                <span>🏠</span> Dashboard
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/profile"
                className={({ isActive }) => (isActive ? 'active' : '')}
              >
                <span>👤</span> Profile
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/jobs"
                className={({ isActive }) => (isActive ? 'active' : '')}
              >
                <span>💼</span> Jobs
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/saved"
                className={({ isActive }) => (isActive ? 'active' : '')}
              >
                <span>⭐</span> Saved
              </NavLink>
            </li>
          </ul>

          <button className="sidebar-logout" onClick={handleLogout}>
            Sign out
          </button>
        </aside>

        <main className="app-content">{children}</main>
      </div>
    </div>
  );
}

export default AppLayout;