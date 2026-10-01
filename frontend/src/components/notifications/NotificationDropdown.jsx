import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bell,
  Check,
  CheckCheck,
  Clock,
  MessageSquare,
  UserCheck,
  X,
} from 'lucide-react';
import { notificationsApi } from '../../api/notifications';
import { formatRelativeTime } from '../../utils/formatters';

export const NotificationDropdown = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  const fetchUnreadCount = async () => {
    try {
      const data = await notificationsApi.getUnreadCount();
      setUnreadCount(data.unread_count || 0);
    } catch {
      // Ignore polling errors silently
    }
  };

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const data = await notificationsApi.getNotifications({ limit: 15 });
      setNotifications(data.items || []);
      setUnreadCount(data.unread_count || 0);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUnreadCount();
    // Poll unread count every 30 seconds
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleMarkAsRead = async (id, e) => {
    e?.stopPropagation();
    try {
      await notificationsApi.markAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Failed to mark notification read:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsApi.markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all read:', err);
    }
  };

  const handleNotificationClick = (notification) => {
    if (!notification.is_read) {
      handleMarkAsRead(notification.id);
    }
    if (notification.task_id) {
      setIsOpen(false);
      navigate(`/tasks/${notification.task_id}`);
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'task_assigned':
        return <UserCheck size={16} color="#38bdf8" />;
      case 'task_completed':
        return <Check size={16} color="#10b981" />;
      case 'task_due_soon':
      case 'task_overdue':
        return <Clock size={16} color="#f59e0b" />;
      case 'comment_added':
        return <MessageSquare size={16} color="#a855f7" />;
      default:
        return <Bell size={16} color="#94a3b8" />;
    }
  };

  return (
    <div style={{ position: 'relative' }} ref={dropdownRef}>
      <button
        style={styles.bellButton}
        onClick={() => setIsOpen(!isOpen)}
        aria-label="View notifications"
      >
        <Bell size={20} color="#94a3b8" />
        {unreadCount > 0 && (
          <span style={styles.badge}>
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div style={styles.dropdown} className="animate-slide-up">
          <div style={styles.header}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <h4 style={styles.headerTitle}>Notifications</h4>
              {unreadCount > 0 && (
                <span style={styles.unreadTag}>{unreadCount} new</span>
              )}
            </div>
            {unreadCount > 0 && (
              <button
                style={styles.markAllBtn}
                onClick={handleMarkAllRead}
                title="Mark all as read"
              >
                <CheckCheck size={14} />
                Mark all read
              </button>
            )}
          </div>

          <div style={styles.list}>
            {loading ? (
              <div style={styles.emptyState}>Loading notifications...</div>
            ) : notifications.length === 0 ? (
              <div style={styles.emptyState}>No notifications right now</div>
            ) : (
              notifications.map((item) => (
                <div
                  key={item.id}
                  style={{
                    ...styles.item,
                    ...(item.is_read ? styles.itemRead : styles.itemUnread),
                  }}
                  onClick={() => handleNotificationClick(item)}
                >
                  <div style={styles.itemIcon}>{getTypeIcon(item.type)}</div>
                  <div style={styles.itemContent}>
                    <div style={styles.itemTitle}>{item.title}</div>
                    <div style={styles.itemMessage}>{item.message}</div>
                    <div style={styles.itemTime}>
                      {formatRelativeTime(item.created_at)}
                    </div>
                  </div>
                  {!item.is_read && (
                    <button
                      style={styles.readDotBtn}
                      onClick={(e) => handleMarkAsRead(item.id, e)}
                      title="Mark as read"
                    >
                      <div style={styles.unreadDot} />
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const styles = {
  bellButton: {
    position: 'relative',
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '10px',
    padding: '8px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 150ms ease',
  },
  badge: {
    position: 'absolute',
    top: '-4px',
    right: '-4px',
    background: '#ef4444',
    color: '#ffffff',
    fontSize: '11px',
    fontWeight: 700,
    minWidth: '18px',
    height: '18px',
    borderRadius: '9999px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '0 4px',
    boxShadow: '0 0 8px rgba(239, 68, 68, 0.5)',
  },
  dropdown: {
    position: 'absolute',
    top: 'calc(100% + 8px)',
    right: 0,
    width: '360px',
    maxWidth: 'calc(100vw - 32px)',
    background: '#131b2e',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '14px',
    boxShadow: '0 15px 35px rgba(0, 0, 0, 0.5)',
    zIndex: 1000,
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '14px 16px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
    background: 'rgba(18, 24, 38, 0.5)',
  },
  headerTitle: {
    fontSize: '15px',
    fontWeight: 700,
    color: '#f8fafc',
    margin: 0,
  },
  unreadTag: {
    fontSize: '11px',
    fontWeight: 600,
    background: 'rgba(99, 102, 241, 0.2)',
    color: '#a5b4fc',
    padding: '2px 8px',
    borderRadius: '9999px',
  },
  markAllBtn: {
    background: 'none',
    border: 'none',
    color: '#94a3b8',
    fontSize: '12px',
    fontWeight: 600,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    transition: 'color 150ms ease',
  },
  list: {
    maxHeight: '380px',
    overflowY: 'auto',
  },
  item: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
    padding: '12px 16px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
    cursor: 'pointer',
    transition: 'background 150ms ease',
  },
  itemUnread: {
    background: 'rgba(99, 102, 241, 0.06)',
  },
  itemRead: {
    opacity: 0.75,
  },
  itemIcon: {
    paddingTop: '2px',
  },
  itemContent: {
    flex: 1,
    minWidth: 0,
  },
  itemTitle: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#f8fafc',
    marginBottom: '2px',
  },
  itemMessage: {
    fontSize: '12px',
    color: '#94a3b8',
    lineHeight: 1.4,
    marginBottom: '4px',
  },
  itemTime: {
    fontSize: '11px',
    color: '#64748b',
  },
  readDotBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: '6px',
    display: 'flex',
    alignItems: 'center',
  },
  unreadDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    background: '#6366f1',
    boxShadow: '0 0 6px rgba(99, 102, 241, 0.6)',
  },
  emptyState: {
    padding: '32px 16px',
    textAlign: 'center',
    color: '#64748b',
    fontSize: '13px',
  },
};
