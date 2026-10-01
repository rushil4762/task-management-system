import React from 'react';
import { Inbox } from 'lucide-react';

export const EmptyState = ({
  icon: Icon = Inbox,
  title = 'No items found',
  description = 'There are no items to display right now.',
  action = null,
}) => {
  return (
    <div style={styles.container}>
      <div style={styles.iconWrapper}>
        <Icon size={32} color="#6366f1" />
      </div>
      <h4 style={styles.title}>{title}</h4>
      <p style={styles.description}>{description}</p>
      {action && <div style={styles.actionWrapper}>{action}</div>}
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '48px 24px',
    textAlign: 'center',
    background: 'rgba(18, 24, 38, 0.4)',
    border: '1px dashed rgba(255, 255, 255, 0.1)',
    borderRadius: '16px',
    margin: '16px 0',
  },
  iconWrapper: {
    width: '64px',
    height: '64px',
    borderRadius: '16px',
    background: 'rgba(99, 102, 241, 0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '16px',
  },
  title: {
    fontSize: '16px',
    fontWeight: 700,
    color: '#f8fafc',
    marginBottom: '8px',
  },
  description: {
    fontSize: '14px',
    color: '#94a3b8',
    maxWidth: '380px',
    lineHeight: 1.5,
  },
  actionWrapper: {
    marginTop: '20px',
  },
};
