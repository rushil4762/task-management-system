import React, { useEffect, useState } from 'react';
import { ArrowDownUp, Filter, RotateCcw, Search, X } from 'lucide-react';
import { categoriesApi } from '../../api/categories';
import { tagsApi } from '../../api/tags';
import { TaskPriority, TaskStatus } from '../../utils/constants';

export const TaskFilters = ({ filters, onFilterChange, onReset }) => {
  const [categories, setCategories] = useState([]);
  const [tags, setTags] = useState([]);

  useEffect(() => {
    const loadMetadata = async () => {
      try {
        const [cats, tgs] = await Promise.all([
          categoriesApi.getCategories(),
          tagsApi.getTags(),
        ]);
        setCategories(cats || []);
        setTags(tgs || []);
      } catch {
        // silent fail
      }
    };
    loadMetadata();
  }, []);

  const handleChange = (key, value) => {
    onFilterChange({ ...filters, [key]: value || undefined, offset: 0 });
  };

  const hasActiveFilters =
    filters.search ||
    filters.status ||
    filters.priority ||
    filters.category_id ||
    filters.tag_id ||
    filters.sort_by !== 'created_at' ||
    filters.sort_order !== 'desc';

  return (
    <div style={styles.container}>
      {/* Search Input */}
      <div style={styles.searchWrapper}>
        <Search size={16} color="#64748b" style={styles.searchIcon} />
        <input
          type="text"
          className="form-input"
          style={styles.searchInput}
          placeholder="Search tasks by title or description..."
          value={filters.search || ''}
          onChange={(e) => handleChange('search', e.target.value)}
        />
        {filters.search && (
          <button
            style={styles.clearSearchBtn}
            onClick={() => handleChange('search', '')}
            aria-label="Clear search"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Filter Row */}
      <div style={styles.filterRow}>
        {/* Status */}
        <select
          className="form-select"
          style={styles.select}
          value={filters.status || ''}
          onChange={(e) => handleChange('status', e.target.value)}
        >
          <option value="">All Statuses</option>
          <option value={TaskStatus.PENDING}>Pending</option>
          <option value={TaskStatus.IN_PROGRESS}>In Progress</option>
          <option value={TaskStatus.COMPLETED}>Completed</option>
          <option value={TaskStatus.CANCELLED}>Cancelled</option>
        </select>

        {/* Priority */}
        <select
          className="form-select"
          style={styles.select}
          value={filters.priority || ''}
          onChange={(e) => handleChange('priority', e.target.value)}
        >
          <option value="">All Priorities</option>
          <option value={TaskPriority.LOW}>Low</option>
          <option value={TaskPriority.MEDIUM}>Medium</option>
          <option value={TaskPriority.HIGH}>High</option>
          <option value={TaskPriority.URGENT}>Urgent</option>
        </select>

        {/* Category */}
        <select
          className="form-select"
          style={styles.select}
          value={filters.category_id || ''}
          onChange={(e) => handleChange('category_id', e.target.value)}
        >
          <option value="">All Categories</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>

        {/* Tag */}
        <select
          className="form-select"
          style={styles.select}
          value={filters.tag_id || ''}
          onChange={(e) => handleChange('tag_id', e.target.value)}
        >
          <option value="">All Tags</option>
          {tags.map((t) => (
            <option key={t.id} value={t.id}>
              #{t.name}
            </option>
          ))}
        </select>

        {/* Sort By */}
        <div style={styles.sortGroup}>
          <select
            className="form-select"
            style={styles.select}
            value={filters.sort_by || 'created_at'}
            onChange={(e) => handleChange('sort_by', e.target.value)}
          >
            <option value="created_at">Date Created</option>
            <option value="due_date">Due Date</option>
            <option value="priority">Priority</option>
            <option value="title">Title</option>
            <option value="status">Status</option>
          </select>

          <button
            type="button"
            className="btn btn-secondary btn-icon"
            onClick={() =>
              handleChange(
                'sort_order',
                filters.sort_order === 'asc' ? 'desc' : 'asc'
              )
            }
            title={`Sort order: ${filters.sort_order === 'asc' ? 'Ascending' : 'Descending'}`}
          >
            <ArrowDownUp size={16} />
          </button>
        </div>

        {/* Reset button */}
        {hasActiveFilters && (
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={onReset}
            style={{ color: '#f87171' }}
          >
            <RotateCcw size={14} />
            Reset
          </button>
        )}
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    marginBottom: '20px',
  },
  searchWrapper: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
    width: '100%',
  },
  searchIcon: {
    position: 'absolute',
    left: '12px',
    pointerEvents: 'none',
  },
  searchInput: {
    paddingLeft: '38px',
    paddingRight: '36px',
    height: '42px',
  },
  clearSearchBtn: {
    position: 'absolute',
    right: '10px',
    background: 'none',
    border: 'none',
    color: '#94a3b8',
    cursor: 'pointer',
    padding: '4px',
    borderRadius: '4px',
    display: 'flex',
    alignItems: 'center',
  },
  filterRow: {
    display: 'flex',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '10px',
  },
  select: {
    width: 'auto',
    minWidth: '140px',
    height: '38px',
    padding: '6px 12px',
  },
  sortGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
};
