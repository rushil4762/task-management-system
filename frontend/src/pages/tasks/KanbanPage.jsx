import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckSquare, ListFilter, Plus } from 'lucide-react';
import { tasksApi } from '../../api/tasks';
import { KanbanBoard } from '../../components/kanban/KanbanBoard';
import { TaskModal } from '../../components/tasks/TaskModal';
import { ConfirmModal } from '../../components/common/ConfirmModal';
import { LoadingScreen } from '../../components/common/Spinner';
import { useToast } from '../../hooks/useToast';
import { useAuth } from '../../hooks/useAuth';
import { TaskStatus } from '../../utils/constants';

export const KanbanPage = () => {
  const { isCEO } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();


  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [taskToEdit, setTaskToEdit] = useState(null);
  const [presetStatus, setPresetStatus] = useState(null);

  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [taskToDelete, setTaskToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const loadTasks = async () => {
    setLoading(true);
    try {
      // Load up to 100 active/pending tasks for the board
      const data = await tasksApi.getTasks({ limit: 100 });
      setTasks(data.items || []);
    } catch (err) {
      console.error('Failed to load board tasks:', err);
      toast.error('Unable to load board tasks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const handleMoveTask = async (taskId, newStatus) => {
    // Optimistic UI update
    setTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, status: newStatus } : t))
    );

    try {
      await tasksApi.patchTask(taskId, { status: newStatus });
      toast.success(`Task moved to ${newStatus.replace('_', ' ')}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to move task');
      loadTasks(); // rollback on failure
    }
  };

  const handleToggleComplete = async (task) => {
    try {
      if (task.status === TaskStatus.COMPLETED) {
        const reopened = await tasksApi.reopenTask(task.id);
        setTasks((prev) => prev.map((t) => (t.id === task.id ? reopened : t)));
        toast.info('Task reopened');
      } else {
        const completed = await tasksApi.markCompleted(task.id);
        setTasks((prev) => prev.map((t) => (t.id === task.id ? completed : t)));
        toast.success('Task marked as completed');
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update task');
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
      setTasks((prev) => prev.filter((t) => t.id !== taskToDelete.id));
      toast.success('Task deleted');
      setDeleteModalOpen(false);
      setTaskToDelete(null);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete task');
    } finally {
      setDeleting(false);
    }
  };

  const handleQuickAdd = (status) => {
    setTaskToEdit(null);
    setPresetStatus(status);
    setIsModalOpen(true);
  };

  return (
    <div style={styles.container}>
      {/* Top Header */}
      <div style={styles.actionBar}>
        <div>
          <h1 style={styles.pageTitle}>Kanban Board</h1>
          <p style={styles.pageSubtitle}>
            Visualize workflows, track progress, and transition task states seamlessly
          </p>
        </div>

        <div style={styles.actionButtons}>
          <button
            className="btn btn-secondary"
            onClick={() => navigate('/tasks')}
            title="Switch to List view"
          >
            <CheckSquare size={16} />
            <span>List View</span>
          </button>
          {isCEO && (
            <button
              className="btn btn-primary"
              onClick={() => {
                setTaskToEdit(null);
                setPresetStatus(null);
                setIsModalOpen(true);
              }}
            >
              <Plus size={16} />
              <span>New Task</span>
            </button>
          )}
        </div>
      </div>

      {/* Board Content */}
      {loading ? (
        <LoadingScreen message="Loading Kanban board..." />
      ) : (
        <KanbanBoard
          tasks={tasks}
          onEdit={handleEdit}
          onDelete={handleDeletePrompt}
          onToggleComplete={handleToggleComplete}
          onMoveTask={handleMoveTask}
          onQuickAdd={isCEO ? handleQuickAdd : undefined}
        />
      )}

      {/* Task Modal */}
      <TaskModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        task={
          taskToEdit
            ? taskToEdit
            : presetStatus
            ? { status: presetStatus }
            : null
        }
        onSuccess={loadTasks}
      />

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={confirmDelete}
        title="Delete Task"
        message={`Are you sure you want to delete "${taskToDelete?.title}"?`}
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
};
