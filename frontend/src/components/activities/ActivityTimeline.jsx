import React, { useEffect, useState } from 'react';
import {
  Activity,
  CheckCircle,
  Folder,
  History,
  MessageSquare,
  PlusCircle,
  Tag,
  UserCheck,
} from 'lucide-react';
import { activitiesApi } from '../../api/activities';
import { formatRelativeTime } from '../../utils/formatters';

export const ActivityTimeline = ({ taskId }) => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadActivities = async () => {
      if (!taskId) return;
      setLoading(true);
      try {
        const data = await activitiesApi.getTaskActivities(taskId, { limit: 50 });
        setActivities(data.items || []);
      } catch (err) {
        console.error('Failed to load task activities:', err);
      } finally {
        setLoading(false);
      }
    };
    loadActivities();
  }, [taskId]);

  const getActionIcon = (action) => {
    switch (action) {
      case 'task_created':
        return <PlusCircle size={15} color="#10b981" />;
      case 'status_changed':
        return <CheckCircle size={15} color="#38bdf8" />;
      case 'assigned_user':
      case 'assignee_changed':
      case 'assignee_removed':
        return <UserCheck size={15} color="#818cf8" />;
      case 'comment_added':
        return <MessageSquare size={15} color="#a855f7" />;
      case 'category_changed':
        return <Folder size={15} color="#06b6d4" />;
      case 'tag_added':
      case 'tag_removed':
        return <Tag size={15} color="#f59e0b" />;
      default:
        return <Activity size={15} color="#94a3b8" />;
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.sectionHeader}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <History size={18} color="#6366f1" />
          <h4 style={styles.title}>Activity History</h4>
        </div>
      </div>

      <div style={styles.timeline}>
        {loading ? (
          <div style={styles.empty}>Loading activities...</div>
        ) : activities.length === 0 ? (
          <div style={styles.empty}>No activity recorded yet</div>
        ) : (
          activities.map((item, index) => (
            <div key={item.id} style={styles.timelineItem}>
              {/* Vertical line connector */}
              {index < activities.length - 1 && <div style={styles.line} />}

              {/* Node Icon */}
              <div style={styles.nodeIcon}>{getActionIcon(item.action)}</div>

              {/* Content */}
              <div style={styles.content}>
                <div style={styles.topRow}>
                  <span style={styles.actor}>
                    {item.user ? item.user.name : 'System'}
                  </span>
                  <span style={styles.time}>{formatRelativeTime(item.created_at)}</span>
                </div>
                <p style={styles.description}>{item.description}</p>
              </div>
            </div>
          ))
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
    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
  },
  title: {
    fontSize: '16px',
    fontWeight: 700,
    color: '#f8fafc',
    margin: 0,
  },
  timeline: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
    paddingLeft: '8px',
  },
  timelineItem: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '14px',
    position: 'relative',
  },
  line: {
    position: 'absolute',
    top: '24px',
    left: '12px',
    width: '2px',
    bottom: '-16px',
    background: 'rgba(255, 255, 255, 0.08)',
  },
  nodeIcon: {
    width: '26px',
    height: '26px',
    borderRadius: '50%',
    background: 'rgba(30, 41, 59, 0.9)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1,
    flexShrink: 0,
  },
  content: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
    paddingTop: '2px',
  },
  topRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  actor: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#f8fafc',
  },
  time: {
    fontSize: '11px',
    color: '#64748b',
  },
  description: {
    fontSize: '12px',
    color: '#94a3b8',
    margin: 0,
    lineHeight: 1.4,
  },
  empty: {
    padding: '24px 16px',
    textAlign: 'center',
    color: '#64748b',
    fontSize: '13px',
    background: 'rgba(255, 255, 255, 0.02)',
    borderRadius: '8px',
    border: '1px dashed rgba(255, 255, 255, 0.06)',
  },
};
