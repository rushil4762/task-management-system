import React, { useEffect, useState } from 'react';
import { MessageSquare, Send } from 'lucide-react';
import { commentsApi } from '../../api/comments';
import { CommentItem } from './CommentItem';
import { ConfirmModal } from '../common/ConfirmModal';
import { useAuth } from '../../hooks/useAuth';
import { useToast } from '../../hooks/useToast';

export const CommentList = ({ taskId }) => {
  const { user } = useAuth();
  const toast = useToast();

  const [comments, setComments] = useState([]);
  const [newContent, setNewContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [commentToDelete, setCommentToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const loadComments = async () => {
    setLoading(true);
    try {
      const data = await commentsApi.getComments(taskId);
      setComments(data || []);
    } catch (err) {
      console.error('Failed to load comments:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (taskId) {
      loadComments();
    }
  }, [taskId]);

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newContent.trim()) return;

    setSubmitting(true);
    try {
      const created = await commentsApi.addComment(taskId, newContent.trim());
      setComments((prev) => [...prev, created]);
      setNewContent('');
      toast.success('Comment added');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add comment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateComment = async (commentId, content) => {
    try {
      const updated = await commentsApi.updateComment(commentId, content);
      setComments((prev) =>
        prev.map((c) => (c.id === commentId ? { ...c, ...updated } : c))
      );
      toast.success('Comment updated');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update comment');
    }
  };

  const handleDeletePrompt = (commentId) => {
    setCommentToDelete(commentId);
    setDeleteModalOpen(true);
  };

  const confirmDeleteComment = async () => {
    if (!commentToDelete) return;
    setDeleting(true);
    try {
      await commentsApi.deleteComment(commentToDelete);
      setComments((prev) => prev.filter((c) => c.id !== commentToDelete));
      toast.success('Comment deleted');
      setDeleteModalOpen(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete comment');
    } finally {
      setDeleting(false);
      setCommentToDelete(null);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.sectionHeader}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <MessageSquare size={18} color="#6366f1" />
          <h4 style={styles.title}>Comments ({comments.length})</h4>
        </div>
      </div>

      {/* New Comment Input */}
      <form onSubmit={handleAddComment} style={styles.inputArea}>
        <textarea
          className="form-textarea"
          rows="2"
          placeholder="Write a comment or update on this task..."
          value={newContent}
          onChange={(e) => setNewContent(e.target.value)}
          disabled={submitting}
        />
        <div style={styles.submitRow}>
          <button
            type="submit"
            className="btn btn-primary btn-sm"
            disabled={submitting || !newContent.trim()}
          >
            <Send size={14} />
            <span>{submitting ? 'Posting...' : 'Post Comment'}</span>
          </button>
        </div>
      </form>

      {/* Comments List */}
      <div style={styles.list}>
        {loading ? (
          <div style={styles.empty}>Loading comments...</div>
        ) : comments.length === 0 ? (
          <div style={styles.empty}>No comments yet. Start the conversation!</div>
        ) : (
          comments.map((comment) => (
            <CommentItem
              key={comment.id}
              comment={comment}
              currentUserId={user?.id}
              onUpdate={handleUpdateComment}
              onDelete={handleDeletePrompt}
            />
          ))
        )}
      </div>

      <ConfirmModal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={confirmDeleteComment}
        title="Delete Comment"
        message="Are you sure you want to delete this comment? This action cannot be undone."
        isLoading={deleting}
      />
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
    marginTop: '24px',
  },
  sectionHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: '12px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
  },
  title: {
    fontSize: '16px',
    fontWeight: 700,
    color: '#f8fafc',
    margin: 0,
  },
  inputArea: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  submitRow: {
    display: 'flex',
    justifyContent: 'flex-end',
  },
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  empty: {
    padding: '24px 16px',
    textAlign: 'center',
    color: '#64748b',
    fontSize: '13px',
    background: 'rgba(255, 255, 255, 0.02)',
    borderRadius: '8px',
    border: '1px dashed rgba(255, 255, 255, 0.06)',
  },
};
