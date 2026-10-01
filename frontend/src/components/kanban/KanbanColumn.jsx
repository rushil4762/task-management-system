import React from 'react';
import { Plus } from 'lucide-react';
import { TaskCard } from '../tasks/TaskCard';
import { STATUS_CONFIG } from '../../utils/constants';

export const KanbanColumn = ({
  status,
  tasks = [],
  onEdit,
  onDelete,
  onToggleComplete,
  onMoveTask,
  onQuickAdd,
}) => {
  const config = STATUS_CONFIG[status] || {
    label: status,
    color: '#94a3b8',
    bg: 'rgba(255, 255, 255, 0.05)',
  };

  const otherStatuses = Object.keys(STATUS_CONFIG).filter((s) => s !== status);

  return (
    <div style={styles.column}>
      {/* Column Header */}
      <div style={styles.header}>
        <div style={styles.headerTitleArea}>
          <div style={{ ...styles.dot, backgroundColor: config.color }} />
          <h3 style={styles.title}>{config.label}</h3>
          <span style={styles.countBadge}>{tasks.length}</span>
        </div>
        {onQuickAdd && (
          <button
            style={styles.addBtn}
            onClick={() => onQuickAdd(status)}
            title={`Add task to ${config.label}`}
          >
            <Plus size={16} />
          </button>
        )}
      </div>

      {/* Task List */}
      <div style={styles.taskList}>
        {tasks.length === 0 ? (
          <div style={styles.emptySlot}>No tasks in {config.label}</div>
        ) : (
          tasks.map((task) => (
            <div key={task.id} style={styles.taskWrapper}>
              <TaskCard
                task={task}
                onEdit={onEdit}
                onDelete={onDelete}
                onToggleComplete={onToggleComplete}
                compact
              />
              {/* Quick Move Status Row */}
              <div style={styles.quickMoveRow}>
                <span style={styles.moveLabel}>Move to:</span>
                <div style={styles.moveButtons}>
                  {otherStatuses.map((s) => (
                    <button
                      key={s}
                      style={{
                        ...styles.moveBtn,
                        color: STATUS_CONFIG[s]?.color || '#94a3b8',
                      }}
                      onClick={() => onMoveTask(task.id, s)}
                      title={`Move to ${STATUS_CONFIG[s]?.label}`}
                    >
                      {STATUS_CONFIG[s]?.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

const styles = {
  column: {
    flex: '1 1 300px',
    minWidth: '290px',
    maxWidth: '360px',
    background: 'rgba(15, 23, 42, 0.6)',
    backdropFilter: 'blur(12px)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '14px',
    display: 'flex',
    flexDirection: 'column',
    maxHeight: 'calc(100vh - 180px)',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
  },
  headerTitleArea: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  dot: {
    width: '10px',
    height: '10px',
    borderRadius: '50%',
    boxShadow: '0 0 8px currentColor',
  },
  title: {
    fontSize: '15px',
    fontWeight: 700,
    color: '#f8fafc',
    margin: 0,
  },
  countBadge: {
    fontSize: '11px',
    fontWeight: 700,
    background: 'rgba(255, 255, 255, 0.08)',
    color: '#94a3b8',
    padding: '2px 8px',
    borderRadius: '9999px',
  },
  addBtn: {
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '6px',
    color: '#94a3b8',
    padding: '4px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 150ms ease',
  },
  taskList: {
    padding: '12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    overflowY: 'auto',
    flex: 1,
  },
  emptySlot: {
    border: '1px dashed rgba(255, 255, 255, 0.08)',
    borderRadius: '10px',
    padding: '32px 16px',
    textAlign: 'center',
    color: '#64748b',
    fontSize: '13px',
  },
  taskWrapper: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  quickMoveRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '0 4px',
  },
  moveLabel: {
    fontSize: '10px',
    color: '#64748b',
    fontWeight: 600,
    textTransform: 'uppercase',
  },
  moveButtons: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '4px',
  },
  moveBtn: {
    background: 'rgba(255, 255, 255, 0.04)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '4px',
    padding: '2px 6px',
    fontSize: '10px',
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 150ms ease',
  },
};
