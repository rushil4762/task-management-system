import client from './client';

export const activitiesApi = {
  getTaskActivities: async (taskId, params = {}) => {
    const response = await client.get(`/tasks/${taskId}/activities`, { params });
    return response.data;
  },
};
