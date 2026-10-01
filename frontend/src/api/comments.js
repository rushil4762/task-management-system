import client from './client';

export const commentsApi = {
  getComments: async (taskId) => {
    const response = await client.get(`/tasks/${taskId}/comments`);
    return response.data;
  },

  addComment: async (taskId, content) => {
    const response = await client.post(`/tasks/${taskId}/comments`, { content });
    return response.data;
  },

  updateComment: async (commentId, content) => {
    const response = await client.put(`/comments/${commentId}`, { content });
    return response.data;
  },

  deleteComment: async (commentId) => {
    await client.delete(`/comments/${commentId}`);
  },
};
