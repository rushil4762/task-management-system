import React from 'react';
import { KanbanColumn } from './KanbanColumn';
import { TaskStatus } from '../../utils/constants';

export const KanbanBoard = ({
  tasks = [],
  onEdit,
  onDelete,
  onToggleComplete,
  onMoveTask,
  onQuickAdd,
}) => {
  const columns = [
    TaskStatus.PENDING,
    TaskStatus.IN_PROGRESS,
    TaskStatus.COMPLETED,
    TaskStatus.CANCELLED,
  ];

  // Group tasks by status
  const tasksByStatus = columns.reduce((acc, status) => {
    acc[status] = tasks.filter((t) => t.status === status);
    return acc;
  }, {});

  return (
    <div style={styles.board}>
      {columns.map((status) => (
        <KanbanColumn
          key={status}
          status={status}
          tasks={tasksByStatus[status] || []}
          onEdit={onEdit}
          onDelete={onDelete}
          onToggleComplete={onToggleComplete}
          onMoveTask={onMoveTask}
          onQuickAdd={onQuickAdd}
        />
      ))}
    </div>
  );
};

const styles = {
  board: {
    display: 'flex',
    gap: '16px',
    overflowX: 'auto',
    paddingBottom: '16px',
    width: '100%',
  },
};
