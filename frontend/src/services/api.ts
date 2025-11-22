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

export const chatWithVideoStream = async (
    request: ChatRequest,
    onChunk: (chunk: string) => void,
    onMeta: (meta: any) => void,
    onCitations: (citations: any[]) => void
): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
    });

    if (!response.body) throw new Error('No response body');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
            if (!line.trim()) continue;
            try {
                const data = JSON.parse(line);
                switch (data.type) {
                    case 'meta':
                        onMeta(data.data);
                        break;
                    case 'citations':
                        onCitations(data.data);
                        break;
                    case 'chunk':
                        onChunk(data.data);
                        break;
                    case 'done':
                        return;
                }
            } catch (e) {
                console.error('Error parsing stream line:', e);
            }
        }
    }
};

export const getReports = async (limit = 10, offset = 0) => {
    const response = await api.get(`/reports?limit=${limit}&offset=${offset}`);
    return response.data;
};

export const getReport = async (reportId: string) => {
    const response = await api.get(`/reports/${reportId}`);
    return response.data;
};

export default api;
