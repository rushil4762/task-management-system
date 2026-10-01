import client from './client';

export const dashboardApi = {
  getSummary: async () => {
    const response = await client.get('/dashboard/summary');
    return response.data;
  },

  getCompletionTrend: async (params = {}) => {
    const response = await client.get('/dashboard/completion-trend', { params });
    return response.data;
  },

  getRecentActivity: async (params = {}) => {
    const response = await client.get('/dashboard/recent-activity', { params });
    return response.data;
  },
};
