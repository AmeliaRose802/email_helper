// Main layout component with navigation
import React from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '@/hooks/redux';
import { logout } from '@/store/authSlice';

const Layout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((state) => state.auth);

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  const isActiveRoute = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <h1 className="app-title">
            <Link to="/">Email Helper</Link>
          </h1>

          <div className="header-actions">
            {user && (
              <>
                <span className="user-greeting">Welcome, {user.username}</span>
                <button onClick={handleLogout} className="logout-button">
                  Logout
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      <div className="main-container">
        <nav className="sidebar">
          <ul className="nav-menu">
            <li>
              <Link
                to="/"
                className={isActiveRoute('/') && location.pathname === '/' ? 'active' : ''}
              >
                📊 Dashboard
              </Link>
            </li>
            <li>
              <Link to="/emails" className={isActiveRoute('/emails') ? 'active' : ''}>
                📧 Emails
              </Link>
            </li>
            <li>
              <Link to="/tasks" className={isActiveRoute('/tasks') ? 'active' : ''}>
                ✅ Tasks
              </Link>
            </li>
            <li>
              <Link to="/settings" className={isActiveRoute('/settings') ? 'active' : ''}>
                ⚙️ Settings
              </Link>
            </li>
          </ul>

          <div className="sidebar-footer">
            <div className="api-status">
              <h4>API Status</h4>
              <div className="status-indicators">
                <div className="status-item">
                  <span className="status-dot green"></span>
                  T1: Auth API
                </div>
                <div className="status-item">
                  <span className="status-dot green"></span>
                  T2: Email API
                </div>
                <div className="status-item">
                  <span className="status-dot green"></span>
                  T3: AI API
                </div>
                <div className="status-item">
                  <span className="status-dot green"></span>
                  T4: Task API
                </div>
              </div>
            </div>
          </div>
        </nav>

        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
