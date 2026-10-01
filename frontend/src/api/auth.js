import client from './client';

export const authApi = {
  login: async (email, password) => {
    const response = await client.post('/auth/login', { email, password });
    return response.data;
  },

  register: async (name, email, password) => {
    const response = await client.post('/auth/register', { name, email, password });
    return response.data;
  },

  refresh: async (refreshToken) => {
    const response = await client.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },

  getMe: async () => {
    const response = await client.get('/auth/me');
    return response.data;
  },
};
