import client from './client';

export const usersApi = {
  getEmployees: async () => {
    const response = await client.get('/users/employees');
    return response.data;
  },
};
