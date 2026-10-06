import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  Edit2,
  Folder,
  Tag,
  Trash2,
  User,
} from 'lucide-react';
import { tasksApi } from '../../api/tasks';
import { CategoryPill, PriorityBadge, StatusBadge, TagPill } from '../../components/common/Badge';
import { CommentList } from '../../components/comments/CommentList';
import { ActivityTimeline } from '../../components/activities/ActivityTimeline';
import { TaskModal } from '../../components/tasks/TaskModal';
import { ConfirmModal } from '../../components/common/ConfirmModal';
import { LoadingScreen } from '../../components/common/Spinner';
import { useToast } from '../../hooks/useToast';
import { useAuth } from '../../hooks/useAuth';
import { formatDate, isDateOverdue } from '../../utils/formatters';

export const TaskDetailPage = () => {
  const { isCEO } = useAuth();
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();


  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);

  // Modals
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const loadTask = async () => {
    setLoading(true);
    try {
      const data = await tasksApi.getTask(id);
      setTask(data);
    } catch (err) {
      console.error('Failed to load task details:', err);
      toast.error('Task not found or access denied');
      navigate('/tasks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTask();
  }, [id]);

  const handleToggleComplete = async () => {
    if (!task) return;
    try {
      if (task.status === 'completed') {
        const reopened = await tasksApi.reopenTask(task.id);
        setTask(reopened);
        toast.info('Task reopened');
      } else {
        const completed = await tasksApi.markCompleted(task.id);
        setTask(completed);
        toast.success('Task completed');
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update task');
    }
  };

  const confirmDelete = async () => {
    if (!task) return;
    setDeleting(true);
    try {
      await tasksApi.deleteTask(task.id);
      toast.success('Task deleted');
      navigate('/tasks');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete task');
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return <LoadingScreen message="Loading task details..." />;
  }

  if (!task) return null;

  const isCompleted = task.status === 'completed';
  const isOverdue = isDateOverdue(task.due_date, task.status);

  return (
    <div style={styles.container}>
      {/* Back button & Actions header */}
      <div style={styles.header}>
        <button
          className="btn btn-ghost btn-sm"
          onClick={() => navigate('/tasks')}
        >
          <ArrowLeft size={16} />
          <span>Back to Tasks</span>
        </button>

        <div style={styles.headerActions}>
          <button
            className={`btn ${isCompleted ? 'btn-secondary' : 'btn-primary'} btn-sm`}
            onClick={handleToggleComplete}
          >
            <CheckCircle2 size={16} />
            <span>{isCompleted ? 'Reopen Task' : 'Mark Completed'}</span>
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setEditModalOpen(true)}
          >
            <Edit2 size={15} />
            <span>{isCEO ? 'Edit' : 'Update Status'}</span>
          </button>
          {isCEO && (
            <button
              className="btn btn-danger btn-sm"
              onClick={() => setDeleteModalOpen(true)}
            >
              <Trash2 size={15} />
              <span>Delete</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Task Card */}
      <div style={styles.taskCard}>
        {/* Badges & Meta */}
        <div style={styles.metaRow}>
          <div style={styles.badgeGroup}>
            <StatusBadge status={task.status} />
            <PriorityBadge priority={task.priority} />
            {task.category && <CategoryPill name={task.category.name} />}
          </div>

          <div style={styles.idBadge}>Task #{task.id}</div>
        </div>

        {/* Title */}
        <h1
          style={{
            ...styles.title,
            textDecoration: isCompleted ? 'line-through' : 'none',
            color: isCompleted ? '#94a3b8' : '#ffffff',
          }}
        >
          {task.title}
        </h1>

        {/* Description */}
        <div style={styles.descSection}>
          <h4 style={styles.sectionHeading}>Description</h4>
          {task.description ? (
            <p style={styles.description}>{task.description}</p>
          ) : (
            <p style={styles.emptyDesc}>No description provided.</p>
          )}
        </div>

        {/* Details Key-Value Grid */}
        <div style={styles.detailsGrid}>
          {/* Due date */}
          <div style={styles.detailBox}>
            <div style={styles.detailLabel}>
              <Calendar size={14} color="#818cf8" />
              <span>Due Date</span>
            </div>
            <span
              style={{
                ...styles.detailValue,
                color: isOverdue ? '#ef4444' : '#f8fafc',
                fontWeight: isOverdue ? 700 : 500,
              }}
            >
              {task.due_date ? formatDate(task.due_date, { includeTime: true }) : 'None'}
            </span>
          </div>

          {/* Assignee */}
          <div style={styles.detailBox}>
            <div style={styles.detailLabel}>
              <User size={14} color="#38bdf8" />
              <span>Assignee</span>
            </div>
            <span style={styles.detailValue}>
              {task.assignee ? task.assignee.name : 'Unassigned'}
            </span>
          </div>

          {/* Created Date */}
          <div style={styles.detailBox}>
            <div style={styles.detailLabel}>
              <Clock size={14} color="#94a3b8" />
              <span>Created</span>
            </div>
            <span style={styles.detailValue}>
              {formatDate(task.created_at, { includeTime: true })}
            </span>
          </div>

          {/* Completed At */}
          {task.completed_at && (
            <div style={styles.detailBox}>
              <div style={styles.detailLabel}>
                <CheckCircle2 size={14} color="#34d399" />
                <span>Completed</span>
              </div>
              <span style={{ ...styles.detailValue, color: '#34d399' }}>
                {formatDate(task.completed_at, { includeTime: true })}
              </span>
            </div>
          )}
        </div>

        {/* Tags Section */}
        {task.tags && task.tags.length > 0 && (
          <div style={styles.tagsSection}>
            <div style={styles.detailLabel}>
              <Tag size={14} color="#f59e0b" />
              <span>Tags</span>
            </div>
            <div style={styles.tagsList}>
              {task.tags.map((t) => (
                <TagPill key={t.id} name={t.name} />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Two Column Grid: Comments + Activity Timeline */}
      <div style={styles.columnsGrid}>
        <div style={styles.commentsCol}>
          <CommentList taskId={task.id} />
        </div>
        <div style={styles.activitiesCol}>
          <ActivityTimeline taskId={task.id} />
        </div>
      </div>

      {/* Edit Modal */}
      <TaskModal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        task={task}
        onSuccess={loadTask}
      />

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={confirmDelete}
        title="Delete Task"
        message={`Are you sure you want to delete "${task.title}"? This cannot be undone.`}
        confirmText="Delete Task"
        isLoading={deleting}
      />
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: '12px',
  },
  headerActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  taskCard: {
    background: 'rgba(18, 24, 38, 0.85)',
    backdropFilter: 'blur(16px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '16px',
    padding: '28px',
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  metaRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  badgeGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    flexWrap: 'wrap',
  },
  idBadge: {
    fontSize: '12px',
    fontWeight: 600,
    color: '#64748b',
    background: 'rgba(255, 255, 255, 0.04)',
    padding: '2px 8px',
    borderRadius: '6px',
  },
  title: {
    fontSize: '22px',
    fontWeight: 800,
    lineHeight: 1.3,
    margin: 0,
  },
  descSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  sectionHeading: {
    fontSize: '13px',
    fontWeight: 700,
    color: '#94a3b8',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
    margin: 0,
  },
  description: {
    fontSize: '14px',
    color: '#cbd5e1',
    lineHeight: 1.6,
    margin: 0,
    whiteSpace: 'pre-wrap',
  },
  emptyDesc: {
    fontSize: '13px',
    color: '#64748b',
    fontStyle: 'italic',
    margin: 0,
  },
  detailsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: '12px',
    padding: '16px 0',
    borderTop: '1px solid rgba(255, 255, 255, 0.06)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
  },
  detailBox: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  detailLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '12px',
    fontWeight: 600,
    color: '#94a3b8',
  },
  detailValue: {
    fontSize: '13px',
    fontWeight: 500,
    color: '#f8fafc',
  },
  tagsSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  tagsList: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
  },
  columnsGrid: {
    display: 'grid',
    gridTemplateColumns: '1.2fr 0.8fr',
    gap: '24px',
  },
  commentsCol: {
    minWidth: 0,
  },
  activitiesCol: {
    minWidth: 0,
  },
};
