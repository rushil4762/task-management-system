import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  CheckSquare,
  FolderTree,
  Kanban,
  LayoutDashboard,
  LogOut,
  Tag,
  User,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

export const Sidebar = ({ isOpen, onClose }) => {
  const { user, isCEO, logout } = useAuth();

  const navItems = isCEO
    ? [
        { to: '/', label: 'Dashboard', icon: LayoutDashboard },
        { to: '/tasks', label: 'Tasks', icon: CheckSquare },
        { to: '/kanban', label: 'Kanban Board', icon: Kanban },
        { to: '/categories', label: 'Categories', icon: FolderTree },
        { to: '/tags', label: 'Tags', icon: Tag },
      ]
    : [
        { to: '/', label: 'Dashboard', icon: LayoutDashboard },
        { to: '/tasks', label: 'My Assigned Tasks', icon: CheckSquare },
        { to: '/kanban', label: 'Kanban Board', icon: Kanban },
      ];

  return (
    <>
      {isOpen && <div style={styles.overlay} onClick={onClose} />}
      <aside
        style={{
          ...styles.sidebar,
          transform: isOpen ? 'translateX(0)' : undefined,
        }}
        className={isOpen ? 'sidebar-open' : ''}
      >
        {/* Brand Header */}
        <div style={styles.brand}>
          <div style={styles.logoIcon}>
            <CheckSquare size={22} color="#ffffff" />
          </div>
          <div>
            <h2 style={styles.brandTitle}>TaskPulse</h2>
            <span style={styles.brandSubtitle}>Productivity Suite</span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav style={styles.nav}>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onClose}
                style={({ isActive }) => ({
                  ...styles.navLink,
                  ...(isActive ? styles.navLinkActive : {}),
                })}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* User Card & Logout */}
        <div style={styles.footer}>
          <div style={styles.userProfile}>
            <div style={styles.avatar}>
              <User size={18} color="#ffffff" />
            </div>
            <div style={styles.userInfo}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={styles.userName}>{user?.name || 'User'}</span>
                <span
                  style={{
                    fontSize: '10px',
                    fontWeight: 700,
                    padding: '1px 6px',
                    borderRadius: '4px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    backgroundColor: isCEO ? 'rgba(129, 140, 248, 0.2)' : 'rgba(52, 211, 153, 0.2)',
                    color: isCEO ? '#a5b4fc' : '#6ee7b7',
                    border: `1px solid ${isCEO ? 'rgba(129, 140, 248, 0.4)' : 'rgba(52, 211, 153, 0.4)'}`,
                  }}
                >
                  {user?.role || 'EMPLOYEE'}
                </span>
              </div>
              <div style={styles.userEmail}>{user?.email || ''}</div>
            </div>
          </div>
          <button style={styles.logoutBtn} onClick={logout} title="Sign Out">
            <LogOut size={16} />
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
};

const styles = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    backdropFilter: 'blur(4px)',
    zIndex: 90,
    display: 'none',
  },
  sidebar: {
    width: '260px',
    backgroundColor: 'rgba(15, 23, 42, 0.95)',
    backdropFilter: 'blur(16px)',
    borderRight: '1px solid rgba(255, 255, 255, 0.08)',
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    position: 'sticky',
    top: 0,
    zIndex: 100,
    transition: 'transform 250ms ease',
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '24px 20px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
  },
  logoIcon: {
    width: '38px',
    height: '38px',
    borderRadius: '10px',
    background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 0 16px rgba(99, 102, 241, 0.4)',
  },
  brandTitle: {
    fontSize: '18px',
    fontWeight: 800,
    color: '#ffffff',
    letterSpacing: '-0.02em',
    lineHeight: 1.1,
  },
  brandSubtitle: {
    fontSize: '11px',
    color: '#94a3b8',
    fontWeight: 500,
  },
  nav: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    padding: '20px 12px',
    flex: 1,
    overflowY: 'auto',
  },
  navLink: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '10px 14px',
    borderRadius: '10px',
    color: '#94a3b8',
    fontSize: '14px',
    fontWeight: 600,
    transition: 'all 150ms ease',
  },
  navLinkActive: {
    background: 'rgba(99, 102, 241, 0.15)',
    color: '#818cf8',
    boxShadow: 'inset 0 0 0 1px rgba(99, 102, 241, 0.3)',
  },
  footer: {
    padding: '16px',
    borderTop: '1px solid rgba(255, 255, 255, 0.06)',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    background: 'rgba(9, 13, 22, 0.5)',
  },
  userProfile: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '6px',
  },
  avatar: {
    width: '34px',
    height: '34px',
    borderRadius: '50%',
    background: '#334155',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  userInfo: {
    flex: 1,
    minWidth: 0,
  },
  userName: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#f8fafc',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  userEmail: {
    fontSize: '11px',
    color: '#64748b',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  logoutBtn: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    width: '100%',
    padding: '8px',
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.2)',
    borderRadius: '8px',
    color: '#f87171',
    fontSize: '13px',
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 150ms ease',
  },
};
