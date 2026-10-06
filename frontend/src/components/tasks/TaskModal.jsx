import React, { useEffect, useState } from 'react';
import { categoriesApi } from '../../api/categories';
import { tagsApi } from '../../api/tags';
import { tasksApi } from '../../api/tasks';
import { usersApi } from '../../api/users';
import { useAuth } from '../../hooks/useAuth';
import { Modal } from '../common/Modal';
import { useToast } from '../../hooks/useToast';
import { TaskPriority, TaskStatus } from '../../utils/constants';

export const TaskModal = ({ isOpen, onClose, task = null, onSuccess }) => {
  const { isCEO } = useAuth();
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
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch available categories, tags, and employees when modal opens
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
      const promises = [categoriesApi.getCategories(), tagsApi.getTags()];
      if (isCEO) {
        promises.push(usersApi.getEmployees());
      }
      const [cats, tags, emps] = await Promise.all(promises);
      setCategories(cats || []);
      setAvailableTags(tags || []);
      if (emps) {
        setEmployees(emps);
      }
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
    if (isCEO && !title.trim()) {
      setError('Task title is required');
      return;
    }

    setLoading(true);
    setError('');

    try {
      if (isEdit) {
        if (isCEO) {
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
          await tasksApi.updateTask(task.id, payload);
        } else {
          // Employee can only update status
          await tasksApi.patchTask(task.id, { status });
        }
        toast.success('Task updated successfully');
      } else {
        const payload = {
          title: title.trim(),
          description: description.trim() ? description.trim() : null,
          status,
          priority,
          due_date: dueDate ? new Date(dueDate).toISOString() : null,
          category_id: categoryId ? parseInt(categoryId, 10) : null,
          tag_ids: selectedTagIds.length > 0 ? selectedTagIds : null,
          ...(isCEO && assignedToId ? { assigned_to_id: parseInt(assignedToId, 10) } : {}),
        };
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
      title={isEdit ? (isCEO ? 'Edit Task' : 'Update Task Status') : 'Create New Task'}
      maxWidth="620px"
    >
      <form onSubmit={handleSubmit}>
        {error && <div className="form-error" style={{ marginBottom: 16 }}>{error}</div>}

        <div className="form-group">
          <label className="form-label">
            Task Title {isCEO && <span style={{ color: 'var(--danger)' }}>*</span>}
          </label>
          <input
            type="text"
            className="form-input"
            placeholder="e.g., Implement OAuth2 integration"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required={isCEO}
            disabled={!isCEO && isEdit}
            autoFocus={isCEO}
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
            disabled={!isCEO && isEdit}
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
              {isCEO && <option value={TaskStatus.CANCELLED}>Cancelled</option>}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Priority</label>
            <select
              className="form-select"
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              disabled={!isCEO && isEdit}
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
              disabled={!isCEO && isEdit}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Category</label>
            <select
              className="form-select"
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              disabled={!isCEO && isEdit}
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

        {isCEO && (
          <div className="form-group">
            <label className="form-label">Assign To</label>
            <select
              className="form-select"
              value={assignedToId}
              onChange={(e) => setAssignedToId(e.target.value)}
            >
              <option value="">Select Employee (Optional)</option>
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.name} ({emp.email})
                </option>
              ))}
            </select>
          </div>
        )}

        {availableTags.length > 0 && isCEO && (
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

