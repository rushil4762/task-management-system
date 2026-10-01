import React from 'react';

export const StatCard = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color = '#6366f1',
  bgColor = 'rgba(99, 102, 241, 0.12)',
}) => {
  return (
    <div style={styles.card} className="card-hover">
      <div style={styles.header}>
        <span style={styles.title}>{title}</span>
        {Icon && (
          <div style={{ ...styles.iconWrapper, background: bgColor }}>
            <Icon size={18} color={color} />
          </div>
        )}
      </div>
      <div style={{ ...styles.value, color }}>{value}</div>
      {subtitle && <div style={styles.subtitle}>{subtitle}</div>}
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
    gap: '6px',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  title: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#94a3b8',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
  },
  iconWrapper: {
    width: '34px',
    height: '34px',
    borderRadius: '10px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  value: {
    fontSize: '28px',
    fontWeight: 800,
    letterSpacing: '-0.02em',
    lineHeight: 1.2,
  },
  subtitle: {
    fontSize: '12px',
    color: '#64748b',
  },
};
