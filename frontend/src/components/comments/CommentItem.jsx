import React, { useState } from 'react';
import { Check, Edit2, Trash2, User, X } from 'lucide-react';
import { formatRelativeTime } from '../../utils/formatters';

export const CommentItem = ({
  comment,
  currentUserId,
  onUpdate,
  onDelete,
}) => {
  const isAuthor = comment.user_id === currentUserId;
  const [isEditing, setIsEditing] = useState(false);
  const [content, setContent] = useState(comment.content);
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    if (!content.trim() || content.trim() === comment.content) {
      setIsEditing(false);
      return;
    }
    setLoading(true);
    try {
      await onUpdate(comment.id, content.trim());
      setIsEditing(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.comment}>
      <div style={styles.header}>
        <div style={styles.authorArea}>
          <div style={styles.avatar}>
            <User size={14} color="#ffffff" />
          </div>
          <span style={styles.authorName}>
            {comment.user?.name || `User #${comment.user_id}`}
          </span>
          {isAuthor && <span style={styles.youBadge}>You</span>}
          <span style={styles.time}>{formatRelativeTime(comment.created_at)}</span>
        </div>

        {isAuthor && !isEditing && (
          <div style={styles.actions}>
            <button
              style={styles.actionBtn}
              onClick={() => setIsEditing(true)}
              title="Edit comment"
            >
              <Edit2 size={13} />
            </button>
            <button
              style={{ ...styles.actionBtn, color: '#ef4444' }}
              onClick={() => onDelete(comment.id)}
              title="Delete comment"
            >
              <Trash2 size={13} />
            </button>
          </div>
        )}
      </div>

      {isEditing ? (
        <div style={styles.editArea}>
          <textarea
            className="form-textarea"
            rows="2"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            disabled={loading}
            autoFocus
          />
          <div style={styles.editActions}>
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => {
                setContent(comment.content);
                setIsEditing(false);
              }}
              disabled={loading}
            >
              <X size={14} />
              Cancel
            </button>
            <button
              className="btn btn-primary btn-sm"
              onClick={handleSave}
              disabled={loading || !content.trim()}
            >
              <Check size={14} />
              Save
            </button>
          </div>
        </div>
      ) : (
        <p style={styles.content}>{comment.content}</p>
      )}
    </div>
  );
};

const styles = {
  comment: {
    background: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid rgba(255, 255, 255, 0.06)',
    borderRadius: '10px',
    padding: '14px',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  authorArea: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  avatar: {
    width: '24px',
    height: '24px',
    borderRadius: '50%',
    background: '#334155',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  authorName: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#f8fafc',
  },
  youBadge: {
    fontSize: '10px',
    fontWeight: 600,
    background: 'rgba(99, 102, 241, 0.2)',
    color: '#a5b4fc',
    padding: '1px 6px',
    borderRadius: '9999px',
  },
  time: {
    fontSize: '11px',
    color: '#64748b',
  },
  actions: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  actionBtn: {
    background: 'none',
    border: 'none',
    color: '#94a3b8',
    cursor: 'pointer',
    padding: '4px',
    borderRadius: '4px',
    display: 'flex',
    alignItems: 'center',
    transition: 'color 150ms ease',
  },
  content: {
    fontSize: '13px',
    color: '#cbd5e1',
    lineHeight: 1.5,
    margin: 0,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
  editArea: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  editActions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '8px',
  },
};
