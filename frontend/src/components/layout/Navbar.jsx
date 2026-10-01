import React from 'react';
import { Menu, Plus } from 'lucide-react';
import { NotificationDropdown } from '../notifications/NotificationDropdown';
import { useAuth } from '../../hooks/useAuth';

export const Navbar = ({ onOpenSidebar, onNewTask }) => {
  const { user } = useAuth();

  return (
    <header style={styles.header}>
      <div style={styles.left}>
        <button
          style={styles.menuBtn}
          onClick={onOpenSidebar}
          aria-label="Toggle navigation menu"
        >
          <Menu size={20} color="#94a3b8" />
        </button>
      </div>

      <div style={styles.right}>
        {onNewTask && (
          <button className="btn btn-primary btn-sm" onClick={onNewTask}>
            <Plus size={16} />
            <span>New Task</span>
          </button>
        )}

        <NotificationDropdown />

        <div style={styles.userBadge}>
          <div style={styles.userInitial}>
            {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
          </div>
          <span style={styles.userName}>{user?.name}</span>
        </div>
      </div>
    </header>
  );
};

const styles = {
  header: {
    height: '64px',
    backgroundColor: 'rgba(15, 23, 42, 0.75)',
    backdropFilter: 'blur(16px)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 24px',
    position: 'sticky',
    top: 0,
    zIndex: 80,
  },
  left: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  menuBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: '8px',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    color: '#94a3b8',
  },
  right: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  userBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '4px 10px 4px 4px',
    background: 'rgba(255, 255, 255, 0.04)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '9999px',
  },
  userInitial: {
    width: '26px',
    height: '26px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
    color: '#ffffff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '12px',
    fontWeight: 700,
  },
  userName: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#f8fafc',
  },
};
