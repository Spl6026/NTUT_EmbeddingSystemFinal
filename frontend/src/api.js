import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
});

export const getImageUrl = (path) => {
    if (!path) return '';
    if (path.startsWith('http')) return path;
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    const cleanBase = API_BASE_URL.replace(/\/$/, '');
    return `${cleanBase}${cleanPath}`;
};

export default apiClient;