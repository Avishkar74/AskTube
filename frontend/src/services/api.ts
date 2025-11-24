import axios from 'axios';
import type { ChatRequest, ChatResponse, TranscriptSegment } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add request interceptor
api.interceptors.request.use(
    (config) => {
        console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, config.data || '');
        return config;
    },
    (error) => {
        console.error('[API Request Error]', error);
        return Promise.reject(error);
    }
);

// Add response interceptor
api.interceptors.response.use(
    (response) => {
        const reqId = response.headers['x-request-id'];
        if (reqId) {
            console.log(`[API Response] ${response.status} ${response.config.url} (X-Request-ID: ${reqId})`, response.data);
        } else {
            console.log(`[API Response] ${response.status} ${response.config.url}`, response.data);
        }
        return response;
    },
    (error) => {
        const status = error.response?.status;
        const reqId = error.response?.headers?.['x-request-id'];
        console.error('[API Response Error]', status, reqId ? `(X-Request-ID: ${reqId})` : '', error.response?.data || error.message);
        return Promise.reject(error);
    }
);

export const processVideo = async (youtubeUrl: string) => {
    const response = await api.post('/process', { youtube_url: youtubeUrl });
    return response.data;
};

export const getTranscript = async (videoId: string): Promise<TranscriptSegment[]> => {
    const response = await api.get(`/videos/${videoId}/transcript`);
    return response.data; // Backend returns a list of segments
};

export const chatWithVideo = async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post('/chat', request);
    return response.data;
};

export const getChatHistory = async (videoId: string): Promise<any[]> => {
    const response = await api.get(`/chat/${videoId}/history`);
    return response.data;
};

export const getReports = async (limit = 10, offset = 0) => {
    const response = await api.get(`/reports?limit=${limit}&offset=${offset}`);
    return response.data;
};

export const getReport = async (reportId: string) => {
    const response = await api.get(`/reports/${reportId}`);
    return response.data;
};

export const getLocalIp = async () => {
    const response = await api.get('/notes/ip');
    return response.data.ip;
};

export const uploadNote = async (videoId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post(`/notes/${videoId}/upload`, formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

export const getNotes = async (videoId: string) => {
    const response = await api.get(`/notes/${videoId}`);
    return response.data;
};

export const importCourse = async (playlistUrl: string) => {
    const response = await api.post('/courses', { playlist_url: playlistUrl });
    return response.data;
};

export const getCourses = async (limit = 50, offset = 0) => {
    const response = await api.get(`/courses?limit=${limit}&offset=${offset}`);
    return response.data;
};

export const getCourse = async (courseId: string) => {
    const response = await api.get(`/courses/${courseId}`);
    return response.data;
};

export default api;
