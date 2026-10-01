export const formatDate = (dateString, options = {}) => {
  if (!dateString) return 'No date';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return 'Invalid date';

    const defaultOptions = {
      month: 'short',
      day: 'numeric',
      year: d.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined,
      hour: options.includeTime ? '2-digit' : undefined,
      minute: options.includeTime ? '2-digit' : undefined,
    };

    return new Intl.DateTimeFormat('en-US', { ...defaultOptions, ...options }).format(d);
  } catch {
    return dateString;
  }
};

export const formatRelativeTime = (dateString) => {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    if (diffInSeconds < 60) return 'just now';
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours}h ago`;
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 30) return `${diffInDays}d ago`;

    return formatDate(dateString);
  } catch {
    return dateString;
  }
};

export const isDateOverdue = (dateString, status) => {
  if (!dateString) return false;
  if (status === 'completed' || status === 'cancelled') return false;
  return new Date(dateString) < new Date();
};
