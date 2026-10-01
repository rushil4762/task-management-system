import client from './client';

export const tagsApi = {
  getTags: async () => {
    const response = await client.get('/tags');
    return response.data;
  },

  getTag: async (id) => {
    const response = await client.get(`/tags/${id}`);
    return response.data;
  },

  createTag: async (tagData) => {
    const response = await client.post('/tags', tagData);
    return response.data;
  },

  updateTag: async (id, tagData) => {
    const response = await client.put(`/tags/${id}`, tagData);
    return response.data;
  },

  deleteTag: async (id) => {
    await client.delete(`/tags/${id}`);
  },
};
