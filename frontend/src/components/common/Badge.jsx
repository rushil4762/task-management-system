import React from 'react';
import { PRIORITY_CONFIG, STATUS_CONFIG } from '../../utils/constants';

export const StatusBadge = ({ status }) => {
  const config = STATUS_CONFIG[status] || {
    label: status,
    badgeClass: 'badge-pending',
  };

  return <span className={`badge ${config.badgeClass}`}>{config.label}</span>;
};

export const PriorityBadge = ({ priority }) => {
  const config = PRIORITY_CONFIG[priority] || {
    label: priority,
    badgeClass: 'badge-priority-medium',
  };

  return <span className={`badge ${config.badgeClass}`}>{config.label}</span>;
};

export const TagPill = ({ name }) => {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        borderRadius: '9999px',
        fontSize: '11px',
        fontWeight: 600,
        background: 'rgba(99, 102, 241, 0.12)',
        color: '#a5b4fc',
        border: '1px solid rgba(99, 102, 241, 0.25)',
      }}
    >
      #{name}
    </span>
  );
};

export const CategoryPill = ({ name }) => {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        borderRadius: '6px',
        fontSize: '11px',
        fontWeight: 600,
        background: 'rgba(6, 182, 212, 0.12)',
        color: '#67e8f9',
        border: '1px solid rgba(6, 182, 212, 0.25)',
      }}
    >
      📁 {name}
    </span>
  );
};
