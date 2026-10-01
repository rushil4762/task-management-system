import React from 'react';
import { Layers } from 'lucide-react';
import { PRIORITY_CONFIG, TaskPriority } from '../../utils/constants';

export const PriorityDistribution = ({ priorities = {} }) => {
  const priorityList = [
    { key: TaskPriority.URGENT, label: 'Urgent', count: priorities.urgent || 0 },
    { key: TaskPriority.HIGH, label: 'High', count: priorities.high || 0 },
    { key: TaskPriority.MEDIUM, label: 'Medium', count: priorities.medium || 0 },
    { key: TaskPriority.LOW, label: 'Low', count: priorities.low || 0 },
  ];

  const total = priorityList.reduce((sum, p) => sum + p.count, 0);

  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Layers size={18} color="#6366f1" />
          <h4 style={styles.title}>Priority Breakdown</h4>
        </div>
        <span style={styles.totalBadge}>{total} Tasks</span>
      </div>

      <div style={styles.list}>
        {priorityList.map((item) => {
          const config = PRIORITY_CONFIG[item.key];
          const pct = total > 0 ? Math.round((item.count / total) * 100) : 0;

          return (
            <div key={item.key} style={styles.item}>
              <div style={styles.itemInfo}>
                <span style={{ ...styles.dot, backgroundColor: config.color }} />
                <span style={styles.label}>{item.label}</span>
                <span style={styles.count}>
                  {item.count} <span style={styles.pct}>({pct}%)</span>
                </span>
              </div>
              <div style={styles.track}>
                <div
                  style={{
                    ...styles.fill,
                    width: `${pct}%`,
                    backgroundColor: config.color,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const styles = {
  card: {
    background: 'rgba(18, 24, 38, 0.75)',
    backdropFilter: 'blur(12px)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '14px',
    padding: '20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  title: {
    fontSize: '15px',
    fontWeight: 700,
    color: '#f8fafc',
    margin: 0,
  },
  totalBadge: {
    fontSize: '12px',
    fontWeight: 600,
    color: '#94a3b8',
  },
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: '14px',
  },
  item: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  itemInfo: {
    display: 'flex',
    alignItems: 'center',
    fontSize: '13px',
  },
  dot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    marginRight: '8px',
  },
  label: {
    fontWeight: 500,
    color: '#e2e8f0',
    flex: 1,
  },
  count: {
    fontWeight: 700,
    color: '#f8fafc',
  },
  pct: {
    fontWeight: 400,
    color: '#64748b',
    fontSize: '11px',
  },
  track: {
    height: '6px',
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '9999px',
    overflow: 'hidden',
  },
  fill: {
    height: '100%',
    borderRadius: '9999px',
    transition: 'width 300ms ease',
  },
};
