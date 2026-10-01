import client from './client';

export const categoriesApi = {
  getCategories: async () => {
    const response = await client.get('/categories');
    return response.data;
  },

  getCategory: async (id) => {
    const response = await client.get(`/categories/${id}`);
    return response.data;
  },

  createCategory: async (categoryData) => {
    const response = await client.post('/categories', categoryData);
    return response.data;
  },

  updateCategory: async (id, categoryData) => {
    const response = await client.put(`/categories/${id}`, categoryData);
    return response.data;
  },

  deleteCategory: async (id) => {
    await client.delete(`/categories/${id}`);
  },
};
