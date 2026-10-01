import React, { useContext } from 'react';
import { AlertCircle, AlertTriangle, CheckCircle, Info, X } from 'lucide-react';
import { ToastContext } from '../../context/ToastContext';

export const ToastContainer = () => {
  const { toasts, removeToast } = useContext(ToastContext);

  if (!toasts || toasts.length === 0) return null;

  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircle size={18} color="#10b981" />;
      case 'error':
        return <AlertCircle size={18} color="#ef4444" />;
      case 'warning':
        return <AlertTriangle size={18} color="#f59e0b" />;
      default:
        return <Info size={18} color="#38bdf8" />;
    }
  };

  return (
    <div style={styles.container}>
      {toasts.map((toast) => (
        <div key={toast.id} style={{ ...styles.toast, ...styles[toast.type] }} className="animate-slide-up">
          <div style={styles.icon}>{getIcon(toast.type)}</div>
          <div style={styles.message}>{toast.message}</div>
          <button
            onClick={() => removeToast(toast.id)}
            style={styles.closeBtn}
            aria-label="Close notification"
          >
            <X size={15} />
          </button>
        </div>
      ))}
    </div>
  );
};

const styles = {
  container: {
    position: 'fixed',
    bottom: 24,
    right: 24,
    zIndex: 9999,
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
    maxWidth: 400,
    width: 'calc(100% - 48px)',
    pointerEvents: 'none',
  },
  toast: {
    display: 'flex',
    alignItems: 'center',
    padding: '12px 16px',
    borderRadius: '10px',
    background: 'rgba(21, 29, 47, 0.95)',
    backdropFilter: 'blur(16px)',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.5)',
    color: '#f8fafc',
    pointerEvents: 'auto',
    fontSize: '14px',
    fontWeight: 500,
  },
  icon: {
    display: 'flex',
    alignItems: 'center',
    marginRight: 12,
  },
  message: {
    flex: 1,
    lineHeight: 1.4,
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    color: '#94a3b8',
    cursor: 'pointer',
    padding: 4,
    display: 'flex',
    alignItems: 'center',
    marginLeft: 8,
    borderRadius: '4px',
    transition: 'color 150ms ease',
  },
  success: {
    borderLeft: '4px solid #10b981',
  },
  error: {
    borderLeft: '4px solid #ef4444',
  },
  warning: {
    borderLeft: '4px solid #f59e0b',
  },
  info: {
    borderLeft: '4px solid #38bdf8',
  },
};
