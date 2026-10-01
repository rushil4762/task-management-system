import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Edit2, FolderTree, Plus, Trash2 } from 'lucide-react';
import { categoriesApi } from '../../api/categories';
import { Modal } from '../../components/common/Modal';
import { ConfirmModal } from '../../components/common/ConfirmModal';
import { EmptyState } from '../../components/common/EmptyState';
import { LoadingScreen } from '../../components/common/Spinner';
import { useToast } from '../../hooks/useToast';

export const CategoriesPage = () => {
  const navigate = useNavigate();
  const toast = useToast();

  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  // Create / Edit modal
  const [modalOpen, setModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');

  // Delete modal
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [categoryToDelete, setCategoryToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const loadCategories = async () => {
    setLoading(true);
    try {
      const data = await categoriesApi.getCategories();
      setCategories(data || []);
    } catch (err) {
      toast.error('Failed to load categories');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCategories();
  }, []);

  const handleOpenCreate = () => {
    setEditingCategory(null);
    setName('');
    setDescription('');
    setFormError('');
    setModalOpen(true);
  };

  const handleOpenEdit = (category) => {
    setEditingCategory(category);
    setName(category.name);
    setDescription(category.description || '');
    setFormError('');
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setFormError('Category name is required');
      return;
    }

    setSaving(true);
    setFormError('');

    try {
      if (editingCategory) {
        await categoriesApi.updateCategory(editingCategory.id, {
          name: name.trim(),
          description: description.trim() || null,
        });
        toast.success('Category updated successfully');
      } else {
        await categoriesApi.createCategory({
          name: name.trim(),
          description: description.trim() || null,
        });
        toast.success('Category created successfully');
      }
      setModalOpen(false);
      loadCategories();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to save category';
      setFormError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setSaving(false);
    }
  };

  const handleDeletePrompt = (category) => {
    setCategoryToDelete(category);
    setDeleteModalOpen(true);
  };

  const confirmDelete = async () => {
    if (!categoryToDelete) return;
    setDeleting(true);
    try {
      await categoriesApi.deleteCategory(categoryToDelete.id);
      toast.success('Category deleted');
      setDeleteModalOpen(false);
      setCategoryToDelete(null);
      loadCategories();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete category');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.actionBar}>
        <div>
          <h1 style={styles.pageTitle}>Categories</h1>
          <p style={styles.pageSubtitle}>
            Organize tasks into structured project folders and domains
          </p>
        </div>

        <button className="btn btn-primary" onClick={handleOpenCreate}>
          <Plus size={16} />
          <span>New Category</span>
        </button>
      </div>

      {/* Categories Grid */}
      {loading ? (
        <LoadingScreen message="Loading categories..." />
      ) : categories.length === 0 ? (
        <EmptyState
          icon={FolderTree}
          title="No categories created yet"
          description="Create your first category to group your tasks logically."
          action={
            <button className="btn btn-primary" onClick={handleOpenCreate}>
              <Plus size={16} />
              <span>Create Category</span>
            </button>
          }
        />
      ) : (
        <div style={styles.grid}>
          {categories.map((cat) => (
            <div key={cat.id} style={styles.categoryCard} className="card-hover">
              <div style={styles.cardTop}>
                <div style={styles.iconCircle}>
                  <FolderTree size={20} color="#06b6d4" />
                </div>
                <div style={styles.cardActions}>
                  <button
                    style={styles.actionBtn}
                    onClick={() => handleOpenEdit(cat)}
                    title="Edit category"
                  >
                    <Edit2 size={14} />
                  </button>
                  <button
                    style={{ ...styles.actionBtn, color: '#ef4444' }}
                    onClick={() => handleDeletePrompt(cat)}
                    title="Delete category"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              <div>
                <h3 style={styles.categoryName}>{cat.name}</h3>
                <p style={styles.categoryDesc}>
                  {cat.description || 'No description provided.'}
                </p>
              </div>

              <div style={styles.cardFooter}>
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={() => navigate(`/tasks?category_id=${cat.id}`)}
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
        title={editingCategory ? 'Edit Category' : 'Create Category'}
        maxWidth="460px"
      >
        <form onSubmit={handleSubmit}>
          {formError && (
            <div className="form-error" style={{ marginBottom: 16 }}>
              {formError}
            </div>
          )}

          <div className="form-group">
            <label className="form-label">
              Category Name <span style={{ color: 'var(--danger)' }}>*</span>
            </label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g., Marketing, Backend, Design"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea
              className="form-textarea"
              rows="3"
              placeholder="Optional description of this category..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
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
              {saving ? 'Saving...' : editingCategory ? 'Save Changes' : 'Create Category'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={confirmDelete}
        title="Delete Category"
        message={`Are you sure you want to delete "${categoryToDelete?.name}"? Tasks assigned to this category will become uncategorized.`}
        confirmText="Delete Category"
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
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: '16px',
  },
  categoryCard: {
    background: 'rgba(18, 24, 38, 0.75)',
    backdropFilter: 'blur(12px)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '14px',
    padding: '20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '14px',
  },
  cardTop: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  iconCircle: {
    width: '40px',
    height: '40px',
    borderRadius: '10px',
    background: 'rgba(6, 182, 212, 0.12)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardActions: {
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
  categoryName: {
    fontSize: '16px',
    fontWeight: 700,
    color: '#f8fafc',
    margin: '0 0 4px 0',
  },
  categoryDesc: {
    fontSize: '13px',
    color: '#94a3b8',
    lineHeight: 1.5,
    margin: 0,
  },
  cardFooter: {
    display: 'flex',
    justifyContent: 'flex-end',
    borderTop: '1px solid rgba(255, 255, 255, 0.05)',
    paddingTop: '12px',
    marginTop: 'auto',
  },
};
