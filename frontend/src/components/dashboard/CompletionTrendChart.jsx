import React, { useState } from 'react';
import { TrendingUp } from 'lucide-react';

export const CompletionTrendChart = ({ data = [] }) => {
  const [hoveredIndex, setHoveredIndex] = useState(null);

  if (!data || data.length === 0) {
    return (
      <div style={styles.chartCard}>
        <div style={styles.cardHeader}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <TrendingUp size={18} color="#10b981" />
            <h4 style={styles.cardTitle}>Productivity Completion Trend</h4>
          </div>
        </div>
        <div style={styles.empty}>No completion data in this period</div>
      </div>
    );
  }

  const maxVal = Math.max(...data.map((d) => d.completed), 1);
  const chartHeight = 160;

  return (
    <div style={styles.chartCard}>
      <div style={styles.cardHeader}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <TrendingUp size={18} color="#10b981" />
          <h4 style={styles.cardTitle}>Productivity Completion Trend</h4>
        </div>
        <span style={styles.subtitle}>Tasks completed per day</span>
      </div>

      <div style={styles.chartContainer}>
        {data.map((item, index) => {
          const heightPercent = (item.completed / maxVal) * 100;
          const isHovered = hoveredIndex === index;
          const dateLabel = new Date(item.date).toLocaleDateString('en-US', {
            month: 'numeric',
            day: 'numeric',
          });

          return (
            <div
              key={item.date}
              style={styles.barGroup}
              onMouseEnter={() => setHoveredIndex(index)}
              onMouseLeave={() => setHoveredIndex(null)}
            >
              {/* Tooltip */}
              {isHovered && (
                <div style={styles.tooltip}>
                  <div style={styles.tooltipDate}>{item.date}</div>
                  <div style={styles.tooltipVal}>
                    {item.completed} task{item.completed !== 1 ? 's' : ''} completed
                  </div>
                </div>
              )}

              {/* Bar */}
              <div style={styles.barTrack}>
                <div
                  style={{
                    ...styles.barFill,
                    height: `${Math.max(heightPercent, 4)}%`,
                    background: item.completed > 0 ? (isHovered ? '#34d399' : '#10b981') : 'rgba(255, 255, 255, 0.05)',
                  }}
                />
              </div>

              {/* Date Label */}
              <span style={styles.xLabel}>{dateLabel}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const styles = {
  chartCard: {
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
  subtitle: {
    fontSize: '12px',
    color: '#64748b',
  },
  chartContainer: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: '8px',
    height: '180px',
    paddingTop: '24px',
    paddingBottom: '8px',
    overflowX: 'auto',
  },
  barGroup: {
    flex: '1 1 0',
    minWidth: '24px',
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: '8px',
    position: 'relative',
    cursor: 'pointer',
  },
  barTrack: {
    width: '100%',
    maxWidth: '28px',
    height: '140px',
    background: 'rgba(255, 255, 255, 0.02)',
    borderRadius: '6px',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'flex-end',
    overflow: 'hidden',
  },
  barFill: {
    width: '100%',
    borderRadius: '6px',
    transition: 'all 200ms ease',
  },
  xLabel: {
    fontSize: '10px',
    color: '#64748b',
    fontWeight: 500,
    whiteSpace: 'nowrap',
  },
  tooltip: {
    position: 'absolute',
    bottom: 'calc(100% + 4px)',
    background: '#090d16',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    borderRadius: '6px',
    padding: '6px 10px',
    boxShadow: '0 8px 16px rgba(0, 0, 0, 0.5)',
    zIndex: 20,
    pointerEvents: 'none',
    whiteSpace: 'nowrap',
    textAlign: 'center',
  },
  tooltipDate: {
    fontSize: '11px',
    color: '#94a3b8',
  },
  tooltipVal: {
    fontSize: '12px',
    fontWeight: 700,
    color: '#34d399',
  },
  empty: {
    padding: '48px 16px',
    textAlign: 'center',
    color: '#64748b',
    fontSize: '13px',
  },
};
