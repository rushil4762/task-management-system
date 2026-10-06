import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  CheckSquare,
  ChevronLeft,
  ChevronRight,
  Kanban,
  Plus,
  Trash2,
} from 'lucide-react';
import { tasksApi } from '../../api/tasks';
import { TaskCard } from '../../components/tasks/TaskCard';
import { TaskFilters } from '../../components/tasks/TaskFilters';
import { TaskModal } from '../../components/tasks/TaskModal';
import { ConfirmModal } from '../../components/common/ConfirmModal';
import { EmptyState } from '../../components/common/EmptyState';
import { LoadingScreen } from '../../components/common/Spinner';
import { useToast } from '../../hooks/useToast';
import { useAuth } from '../../hooks/useAuth';

export const TasksListPage = () => {
  const { isCEO } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const toast = useToast();


  const [tasks, setTasks] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  // Filters state initialized from search params or defaults
  const [filters, setFilters] = useState({
    limit: 12,
    offset: 0,
    search: searchParams.get('search') || '',
    status: searchParams.get('status') || '',
    priority: searchParams.get('priority') || '',
    category_id: searchParams.get('category_id') || '',
    tag_id: searchParams.get('tag_id') || '',
    sort_by: searchParams.get('sort_by') || 'created_at',
    sort_order: searchParams.get('sort_order') || 'desc',
  });

  // Modals state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [taskToEdit, setTaskToEdit] = useState(null);

  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [taskToDelete, setTaskToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const loadTasks = async () => {
    setLoading(true);
    try {
      const cleanParams = Object.fromEntries(
        Object.entries(filters).filter(([_, v]) => v !== '' && v !== null && v !== undefined)
      );
      const data = await tasksApi.getTasks(cleanParams);
      setTasks(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Failed to load tasks:', err);
      toast.error('Unable to load tasks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, [filters]);

  useEffect(() => {
    const handleCreated = () => loadTasks();
    window.addEventListener('task:created', handleCreated);
    return () => window.removeEventListener('task:created', handleCreated);
  }, [filters]);

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
  };

  const handleResetFilters = () => {
    setFilters({
      limit: 12,
      offset: 0,
      search: '',
      status: '',
      priority: '',
      category_id: '',
      tag_id: '',
      sort_by: 'created_at',
      sort_order: 'desc',
    });
  };

  const handleToggleComplete = async (task) => {
    try {
      if (task.status === 'completed') {
        const reopened = await tasksApi.reopenTask(task.id);
        setTasks((prev) => prev.map((t) => (t.id === task.id ? reopened : t)));
        toast.info('Task reopened');
      } else {
        const completed = await tasksApi.markCompleted(task.id);
        setTasks((prev) => prev.map((t) => (t.id === task.id ? completed : t)));
        toast.success('Task marked as completed');
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update task status');
    }
  };

  const handleEdit = (task) => {
    setTaskToEdit(task);
    setIsModalOpen(true);
  };

  const handleDeletePrompt = (task) => {
    setTaskToDelete(task);
    setDeleteModalOpen(true);
  };

  const confirmDelete = async () => {
    if (!taskToDelete) return;
    setDeleting(true);
    try {
      await tasksApi.deleteTask(taskToDelete.id);
      toast.success('Task deleted successfully');
      setDeleteModalOpen(false);
      setTaskToDelete(null);
      loadTasks();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete task');
    } finally {
      setDeleting(false);
    }
  };

  // Pagination calculations
  const totalPages = Math.ceil(total / filters.limit) || 1;
  const currentPage = Math.floor(filters.offset / filters.limit) + 1;

  const handlePageChange = (newPage) => {
    if (newPage < 1 || newPage > totalPages) return;
    setFilters((prev) => ({
      ...prev,
      offset: (newPage - 1) * prev.limit,
    }));
  };

  return (
    <div style={styles.container}>
      {/* Top Action Bar */}
      <div style={styles.actionBar}>
        <div>
          <h1 style={styles.pageTitle}>{isCEO ? 'Tasks' : 'My Assigned Tasks'}</h1>
          <p style={styles.pageSubtitle}>
            {isCEO
              ? 'Manage, assign, and track all organizational tasks'
              : 'View, progress, and complete tasks assigned to you'}
          </p>
        </div>

        <div style={styles.actionButtons}>
          <button
            className="btn btn-secondary"
            onClick={() => navigate('/kanban')}
            title="Switch to Kanban Board view"
          >
            <Kanban size={16} />
            <span>Kanban View</span>
          </button>
          {isCEO && (
            <button
              className="btn btn-primary"
              onClick={() => {
                setTaskToEdit(null);
                setIsModalOpen(true);
              }}
            >
              <Plus size={16} />
              <span>New Task</span>
            </button>
          )}
        </div>
      </div>

      {/* Filter & Search Bar */}
      <TaskFilters
        filters={filters}
        onFilterChange={handleFilterChange}
        onReset={handleResetFilters}
      />

      {/* Tasks Listing */}
      {loading ? (
        <LoadingScreen message="Loading tasks..." />
      ) : tasks.length === 0 ? (
        <EmptyState
          icon={CheckSquare}
          title="No tasks match your filters"
          description={
            isCEO
              ? 'Try clearing your filters or create a new task to get started.'
              : 'No tasks are currently assigned to you matching these filters.'
          }
          action={
            isCEO ? (
              <button
                className="btn btn-primary"
                onClick={() => {
                  setTaskToEdit(null);
                  setIsModalOpen(true);
                }}
              >
                <Plus size={16} />
                <span>Create Task</span>
              </button>
            ) : null
          }
        />
      ) : (
        <>
          <div style={styles.grid}>
            {tasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onEdit={handleEdit}
                onDelete={handleDeletePrompt}
                onToggleComplete={handleToggleComplete}
              />
            ))}
          </div>

          {/* Pagination Footer */}
          <div style={styles.paginationFooter}>
            <span style={styles.paginationInfo}>
              Showing {filters.offset + 1} to{' '}
              {Math.min(filters.offset + filters.limit, total)} of {total} tasks
            </span>

            <div style={styles.paginationControls}>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage <= 1}
              >
                <ChevronLeft size={16} />
                <span>Prev</span>
              </button>

              <span style={styles.pageIndicator}>
                Page {currentPage} of {totalPages}
              </span>

              <button
                className="btn btn-secondary btn-sm"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage >= totalPages}
              >
                <span>Next</span>
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </>
      )}

      {/* Create / Edit Modal */}
      <TaskModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        task={taskToEdit}
        onSuccess={loadTasks}
      />

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={confirmDelete}
        title="Delete Task"
        message={`Are you sure you want to delete "${taskToDelete?.title}"? All associated comments and activities will be permanently deleted.`}
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
    gap: '16px',
  },
  actionBar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: '16px',
    paddingBottom: '8px',
  },
  pageTitle: {
    fontSize: '24px',
    fontWeight: 800,
    color: '#f8fafc',
    margin: 0,
    letterSpacing: '-0.02em',
  },
  pageSubtitle: {
    fontSize: '14px',
    color: '#94a3b8',
    margin: '4px 0 0 0',
  },
  actionButtons: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
    gap: '16px',
  },
  paginationFooter: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: '16px',
    padding: '16px 0',
    marginTop: '12px',
    borderTop: '1px solid rgba(255, 255, 255, 0.08)',
  },
  paginationInfo: {
    fontSize: '13px',
    color: '#94a3b8',
  },
  paginationControls: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  pageIndicator: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#e2e8f0',
    padding: '0 4px',
  },
};
