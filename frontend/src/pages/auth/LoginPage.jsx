import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Lock, LogIn, Mail } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useToast } from '../../hooks/useToast';

export const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { login } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError('Please provide both email and password');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await login(email.trim(), password);
      toast.success('Welcome back!');
      navigate('/');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Invalid email or password';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 style={styles.title}>Sign in to your account</h2>
      <p style={styles.subtitle}>Enter your credentials to access your workspaces</p>

      {error && <div className="form-error" style={styles.errorBox}>{error}</div>}

      <form onSubmit={handleSubmit} style={styles.form}>
        <div className="form-group">
          <label className="form-label">Email Address</label>
          <div style={styles.inputWrapper}>
            <Mail size={16} color="#64748b" style={styles.inputIcon} />
            <input
              type="email"
              className="form-input"
              style={styles.input}
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Password</label>
          <div style={styles.inputWrapper}>
            <Lock size={16} color="#64748b" style={styles.inputIcon} />
            <input
              type="password"
              className="form-input"
              style={styles.input}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          style={{ width: '100%', marginTop: '8px', padding: '12px' }}
          disabled={loading}
        >
          <LogIn size={16} />
          <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
        </button>
      </form>

      <div style={styles.footer}>
        <span style={styles.footerText}>Don't have an account?</span>
        <Link to="/register" style={styles.link}>
          Create an account
        </Link>
      </div>
    </div>
  );
};

const styles = {
  title: {
    fontSize: '20px',
    fontWeight: 700,
    color: '#f8fafc',
    marginBottom: '6px',
    textAlign: 'center',
  },
  subtitle: {
    fontSize: '13px',
    color: '#94a3b8',
    marginBottom: '24px',
    textAlign: 'center',
  },
  errorBox: {
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.25)',
    borderRadius: '8px',
    padding: '10px 14px',
    marginBottom: '16px',
    fontSize: '13px',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  inputWrapper: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  },
  inputIcon: {
    position: 'absolute',
    left: '12px',
    pointerEvents: 'none',
  },
  input: {
    paddingLeft: '38px',
  },
  footer: {
    marginTop: '24px',
    textAlign: 'center',
    fontSize: '13px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '6px',
  },
  footerText: {
    color: '#94a3b8',
  },
  link: {
    fontWeight: 600,
  },
};
