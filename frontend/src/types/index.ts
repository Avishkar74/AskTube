export interface Citation {
    chunk_index: number;
    text: string;
    start_sec: number;
    end_sec: number;
    score?: number;
}

export interface ChatResponse {
    answer: string;
    citations?: Citation[];
    meta?: Record<string, unknown>;
}

export interface ChatRequest {
    video_id?: string;
    youtube_url?: string;
    message: string;
    window?: number;
    use_rag?: boolean;
    top_k?: number;
    backend?: 'ollama' | 'gemini';
    model?: string;
}

export interface VideoMetadata {
    video_id: string;
    title: string;
    channel: string;
    thumbnail_url: string;
    duration: number;
}

export interface TranscriptSegment {
    text: string;
    start: number;
    duration: number;
}
