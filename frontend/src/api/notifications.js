import client from './client';

export const notificationsApi = {
  getNotifications: async (params = {}) => {
    const response = await client.get('/notifications', { params });
    return response.data;
  },

  getUnreadCount: async () => {
    const response = await client.get('/notifications/unread-count');
    return response.data;
  },

  markAsRead: async (id) => {
    const response = await client.patch(`/notifications/${id}/read`);
    return response.data;
  },

  markAllAsRead: async () => {
    const response = await client.patch('/notifications/read-all');
    return response.data;
  },
};
