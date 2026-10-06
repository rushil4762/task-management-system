import React, { useCallback, useEffect, useState } from 'react';
import {
  Activity,
  AlertCircle,
  Calendar,
  CheckCircle,
  Clock,
  Folder,
  History,
  MessageSquare,
  PlusCircle,
  RefreshCw,
  Tag,
  UserCheck,
} from 'lucide-react';
import { activitiesApi } from '../../api/activities';

const formatTimelineTime = (dateString) => {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    if (diffInSeconds < 60) return 'just now';
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    if (diffInMinutes === 1) return '1 minute ago';
    if (diffInMinutes < 60) return `${diffInMinutes} minutes ago`;
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours === 1) return '1 hour ago';
    if (diffInHours < 24) return `${diffInHours} hours ago`;
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays === 1) return '1 day ago';
    if (diffInDays < 30) return `${diffInDays} days ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return dateString;
  }
};

const formatStatusLabel = (val) => {
  if (!val) return '';
  const mapping = {
    pending: 'Pending',
    in_progress: 'In Progress',
    completed: 'Completed',
    cancelled: 'Cancelled',
  };
  return mapping[val.toLowerCase()] || val.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
};

const formatPriorityLabel = (val) => {
  if (!val) return '';
  const mapping = {
    low: 'Low',
    medium: 'Medium',
    high: 'High',
    urgent: 'Urgent',
  };
  return mapping[val.toLowerCase()] || val.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
};

export const ActivityTimeline = ({ taskId }) => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadActivities = useCallback(async () => {
    if (!taskId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await activitiesApi.getTaskActivities(taskId, { limit: 50 });
      setActivities(data.items || []);
    } catch (err) {
      console.error('Failed to load task activities:', err);
      setError(err?.response?.data?.detail || 'Failed to load activities');
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    loadActivities();
  }, [loadActivities]);

  const getActionTheme = (action) => {
    switch (action) {
      case 'task_created':
        return { icon: <PlusCircle size={14} />, color: '#10b981', bg: 'rgba(16, 185, 129, 0.12)' };
      case 'task_assigned':
      case 'assigned_user':
      case 'assignee_changed':
        return { icon: <UserCheck size={14} />, color: '#6366f1', bg: 'rgba(99, 102, 241, 0.12)' };
      case 'status_changed':
        return { icon: <Activity size={14} />, color: '#06b6d4', bg: 'rgba(6, 182, 212, 0.12)' };
      case 'priority_changed':
        return { icon: <AlertCircle size={14} />, color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.12)' };
      case 'due_date_changed':
        return { icon: <Calendar size={14} />, color: '#ec4899', bg: 'rgba(236, 72, 153, 0.12)' };
      case 'comment_added':
        return { icon: <MessageSquare size={14} />, color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.12)' };
      case 'task_completed':
        return { icon: <CheckCircle size={14} />, color: '#10b981', bg: 'rgba(16, 185, 129, 0.12)' };
      case 'task_reopened':
        return { icon: <RefreshCw size={14} />, color: '#f97316', bg: 'rgba(249, 115, 22, 0.12)' };
      case 'category_changed':
        return { icon: <Folder size={14} />, color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.12)' };
      case 'tag_added':
        return { icon: <Tag size={14} />, color: '#10b981', bg: 'rgba(16, 185, 129, 0.12)' };
      case 'tag_removed':
        return { icon: <Tag size={14} />, color: '#ef4444', bg: 'rgba(239, 68, 68, 0.12)' };
      default:
        return { icon: <Activity size={14} />, color: '#94a3b8', bg: 'rgba(148, 163, 184, 0.12)' };
    }
  };

  const renderActionMessage = (item) => {
    const actorName = item.user?.name || 'Someone';

    // Status change with arrow
    if (item.action === 'status_changed' && item.metadata?.old_value && item.metadata?.new_value) {
      return (
        <span>
          <strong style={styles.actorName}>{actorName}</strong> changed status{' '}
          <span style={styles.badgeOld}>{formatStatusLabel(item.metadata.old_value)}</span>
          {' → '}
          <span style={styles.badgeNew}>{formatStatusLabel(item.metadata.new_value)}</span>
        </span>
      );
    }

    // Priority change with arrow
    if (item.action === 'priority_changed' && item.metadata?.old_value && item.metadata?.new_value) {
      return (
        <span>
          <strong style={styles.actorName}>{actorName}</strong> changed priority{' '}
          <span style={styles.badgeOld}>{formatPriorityLabel(item.metadata.old_value)}</span>
          {' → '}
          <span style={styles.badgeNew}>{formatPriorityLabel(item.metadata.new_value)}</span>
        </span>
      );
    }

    // Default message or description
    const text = item.message || item.description;
    return <span style={styles.actionText}>{text}</span>;
  };

  return (
    <div style={styles.container}>
      <div style={styles.sectionHeader}>
        <div style={styles.headerLeft}>
          <History size={18} color="#6366f1" />
          <h4 style={styles.title}>Activity</h4>
          {activities.length > 0 && (
            <span style={styles.countBadge}>{activities.length}</span>
          )}
        </div>
      </div>

      <div style={styles.timeline}>
        {loading ? (
          <div style={styles.stateCard}>
            <Clock size={18} color="#6366f1" style={{ animation: 'spin 1.5s linear infinite' }} />
            <span>Loading activity...</span>
          </div>
        ) : error ? (
          <div style={styles.errorCard}>
            <AlertCircle size={18} color="#ef4444" />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, color: '#f87171' }}>Failed to load activity</div>
              <div style={{ fontSize: '12px', color: '#94a3b8' }}>{error}</div>
            </div>
            <button type="button" onClick={loadActivities} style={styles.retryButton}>
              Retry
            </button>
          </div>
        ) : activities.length === 0 ? (
          <div style={styles.emptyCard}>
            <Activity size={24} color="#475569" />
            <div style={styles.emptyText}>No activity yet.</div>
          </div>
        ) : (
          activities.map((item, index) => {
            const theme = getActionTheme(item.action);
            const absoluteTime = item.created_at ? new Date(item.created_at).toLocaleString() : '';
            return (
              <div key={item.id} style={styles.timelineItem}>
                {/* Vertical connector line */}
                {index < activities.length - 1 && <div style={styles.connectorLine} />}

                {/* Node icon bullet */}
                <div
                  style={{
                    ...styles.nodeBullet,
                    color: theme.color,
                    backgroundColor: theme.bg,
                    borderColor: `${theme.color}40`,
                  }}
                  title={item.action}
                >
                  {theme.icon}
                </div>

                {/* Event Details */}
                <div style={styles.itemContent}>
                  <div style={styles.messageRow}>
                    {renderActionMessage(item)}
                  </div>
                  <div style={styles.timeRow} title={absoluteTime}>
                    <Clock size={11} color="#64748b" style={{ marginRight: 4 }} />
                    <span style={styles.timeText}>{formatTimelineTime(item.created_at)}</span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
    marginTop: '24px',
  },
  sectionHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: '12px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  title: {
    fontSize: '16px',
    fontWeight: 700,
    color: '#f8fafc',
    margin: 0,
    letterSpacing: '-0.01em',
  },
  countBadge: {
    fontSize: '11px',
    fontWeight: 600,
    color: '#a5b4fc',
    background: 'rgba(99, 102, 241, 0.15)',
    border: '1px solid rgba(99, 102, 241, 0.3)',
    borderRadius: '12px',
    padding: '1px 7px',
  },
  timeline: {
    display: 'flex',
    flexDirection: 'column',
    gap: '18px',
    paddingLeft: '4px',
  },
  timelineItem: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '14px',
    position: 'relative',
  },
  connectorLine: {
    position: 'absolute',
    top: '26px',
    left: '13px',
    width: '2px',
    bottom: '-18px',
    background: 'linear-gradient(to bottom, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.04))',
  },
  nodeBullet: {
    width: '28px',
    height: '28px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    border: '1px solid',
    zIndex: 1,
    flexShrink: 0,
    boxShadow: '0 2px 6px rgba(0, 0, 0, 0.25)',
  },
  itemContent: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    paddingTop: '2px',
  },
  messageRow: {
    fontSize: '13px',
    lineHeight: 1.5,
    color: '#e2e8f0',
  },
  actorName: {
    color: '#ffffff',
    fontWeight: 600,
  },
  actionText: {
    color: '#e2e8f0',
  },
  badgeOld: {
    color: '#94a3b8',
    textDecoration: 'line-through',
    fontSize: '12px',
    padding: '1px 5px',
    borderRadius: '4px',
    background: 'rgba(255, 255, 255, 0.04)',
  },
  badgeNew: {
    color: '#38bdf8',
    fontWeight: 600,
    fontSize: '12px',
    padding: '1px 5px',
    borderRadius: '4px',
    background: 'rgba(56, 189, 248, 0.1)',
  },
  timeRow: {
    display: 'flex',
    alignItems: 'center',
    cursor: 'help',
  },
  timeText: {
    fontSize: '12px',
    color: '#64748b',
  },
  stateCard: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
    padding: '24px 16px',
    color: '#94a3b8',
    fontSize: '13px',
    background: 'rgba(255, 255, 255, 0.02)',
    borderRadius: '10px',
    border: '1px solid rgba(255, 255, 255, 0.06)',
  },
  errorCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '16px',
    background: 'rgba(239, 68, 68, 0.08)',
    border: '1px solid rgba(239, 68, 68, 0.2)',
    borderRadius: '10px',
  },
  retryButton: {
    background: '#ef4444',
    color: '#ffffff',
    border: 'none',
    borderRadius: '6px',
    padding: '6px 12px',
    fontSize: '12px',
    fontWeight: 600,
    cursor: 'pointer',
  },
  emptyCard: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    padding: '32px 16px',
    background: 'rgba(255, 255, 255, 0.02)',
    borderRadius: '10px',
    border: '1px dashed rgba(255, 255, 255, 0.08)',
  },
  emptyText: {
    fontSize: '13px',
    color: '#64748b',
    fontWeight: 500,
  },
};
