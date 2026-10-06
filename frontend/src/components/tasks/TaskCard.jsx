import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Calendar,
  CheckCircle2,
  Clock,
  Edit2,
  Folder,
  MessageSquare,
  Trash2,
  User,
} from 'lucide-react';
import { CategoryPill, PriorityBadge, StatusBadge, TagPill } from '../common/Badge';
import { formatDate, isDateOverdue } from '../../utils/formatters';
import { useAuth } from '../../hooks/useAuth';

export const TaskCard = ({
  task,
  onEdit,
  onDelete,
  onToggleComplete,
  compact = false,
}) => {
  const { isCEO, user } = useAuth();
  const navigate = useNavigate();

  const isCompleted = task.status === 'completed';
  const isOverdue = isDateOverdue(task.due_date, task.status);

  return (
    <div
      style={{
        ...styles.card,
        opacity: isCompleted ? 0.75 : 1,
      }}
      className="card-hover"
      onClick={() => navigate(`/tasks/${task.id}`)}
    >
      {/* Top Header: Category & Priority */}
      <div style={styles.topRow}>
        <div style={styles.categoryArea}>
          {task.category ? (
            <CategoryPill name={task.category.name} />
          ) : (
            <span style={styles.uncategorized}>General</span>
          )}
        </div>
        <PriorityBadge priority={task.priority} />
      </div>

      {/* Title & Quick Complete */}
      <div style={styles.titleRow}>
        <button
          style={{
            ...styles.checkBtn,
            color: isCompleted ? '#10b981' : '#64748b',
          }}
          onClick={(e) => {
            e.stopPropagation();
            onToggleComplete?.(task);
          }}
          title={isCompleted ? 'Reopen task' : 'Mark as completed'}
        >
          <CheckCircle2 size={18} />
        </button>

        <h4
          style={{
            ...styles.title,
            textDecoration: isCompleted ? 'line-through' : 'none',
            color: isCompleted ? '#94a3b8' : '#f8fafc',
          }}
        >
          {task.title}
        </h4>
      </div>

      {/* Description Preview (if not compact) */}
      {!compact && task.description && (
        <p style={styles.description}>{task.description}</p>
      )}

      {/* Tags */}
      {task.tags && task.tags.length > 0 && (
        <div style={styles.tagsArea}>
          {task.tags.map((t) => (
            <TagPill key={t.id} name={t.name} />
          ))}
        </div>
      )}

      {/* Bottom Metadata & Actions */}
      <div style={styles.footer}>
        <div style={styles.metadataArea}>
          {task.due_date && (
            <div
              style={{
                ...styles.metaItem,
                color: isOverdue ? '#ef4444' : '#94a3b8',
                fontWeight: isOverdue ? 600 : 400,
              }}
              title={isOverdue ? 'Task is overdue!' : 'Due date'}
            >
              <Calendar size={13} />
              <span>{formatDate(task.due_date)}</span>
            </div>
          )}

          {task.assignee && (
            <div style={styles.metaItem} title={`Assigned to ${task.assignee.name}`}>
              <User size={13} color="#38bdf8" />
              <span>
                {task.assigned_to_id === user?.id ? 'Assigned to You' : task.assignee.name}
              </span>
            </div>
          )}
        </div>

        <div style={styles.actionsArea}>
          <button
            style={styles.actionBtn}
            onClick={(e) => {
              e.stopPropagation();
              onEdit?.(task);
            }}
            title={isCEO ? "Edit task" : "Update status"}
          >
            <Edit2 size={14} />
          </button>
          {isCEO && (
            <button
              style={{ ...styles.actionBtn, color: '#ef4444' }}
              onClick={(e) => {
                e.stopPropagation();
                onDelete?.(task);
              }}
              title="Delete task"
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

const styles = {
  card: {
    background: 'rgba(18, 24, 38, 0.75)',
    backdropFilter: 'blur(12px)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '12px',
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    cursor: 'pointer',
    transition: 'all 200ms ease',
  },
  topRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '8px',
  },
  categoryArea: {
    display: 'flex',
    alignItems: 'center',
  },
  uncategorized: {
    fontSize: '11px',
    color: '#64748b',
    fontWeight: 500,
  },
  titleRow: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '10px',
  },
  checkBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: 0,
    marginTop: '2px',
    display: 'flex',
    alignItems: 'center',
    transition: 'color 150ms ease, transform 150ms ease',
  },
  title: {
    fontSize: '14px',
    fontWeight: 600,
    lineHeight: 1.4,
    margin: 0,
    flex: 1,
    wordBreak: 'break-word',
  },
  description: {
    fontSize: '13px',
    color: '#94a3b8',
    lineHeight: 1.5,
    margin: 0,
    display: '-webkit-box',
    WebkitLineClamp: 2,
    WebkitBoxOrient: 'vertical',
    overflow: 'hidden',
  },
  tagsArea: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
  },
  footer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: '8px',
    borderTop: '1px solid rgba(255, 255, 255, 0.05)',
    marginTop: 'auto',
  },
  metadataArea: {
    display: 'flex',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '12px',
  },
  metaItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    fontSize: '12px',
    color: '#94a3b8',
  },
  actionsArea: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  actionBtn: {
    background: 'rgba(255, 255, 255, 0.04)',
    border: '1px solid rgba(255, 255, 255, 0.06)',
    borderRadius: '6px',
    color: '#94a3b8',
    padding: '6px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 150ms ease',
  },
};
