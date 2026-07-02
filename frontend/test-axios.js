import axios from 'axios';
console.log('Axios version:', axios.VERSION);

const apiClient = axios.create({
  baseURL: 'https://httpbin.org',
});

apiClient.interceptors.request.use((config) => {
  if (config.headers) {
    config.headers.Authorization = `Bearer TEST_TOKEN`;
  }
  return config;
});

apiClient.get('/get').then(res => {
  console.log('Headers sent:', res.data.headers);
}).catch(console.error);
