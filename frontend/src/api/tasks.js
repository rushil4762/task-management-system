import client from './client';

export const tasksApi = {
  getTasks: async (params = {}) => {
    const response = await client.get('/tasks', { params });
    return response.data;
  },

  getTask: async (id) => {
    const response = await client.get(`/tasks/${id}`);
    return response.data;
  },

  createTask: async (taskData) => {
    const response = await client.post('/tasks', taskData);
    return response.data;
  },

  updateTask: async (id, taskData) => {
    const response = await client.put(`/tasks/${id}`, taskData);
    return response.data;
  },

  patchTask: async (id, taskData) => {
    const response = await client.patch(`/tasks/${id}`, taskData);
    return response.data;
  },

  deleteTask: async (id) => {
    await client.delete(`/tasks/${id}`);
  },

  bulkDeleteTasks: async (taskIds) => {
    const response = await client.post('/tasks/bulk-delete', { task_ids: taskIds });
    return response.data;
  },

  markCompleted: async (id) => {
    const response = await client.patch(`/tasks/${id}/complete`);
    return response.data;
  },

  reopenTask: async (id) => {
    const response = await client.patch(`/tasks/${id}/reopen`);
    return response.data;
  },

  attachTags: async (id, tagIds) => {
    const response = await client.post(`/tasks/${id}/tags`, { tag_ids: tagIds });
    return response.data;
  },
};
