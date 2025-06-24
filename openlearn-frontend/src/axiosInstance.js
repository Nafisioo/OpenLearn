import axios from 'axios';

const baseURL = 'http://127.0.0.1:8000';

const axiosInstance = axios.create({
  baseURL: baseURL,
  headers: {
    Authorization: localStorage.getItem('access')
      ? `Bearer ${localStorage.getItem('access')}`
      : null,
    'Content-Type': 'application/json',
    accept: 'application/json',
  },
});

axiosInstance.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;

    // Token expired?
    if (
      error.response?.status === 401 &&
      error.response.data.code === 'token_not_valid' &&
      !originalRequest._retry
    ) {
      originalRequest._retry = true;

      try {
        const refresh = localStorage.getItem('refresh');

        const res = await axios.post(`${baseURL}/api/token/refresh/`, {
          refresh: refresh,
        });

        localStorage.setItem('access', res.data.access);
        axiosInstance.defaults.headers['Authorization'] =
          'Bearer ' + res.data.access;
        originalRequest.headers['Authorization'] =
          'Bearer ' + res.data.access;

        return axiosInstance(originalRequest); // retry
      } catch (err) {
        console.log('🔒 Refresh token failed');
        localStorage.removeItem('access');
        localStorage.removeItem('refresh');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
