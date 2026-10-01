import React from 'react';

export const Spinner = ({ size = 24, color = 'var(--primary)' }) => {
  return (
    <div
      style={{
        width: size,
        height: size,
        border: `3px solid rgba(255, 255, 255, 0.1)`,
        borderTopColor: color,
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
        display: 'inline-block',
      }}
    />
  );
};

export const LoadingScreen = ({ message = 'Loading...' }) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '260px',
        width: '100%',
        gap: '16px',
        color: 'var(--text-secondary)',
      }}
    >
      <Spinner size={36} />
      <span style={{ fontSize: '14px', fontWeight: 500 }}>{message}</span>
    </div>
  );
};
