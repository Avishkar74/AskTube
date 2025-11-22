import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, MessageSquare, FileText, List } from 'lucide-react';
import VideoPlayer from '../components/VideoPlayer';
import TranscriptView from '../components/TranscriptView';
import ChatInterface from '../components/ChatInterface';
import NotesView from '../components/NotesView';
import { getReport, getTranscript, chatWithVideoStream } from '../services/api';
import type { TranscriptSegment } from '../types';

const VideoPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const [videoUrl, setVideoUrl] = useState('');
    const [videoId, setVideoId] = useState('');
    const [segments, setSegments] = useState<TranscriptSegment[]>([]);
    const [currentTime, setCurrentTime] = useState(0);
    const [seekTo, setSeekTo] = useState<number | null>(null);
    const [activeTab, setActiveTab] = useState<'transcript' | 'chat' | 'notes'>('transcript');
    const [report, setReport] = useState<any>(null);

    useEffect(() => {
        if (id) {
            fetchData(id);
        }
    }, [id]);

    const fetchData = async (reportId: string) => {
        console.log(`[VideoPage] Fetching data for report: ${reportId}`);
        try {
            const reportData = await getReport(reportId);
            console.log('[VideoPage] Report data loaded:', reportData);
            setReport(reportData);
            setVideoUrl(reportData.youtube_url);

            // Extract video ID from URL or report
            const vidId = reportData.video_id || extractVideoId(reportData.youtube_url);
            console.log(`[VideoPage] Resolved video ID: ${vidId}`);
            setVideoId(vidId);

            if (vidId) {
                const transcriptData = await getTranscript(vidId);
                console.log(`[VideoPage] Transcript loaded (${transcriptData.length} segments)`);
                setSegments(transcriptData);
            }
        } catch (error) {
            console.error('[VideoPage] Error fetching video data:', error);
        }
    };

    const extractVideoId = (url: string) => {
        const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
        const match = url.match(regExp);
        return (match && match[2].length === 11) ? match[2] : '';
    };

    const handleProgress = (state: { playedSeconds: number }) => {
        setCurrentTime(state.playedSeconds);
    };

    const handleSeek = (time: number) => {
        setSeekTo(time);
        // Reset seekTo after a short delay to allow re-seeking to same timestamp
        setTimeout(() => setSeekTo(null), 100);
    };

    const handleDownloadPdf = () => {
        if (id) {
            window.open(`http://localhost:8000/api/v1/reports/${id}/download?type=pdf`, '_blank');
        }
    };

    const [chatMessages, setChatMessages] = useState<{ role: 'user' | 'ai'; content: string; citations?: any[] }[]>([]);
    const [isChatLoading, setIsChatLoading] = useState(false);

    const handleSendMessage = async (message: string) => {
        const userMessage = { role: 'user' as const, content: message };
        setChatMessages((prev) => [...prev, userMessage]);
        setIsChatLoading(true);

        // Create placeholder for AI message
        const aiMessagePlaceholder = { role: 'ai' as const, content: '', citations: [] };
        setChatMessages((prev) => [...prev, aiMessagePlaceholder]);

        try {
            console.log('[VideoPage] Sending message (stream):', message);
            let currentContent = '';

            await chatWithVideoStream(
                {
                    video_id: videoId,
                    message: message,
                    use_rag: true,
                },
                (chunk: string) => {
                    currentContent += chunk;
                    setChatMessages((prev) => {
                        const newMessages = [...prev];
                        const lastMsg = newMessages[newMessages.length - 1];
                        if (lastMsg.role === 'ai') {
                            lastMsg.content = currentContent;
                        }
                        return newMessages;
                    });
                },
                (meta: any) => {
                    console.log('[VideoPage] Stream meta:', meta);
                },
                (citations: any[]) => {
                    setChatMessages((prev) => {
                        const newMessages = [...prev];
                        const lastMsg = newMessages[newMessages.length - 1];
                        if (lastMsg.role === 'ai') {
                            lastMsg.citations = citations;
                        }
                        return newMessages;
                    });
                }
            );
        } catch (error) {
            console.error('[VideoPage] Chat error:', error);
            setChatMessages((prev) => {
                const newMessages = [...prev];
                const lastMsg = newMessages[newMessages.length - 1];
                if (lastMsg.role === 'ai') {
                    lastMsg.content += '\n\n[Error: Failed to generate response]';
                }
                return newMessages;
            });
        } finally {
            setIsChatLoading(false);
        }
    };

    if (!report) {
        return <div className="flex justify-center items-center h-screen">Loading...</div>;
    }

    return (
        <div className="flex flex-col h-screen bg-slate-50 dark:bg-slate-900">
            {/* Header */}
            <header className="bg-white dark:bg-slate-800 shadow-sm p-4 flex items-center gap-4 z-10 border-b border-slate-200 dark:border-slate-700">
                <Link to="/" className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-full transition-colors text-slate-500 hover:text-indigo-600">
                    <ArrowLeft size={20} />
                </Link>
                <h1 className="text-lg font-bold text-slate-900 dark:text-white truncate flex-1">
                    {report.title || 'Video Learning Session'}
                </h1>
                <div className="flex items-center gap-2">
                    {/* Placeholder for future actions like 'Share' or 'Settings' */}
                </div>
            </header>

            {/* Main Content */}
            <div className="flex-1 flex overflow-hidden">
                {/* Left Panel: Video */}
                <div className="flex-1 bg-black flex flex-col justify-center relative">
                    <div className="w-full h-full">
                        <VideoPlayer
                            url={videoUrl}
                            onProgress={handleProgress}
                            onReady={() => { }}
                            seekTo={seekTo}
                        />
                    </div>
                </div>

                {/* Right Panel: Tabs */}
                <div className="w-[450px] bg-white dark:bg-slate-800 border-l border-slate-200 dark:border-slate-700 flex flex-col shadow-xl z-20">
                    {/* Tab Headers */}
                    <div className="flex p-2 gap-2 bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700">
                        <button
                            onClick={() => setActiveTab('transcript')}
                            className={`flex-1 py-2 px-3 text-sm font-semibold rounded-lg flex items-center justify-center gap-2 transition-all ${activeTab === 'transcript'
                                ? 'bg-white dark:bg-slate-800 text-indigo-600 shadow-sm ring-1 ring-slate-200 dark:ring-slate-700'
                                : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800'
                                }`}
                        >
                            <List size={16} />
                            Transcript
                        </button>
                        <button
                            onClick={() => setActiveTab('chat')}
                            className={`flex-1 py-2 px-3 text-sm font-semibold rounded-lg flex items-center justify-center gap-2 transition-all ${activeTab === 'chat'
                                ? 'bg-white dark:bg-slate-800 text-indigo-600 shadow-sm ring-1 ring-slate-200 dark:ring-slate-700'
                                : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800'
                                }`}
                        >
                            <MessageSquare size={16} />
                            Chat
                        </button>
                        <button
                            onClick={() => setActiveTab('notes')}
                            className={`flex-1 py-2 px-3 text-sm font-semibold rounded-lg flex items-center justify-center gap-2 transition-all ${activeTab === 'notes'
                                ? 'bg-white dark:bg-slate-800 text-indigo-600 shadow-sm ring-1 ring-slate-200 dark:ring-slate-700'
                                : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800'
                                }`}
                        >
                            <FileText size={16} />
                            Notes
                        </button>
                    </div>

                    {/* Tab Content */}
                    <div className="flex-1 overflow-hidden relative bg-slate-50/50 dark:bg-slate-900/50">
                        {activeTab === 'transcript' && (
                            <TranscriptView
                                segments={segments}
                                currentTime={currentTime}
                                onSegmentClick={handleSeek}
                            />
                        )}
                        {activeTab === 'chat' && (
                            <div className="h-full flex flex-col">
                                <ChatInterface
                                    messages={chatMessages}
                                    onSendMessage={handleSendMessage}
                                    isLoading={isChatLoading}
                                    onTimestampClick={handleSeek}
                                />
                            </div>
                        )}
                        {activeTab === 'notes' && (
                            <NotesView
                                summary={report.artifacts?.summary || "Summary not available yet."}
                                notes={report.artifacts?.notes || "Detailed notes not available yet."}
                                onDownloadPdf={handleDownloadPdf}
                            />
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default VideoPage;
