import React from 'react';
import { Outlet } from 'react-router-dom';
import { CheckSquare } from 'lucide-react';

export const AuthLayout = () => {
  return (
    <div style={styles.container}>
      <div style={styles.contentWrapper} className="animate-slide-up">
        {/* Brand Header */}
        <div style={styles.brand}>
          <div style={styles.logoIcon}>
            <CheckSquare size={28} color="#ffffff" />
          </div>
          <h1 style={styles.brandTitle}>TaskPulse</h1>
          <p style={styles.brandSubtitle}>
            Modern Collaborative Task Management & Productivity System
          </p>
        </div>

        {/* Card for Login / Register */}
        <div style={styles.card}>
          <Outlet />
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '24px 16px',
    background: 'radial-gradient(ellipse at 50% 20%, rgba(99, 102, 241, 0.15) 0%, transparent 60%), #090d16',
  },
  contentWrapper: {
    width: '100%',
    maxWidth: '440px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  brand: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    marginBottom: '28px',
  },
  logoIcon: {
    width: '54px',
    height: '54px',
    borderRadius: '14px',
    background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 0 25px rgba(99, 102, 241, 0.5)',
    marginBottom: '16px',
  },
  brandTitle: {
    fontSize: '26px',
    fontWeight: 800,
    color: '#ffffff',
    letterSpacing: '-0.02em',
    marginBottom: '6px',
  },
  brandSubtitle: {
    fontSize: '13px',
    color: '#94a3b8',
    maxWidth: '320px',
    lineHeight: 1.4,
  },
  card: {
    width: '100%',
    background: 'rgba(18, 24, 38, 0.85)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '20px',
    padding: '32px 28px',
    boxShadow: '0 20px 45px rgba(0, 0, 0, 0.6)',
  },
};
