import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Edit2, Plus, Tag, Trash2 } from 'lucide-react';
import { tagsApi } from '../../api/tags';
import { Modal } from '../../components/common/Modal';
import { ConfirmModal } from '../../components/common/ConfirmModal';
import { EmptyState } from '../../components/common/EmptyState';
import { LoadingScreen } from '../../components/common/Spinner';
import { useToast } from '../../hooks/useToast';

export const TagsPage = () => {
  const navigate = useNavigate();
  const toast = useToast();

  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modal
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTag, setEditingTag] = useState(null);
  const [name, setName] = useState('');
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');

  // Delete modal
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [tagToDelete, setTagToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const loadTags = async () => {
    setLoading(true);
    try {
      const data = await tagsApi.getTags();
      setTags(data || []);
    } catch {
      toast.error('Failed to load tags');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTags();
  }, []);

  const handleOpenCreate = () => {
    setEditingTag(null);
    setName('');
    setFormError('');
    setModalOpen(true);
  };

  const handleOpenEdit = (tag) => {
    setEditingTag(tag);
    setName(tag.name);
    setFormError('');
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setFormError('Tag name is required');
      return;
    }

    setSaving(true);
    setFormError('');

    try {
      if (editingTag) {
        await tagsApi.updateTag(editingTag.id, { name: name.trim() });
        toast.success('Tag updated successfully');
      } else {
        await tagsApi.createTag({ name: name.trim() });
        toast.success('Tag created successfully');
      }
      setModalOpen(false);
      loadTags();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to save tag';
      setFormError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setSaving(false);
    }
  };

  const handleDeletePrompt = (tag) => {
    setTagToDelete(tag);
    setDeleteModalOpen(true);
  };

  const confirmDelete = async () => {
    if (!tagToDelete) return;
    setDeleting(true);
    try {
      await tagsApi.deleteTag(tagToDelete.id);
      toast.success('Tag deleted');
      setDeleteModalOpen(false);
      setTagToDelete(null);
      loadTags();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete tag');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.actionBar}>
        <div>
          <h1 style={styles.pageTitle}>Tags</h1>
          <p style={styles.pageSubtitle}>
            Create lightweight labels to cross-categorize and filter your tasks
          </p>
        </div>

        <button className="btn btn-primary" onClick={handleOpenCreate}>
          <Plus size={16} />
          <span>New Tag</span>
        </button>
      </div>

      {/* Tags Grid */}
      {loading ? (
        <LoadingScreen message="Loading tags..." />
      ) : tags.length === 0 ? (
        <EmptyState
          icon={Tag}
          title="No tags created yet"
          description="Tags help you categorize tasks across different categories and projects."
          action={
            <button className="btn btn-primary" onClick={handleOpenCreate}>
              <Plus size={16} />
              <span>Create Tag</span>
            </button>
          }
        />
      ) : (
        <div style={styles.grid}>
          {tags.map((tag) => (
            <div key={tag.id} style={styles.tagCard} className="card-hover">
              <div style={styles.tagHeader}>
                <div style={styles.tagBadge}>
                  <Tag size={14} color="#6366f1" />
                  <span style={styles.tagName}>#{tag.name}</span>
                </div>
                <div style={styles.tagActions}>
                  <button
                    style={styles.actionBtn}
                    onClick={() => handleOpenEdit(tag)}
                    title="Edit tag"
                  >
                    <Edit2 size={13} />
                  </button>
                  <button
                    style={{ ...styles.actionBtn, color: '#ef4444' }}
                    onClick={() => handleDeletePrompt(tag)}
                    title="Delete tag"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>

              <div style={styles.tagFooter}>
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={() => navigate(`/tasks?tag_id=${tag.id}`)}
                >
                  View Tasks
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingTag ? 'Edit Tag' : 'Create Tag'}
        maxWidth="400px"
      >
        <form onSubmit={handleSubmit}>
          {formError && (
            <div className="form-error" style={{ marginBottom: 16 }}>
              {formError}
            </div>
          )}

          <div className="form-group">
            <label className="form-label">
              Tag Name <span style={{ color: 'var(--danger)' }}>*</span>
            </label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g., bug, frontend, urgent"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 20 }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setModalOpen(false)}
              disabled={saving}
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving...' : editingTag ? 'Save Changes' : 'Create Tag'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={confirmDelete}
        title="Delete Tag"
        message={`Are you sure you want to delete the tag "#${tagToDelete?.name}"? It will be removed from all associated tasks.`}
        confirmText="Delete Tag"
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
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
    gap: '14px',
  },
  tagCard: {
    background: 'rgba(18, 24, 38, 0.75)',
    backdropFilter: 'blur(12px)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '12px',
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '14px',
  },
  tagHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  tagBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    background: 'rgba(99, 102, 241, 0.15)',
    border: '1px solid rgba(99, 102, 241, 0.3)',
    padding: '4px 10px',
    borderRadius: '9999px',
  },
  tagName: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#a5b4fc',
  },
  tagActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  actionBtn: {
    background: 'rgba(255, 255, 255, 0.04)',
    border: '1px solid rgba(255, 255, 255, 0.06)',
    borderRadius: '6px',
    color: '#94a3b8',
    padding: '5px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 150ms ease',
  },
  tagFooter: {
    display: 'flex',
    justifyContent: 'flex-end',
    borderTop: '1px solid rgba(255, 255, 255, 0.05)',
    paddingTop: '10px',
  },
};
