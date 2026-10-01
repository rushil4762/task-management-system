import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  Calendar,
  CheckCircle2,
  Clock,
  Folder,
  History,
  ListTodo,
  TrendingUp,
} from 'lucide-react';
import { dashboardApi } from '../../api/dashboard';
import { StatCard } from '../../components/dashboard/StatCard';
import { CompletionTrendChart } from '../../components/dashboard/CompletionTrendChart';
import { PriorityDistribution } from '../../components/dashboard/PriorityDistribution';
import { LoadingScreen } from '../../components/common/Spinner';
import { useAuth } from '../../hooks/useAuth';
import { formatRelativeTime } from '../../utils/formatters';

export const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [summary, setSummary] = useState(null);
  const [recentActivities, setRecentActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadDashboardData = async () => {
    try {
      const [sumData, actData] = await Promise.all([
        dashboardApi.getSummary(),
        dashboardApi.getRecentActivity({ limit: 6 }),
      ]);
      setSummary(sumData);
      setRecentActivities(actData.items || []);
      setError('');
    } catch (err) {
      console.error('Failed to load dashboard:', err);
      setError('Unable to load dashboard metrics. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();

    const handleTaskEvent = () => loadDashboardData();
    window.addEventListener('task:created', handleTaskEvent);
    return () => {
      window.removeEventListener('task:created', handleTaskEvent);
    };
  }, []);

  if (loading) {
    return <LoadingScreen message="Loading productivity dashboard..." />;
  }

  if (error) {
    return (
      <div style={styles.errorBanner}>
        <AlertCircle size={20} color="#ef4444" />
        <span>{error}</span>
        <button className="btn btn-secondary btn-sm" onClick={loadDashboardData}>
          Retry
        </button>
      </div>
    );
  }

  const totals = summary?.total_tasks || {};
  const dueDates = summary?.due_date_summary || {};
  const completion = summary?.completion_metrics || {};
  const priorities = summary?.priority_summary || {};
  const categories = summary?.category_summary || [];
  const trend = summary?.completion_trend || [];

  return (
    <div style={styles.container}>
      {/* Welcome Banner */}
      <div style={styles.welcomeBanner}>
        <div>
          <h1 style={styles.welcomeTitle}>Welcome back, {user?.name || 'Explorer'}</h1>
          <p style={styles.welcomeSubtitle}>
            Here is your productivity overview and task status breakdown for today.
          </p>
        </div>
        <div style={styles.dateBadge}>
          <Calendar size={15} color="#818cf8" />
          <span>
            {new Date().toLocaleDateString('en-US', {
              weekday: 'short',
              month: 'short',
              day: 'numeric',
            })}
          </span>
        </div>
      </div>

      {/* Primary KPI Metric Cards */}
      <div style={styles.kpiGrid}>
        <StatCard
          title="Total Tasks"
          value={totals.total || 0}
          subtitle="All active & completed"
          icon={ListTodo}
          color="#818cf8"
          bgColor="rgba(99, 102, 241, 0.12)"
        />
        <StatCard
          title="Pending"
          value={totals.pending || 0}
          subtitle="Awaiting start"
          icon={Clock}
          color="#fbbf24"
          bgColor="rgba(245, 158, 11, 0.12)"
        />
        <StatCard
          title="In Progress"
          value={totals.in_progress || 0}
          subtitle="Currently underway"
          icon={TrendingUp}
          color="#38bdf8"
          bgColor="rgba(56, 189, 248, 0.12)"
        />
        <StatCard
          title="Completed"
          value={totals.completed || 0}
          subtitle={`${completion.completion_percentage || 0}% completion rate`}
          icon={CheckCircle2}
          color="#34d399"
          bgColor="rgba(16, 185, 129, 0.12)"
        />
        <StatCard
          title="Overdue"
          value={dueDates.overdue || 0}
          subtitle="Requires attention"
          icon={AlertCircle}
          color="#f87171"
          bgColor="rgba(239, 68, 68, 0.12)"
        />
      </div>

      {/* Visual Analytics Grid: Completion Chart + Priority Breakdown */}
      <div style={styles.chartsGrid}>
        <div style={styles.trendWrapper}>
          <CompletionTrendChart data={trend} />
        </div>
        <div style={styles.priorityWrapper}>
          <PriorityDistribution priorities={priorities} />
        </div>
      </div>

      {/* Two-column Bottom Section: Categories Breakdown + Recent Activity */}
      <div style={styles.bottomGrid}>
        {/* Category Distribution */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Folder size={18} color="#06b6d4" />
              <h4 style={styles.cardTitle}>Category Breakdown</h4>
            </div>
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => navigate('/categories')}
            >
              Manage
            </button>
          </div>

          <div style={styles.categoryList}>
            {categories.length === 0 ? (
              <div style={styles.emptyText}>No categories found</div>
            ) : (
              categories.map((c) => (
                <div
                  key={c.category_id ?? 'uncategorized'}
                  style={styles.categoryItem}
                  onClick={() =>
                    navigate(
                      c.category_id ? `/tasks?category_id=${c.category_id}` : '/tasks'
                    )
                  }
                >
                  <div style={styles.categoryInfo}>
                    <span style={styles.categoryName}>
                      {c.category_name || 'Uncategorized'}
                    </span>
                  </div>
                  <span style={styles.taskCountBadge}>{c.task_count} tasks</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Activity Stream */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <History size={18} color="#6366f1" />
              <h4 style={styles.cardTitle}>Recent Workspace Activity</h4>
            </div>
          </div>

          <div style={styles.activityList}>
            {recentActivities.length === 0 ? (
              <div style={styles.emptyText}>No recent activity</div>
            ) : (
              recentActivities.map((act) => (
                <div
                  key={act.id}
                  style={styles.activityItem}
                  onClick={() => navigate(`/tasks/${act.task_id}`)}
                >
                  <div style={styles.activityBullet} />
                  <div style={styles.activityContent}>
                    <p style={styles.activityDesc}>{act.description}</p>
                    <span style={styles.activityTime}>
                      {formatRelativeTime(act.created_at)}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
  },
  welcomeBanner: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: '16px',
    paddingBottom: '8px',
  },
  welcomeTitle: {
    fontSize: '24px',
    fontWeight: 800,
    color: '#f8fafc',
    margin: 0,
    letterSpacing: '-0.02em',
  },
  welcomeSubtitle: {
    fontSize: '14px',
    color: '#94a3b8',
    margin: '4px 0 0 0',
  },
  dateBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '6px 12px',
    background: 'rgba(99, 102, 241, 0.1)',
    border: '1px solid rgba(99, 102, 241, 0.2)',
    borderRadius: '9999px',
    fontSize: '12px',
    fontWeight: 600,
    color: '#c7d2fe',
  },
  kpiGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
  },
  chartsGrid: {
    display: 'grid',
    gridTemplateColumns: '2fr 1fr',
    gap: '20px',
  },
  trendWrapper: {
    minWidth: 0,
  },
  priorityWrapper: {
    minWidth: 0,
  },
  bottomGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '20px',
  },
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
  cardHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  cardTitle: {
    fontSize: '15px',
    fontWeight: 700,
    color: '#f8fafc',
    margin: 0,
  },
  categoryList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  categoryItem: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '10px 14px',
    background: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid rgba(255, 255, 255, 0.05)',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 150ms ease',
  },
  categoryInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  categoryName: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#e2e8f0',
  },
  taskCountBadge: {
    fontSize: '11px',
    fontWeight: 600,
    color: '#94a3b8',
    background: 'rgba(255, 255, 255, 0.05)',
    padding: '2px 8px',
    borderRadius: '9999px',
  },
  activityList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  activityItem: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '10px',
    padding: '8px',
    borderRadius: '6px',
    cursor: 'pointer',
    transition: 'background 150ms ease',
  },
  activityBullet: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    background: '#6366f1',
    marginTop: '6px',
    flexShrink: 0,
  },
  activityContent: {
    flex: 1,
    minWidth: 0,
  },
  activityDesc: {
    fontSize: '13px',
    color: '#cbd5e1',
    margin: 0,
    lineHeight: 1.4,
  },
  activityTime: {
    fontSize: '11px',
    color: '#64748b',
  },
  emptyText: {
    padding: '24px 0',
    textAlign: 'center',
    color: '#64748b',
    fontSize: '13px',
  },
  errorBanner: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px',
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.2)',
    borderRadius: '10px',
    color: '#f87171',
  },
};
