import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Compass, Home } from 'lucide-react';

export const NotFoundPage = () => {
  const navigate = useNavigate();

  return (
    <div style={styles.container}>
      <div style={styles.content} className="animate-slide-up">
        <div style={styles.iconCircle}>
          <Compass size={40} color="#6366f1" />
        </div>
        <h1 style={styles.code}>404</h1>
        <h2 style={styles.title}>Page Not Found</h2>
        <p style={styles.desc}>
          The page or resource you are looking for does not exist or has been moved.
        </p>
        <button className="btn btn-primary" onClick={() => navigate('/')}>
          <Home size={16} />
          <span>Back to Dashboard</span>
        </button>
      </div>
    </div>
  );
};

const styles = {
  container: {
    minHeight: '70vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    textAlign: 'center',
    padding: '32px 16px',
  },
  content: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    maxWidth: '420px',
  },
  iconCircle: {
    width: '80px',
    height: '80px',
    borderRadius: '20px',
    background: 'rgba(99, 102, 241, 0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '20px',
  },
  code: {
    fontSize: '56px',
    fontWeight: 900,
    color: '#6366f1',
    lineHeight: 1,
    margin: '0 0 8px 0',
  },
  title: {
    fontSize: '22px',
    fontWeight: 700,
    color: '#f8fafc',
    margin: '0 0 12px 0',
  },
  desc: {
    fontSize: '14px',
    color: '#94a3b8',
    lineHeight: 1.5,
    margin: '0 0 24px 0',
  },
};
