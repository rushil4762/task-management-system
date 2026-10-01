import React, { useEffect, useState } from 'react';
import { categoriesApi } from '../../api/categories';
import { tagsApi } from '../../api/tags';
import { tasksApi } from '../../api/tasks';
import { Modal } from '../common/Modal';
import { useToast } from '../../hooks/useToast';
import { TaskPriority, TaskStatus } from '../../utils/constants';

export const TaskModal = ({ isOpen, onClose, task = null, onSuccess }) => {
  const toast = useToast();
  const isEdit = !!task;

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState(TaskStatus.PENDING);
  const [priority, setPriority] = useState(TaskPriority.MEDIUM);
  const [dueDate, setDueDate] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [selectedTagIds, setSelectedTagIds] = useState([]);
  const [assignedToId, setAssignedToId] = useState('');

  const [categories, setCategories] = useState([]);
  const [availableTags, setAvailableTags] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch available categories and tags when modal opens
  useEffect(() => {
    if (isOpen) {
      loadDependencies();
      if (task) {
        setTitle(task.title || '');
        setDescription(task.description || '');
        setStatus(task.status || TaskStatus.PENDING);
        setPriority(task.priority || TaskPriority.MEDIUM);
        setDueDate(task.due_date ? new Date(task.due_date).toISOString().slice(0, 16) : '');
        setCategoryId(task.category_id ? String(task.category_id) : '');
        setSelectedTagIds(task.tags ? task.tags.map((t) => t.id) : []);
        setAssignedToId(task.assigned_to_id ? String(task.assigned_to_id) : '');
      } else {
        resetForm();
      }
      setError('');
    }
  }, [isOpen, task]);

  const resetForm = () => {
    setTitle('');
    setDescription('');
    setStatus(TaskStatus.PENDING);
    setPriority(TaskPriority.MEDIUM);
    setDueDate('');
    setCategoryId('');
    setSelectedTagIds([]);
    setAssignedToId('');
  };

  const loadDependencies = async () => {
    try {
      const [cats, tags] = await Promise.all([
        categoriesApi.getCategories(),
        tagsApi.getTags(),
      ]);
      setCategories(cats || []);
      setAvailableTags(tags || []);
    } catch {
      // Non-critical if tags fail
    }
  };

  const handleTagToggle = (tagId) => {
    setSelectedTagIds((prev) =>
      prev.includes(tagId) ? prev.filter((id) => id !== tagId) : [...prev, tagId]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Task title is required');
      return;
    }

    setLoading(true);
    setError('');

    const payload = {
      title: title.trim(),
      description: description.trim() ? description.trim() : null,
      status,
      priority,
      due_date: dueDate ? new Date(dueDate).toISOString() : null,
      category_id: categoryId ? parseInt(categoryId, 10) : null,
      tag_ids: selectedTagIds.length > 0 ? selectedTagIds : null,
      assigned_to_id: assignedToId ? parseInt(assignedToId, 10) : null,
    };

    try {
      if (isEdit) {
        await tasksApi.updateTask(task.id, payload);
        toast.success('Task updated successfully');
      } else {
        await tasksApi.createTask(payload);
        toast.success('Task created successfully');
      }
      onSuccess?.();
      onClose();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to save task';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? 'Edit Task' : 'Create New Task'}
      maxWidth="620px"
    >
      <form onSubmit={handleSubmit}>
        {error && <div className="form-error" style={{ marginBottom: 16 }}>{error}</div>}

        <div className="form-group">
          <label className="form-label">
            Task Title <span style={{ color: 'var(--danger)' }}>*</span>
          </label>
          <input
            type="text"
            className="form-input"
            placeholder="e.g., Implement OAuth2 integration"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            autoFocus
          />
        </div>

        <div className="form-group">
          <label className="form-label">Description</label>
          <textarea
            className="form-textarea"
            rows="3"
            placeholder="Provide context, acceptance criteria, or notes..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div className="form-group">
            <label className="form-label">Status</label>
            <select
              className="form-select"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value={TaskStatus.PENDING}>Pending</option>
              <option value={TaskStatus.IN_PROGRESS}>In Progress</option>
              <option value={TaskStatus.COMPLETED}>Completed</option>
              <option value={TaskStatus.CANCELLED}>Cancelled</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Priority</label>
            <select
              className="form-select"
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
            >
              <option value={TaskPriority.LOW}>Low</option>
              <option value={TaskPriority.MEDIUM}>Medium</option>
              <option value={TaskPriority.HIGH}>High</option>
              <option value={TaskPriority.URGENT}>Urgent</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div className="form-group">
            <label className="form-label">Due Date</label>
            <input
              type="datetime-local"
              className="form-input"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Category</label>
            <select
              className="form-select"
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
            >
              <option value="">None (Uncategorized)</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Assignee (User ID)</label>
          <input
            type="number"
            min="1"
            className="form-input"
            placeholder="Assignee User ID (optional)"
            value={assignedToId}
            onChange={(e) => setAssignedToId(e.target.value)}
          />
        </div>

        {availableTags.length > 0 && (
          <div className="form-group">
            <label className="form-label">Tags</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '4px' }}>
              {availableTags.map((tag) => {
                const isSelected = selectedTagIds.includes(tag.id);
                return (
                  <button
                    type="button"
                    key={tag.id}
                    onClick={() => handleTagToggle(tag.id)}
                    style={{
                      padding: '4px 10px',
                      borderRadius: '9999px',
                      fontSize: '12px',
                      fontWeight: 600,
                      cursor: 'pointer',
                      border: '1px solid',
                      borderColor: isSelected ? 'var(--primary)' : 'rgba(255, 255, 255, 0.1)',
                      background: isSelected ? 'rgba(99, 102, 241, 0.25)' : 'rgba(255, 255, 255, 0.05)',
                      color: isSelected ? '#ffffff' : '#94a3b8',
                      transition: 'all 150ms ease',
                    }}
                  >
                    #{tag.name}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '24px' }}>
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={loading}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Task'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
