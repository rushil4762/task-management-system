export const TaskStatus = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
};

export const TaskPriority = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  URGENT: 'urgent',
};

export const STATUS_CONFIG = {
  [TaskStatus.PENDING]: {
    label: 'Pending',
    badgeClass: 'badge-pending',
    color: '#fbbf24',
    bg: 'rgba(245, 158, 11, 0.15)',
  },
  [TaskStatus.IN_PROGRESS]: {
    label: 'In Progress',
    badgeClass: 'badge-in_progress',
    color: '#38bdf8',
    bg: 'rgba(56, 189, 248, 0.15)',
  },
  [TaskStatus.COMPLETED]: {
    label: 'Completed',
    badgeClass: 'badge-completed',
    color: '#34d399',
    bg: 'rgba(16, 185, 129, 0.15)',
  },
  [TaskStatus.CANCELLED]: {
    label: 'Cancelled',
    badgeClass: 'badge-cancelled',
    color: '#94a3b8',
    bg: 'rgba(148, 163, 184, 0.15)',
  },
};

export const PRIORITY_CONFIG = {
  [TaskPriority.LOW]: {
    label: 'Low',
    badgeClass: 'badge-priority-low',
    color: '#94a3b8',
  },
  [TaskPriority.MEDIUM]: {
    label: 'Medium',
    badgeClass: 'badge-priority-medium',
    color: '#60a5fa',
  },
  [TaskPriority.HIGH]: {
    label: 'High',
    badgeClass: 'badge-priority-high',
    color: '#fbbf24',
  },
  [TaskPriority.URGENT]: {
    label: 'Urgent',
    badgeClass: 'badge-priority-urgent',
    color: '#f87171',
  },
};
