// VideoPage.tsx - Updated with proper JSX and reportStatus prop
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Loader } from 'lucide-react';
import VideoPlayer from '../components/VideoPlayer';
import ChatInterface from '../components/ChatInterface';
import NotesView from '../components/NotesView';
import { getReport, downloadAiNotesPdf, downloadUploadedNotesPdf } from '../services/api';

const VideoPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const [videoId, setVideoId] = useState('');
    const [currentTime, setCurrentTime] = useState(0);
    const [seekTo, setSeekTo] = useState<number | null>(null);
    const [activeTab, setActiveTab] = useState<'chat' | 'notes'>('chat');
    const [report, setReport] = useState<any>({});

    // Resizable sidebar state
    const [sidebarWidth, setSidebarWidth] = useState(400);
    const [isResizing, setIsResizing] = useState(false);

    // Fetch report data
    useEffect(() => {
        const fetchData = async (reportId: string) => {
            console.log(`[VideoPage] Fetching data for report: ${reportId}`);
            try {
                const reportData = await getReport(reportId);
                console.log('[VideoPage] Report data loaded:', reportData);
                setReport(reportData);
                const vidId = reportData.video_id || extractVideoId(reportData.youtube_url);
                console.log(`[VideoPage] Resolved video ID: ${vidId}`);
                setVideoId(vidId);
            } catch (error) {
                console.error('[VideoPage] Error fetching video data:', error);
            }
        };
        if (id) fetchData(id);
    }, [id]);

    // Handle resizing of sidebar
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!isResizing) return;
            const newWidth = window.innerWidth - e.clientX;
            if (newWidth >= 300 && newWidth <= window.innerWidth * 0.5) {
                setSidebarWidth(newWidth);
            }
        };
        const handleMouseUp = () => {
            setIsResizing(false);
            document.body.style.cursor = 'default';
        };
        if (isResizing) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = 'col-resize';
        }
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isResizing]);

    const extractVideoId = (url: string) => {
        if (!url) return '';
        const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
        const match = url.match(regExp);
        return match && match[2].length === 11 ? match[2] : '';
    };

    const handleProgress = (state: { playedSeconds: number }) => {
        setCurrentTime(state.playedSeconds);
    };

    const handleSeek = (time: number) => {
        setSeekTo(time);
        setTimeout(() => setSeekTo(null), 100);
    };

    const handleDownloadAiNotesPdf = async () => {
        if (id) {
            try {
                await downloadAiNotesPdf(id);
            } catch (error) {
                console.error('Failed to download AI notes PDF:', error);
                alert('Failed to download AI notes PDF. Please try again.');
            }
        }
    };

    const handleDownloadUploadedNotesPdf = async () => {
        if (id) {
            try {
                await downloadUploadedNotesPdf(id);
            } catch (error) {
                console.error('Failed to download uploaded notes PDF:', error);
                alert('This video has no uploaded notes yet.');
            }
        }
    };

    if (!report || Object.keys(report).length === 0) {
        return (
            <div className="flex flex-col justify-center items-center h-screen bg-zinc-950 text-zinc-400 gap-4">
                <Loader className="animate-spin text-white" size={32} />
                <p className="text-lg font-medium">Fetching video details...</p>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-screen bg-zinc-950 text-zinc-100 font-sans overflow-hidden selection:bg-zinc-800 selection:text-white">
            {/* Header - Glassmorphism */}
            <header className="absolute top-0 left-0 right-0 h-16 bg-zinc-950/80 backdrop-blur-md border-b border-zinc-800/50 flex items-center px-6 gap-4 z-50">
                <Link to="/" className="p-2 hover:bg-zinc-800/50 rounded-full transition-all text-zinc-400 hover:text-white group">
                    <ArrowLeft size={20} className="group-hover:-translate-x-0.5 transition-transform" />
                </Link>
                <h1 className="text-xl font-bold tracking-tight text-white/90 uppercase">AskTube</h1>
            </header>

            {/* Main Content */}
            <div className="flex-1 flex overflow-hidden pt-16 pb-8 relative">
                {/* Left Panel: Video */}
                <div className="flex-1 bg-black flex flex-col justify-center relative border-r border-zinc-800/50 p-6 min-w-0">
                    <div className="w-full h-full border border-zinc-800/50 rounded-xl overflow-hidden shadow-2xl shadow-black/50">
                        <VideoPlayer videoId={videoId} onProgress={handleProgress} onReady={() => { }} seekTo={seekTo} />
                    </div>
                </div>

                {/* Resizer Handle */}
                <div
                    className="w-1 hover:w-1.5 -ml-0.5 bg-transparent hover:bg-zinc-700/50 cursor-col-resize transition-all z-40 flex items-center justify-center group"
                    onMouseDown={() => setIsResizing(true)}
                >
                    <div className="h-12 w-0.5 bg-zinc-700/50 group-hover:bg-zinc-400 rounded-full transition-colors" />
                </div>

                {/* Right Panel: Tabs */}
                <div className="bg-zinc-950 flex flex-col z-20 shrink-0" style={{ width: sidebarWidth }}>
                    {/* Tab Headers */}
                    <div className="flex border-b border-zinc-800/50 shrink-0 px-4 pt-2 gap-2">
                        <button
                            onClick={() => setActiveTab('chat')}
                            className={`flex-1 pb-3 text-xs font-bold uppercase tracking-wider transition-all border-b-2 ${activeTab === 'chat' ? 'border-white text-white' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}
                        >
                            Chat
                        </button>
                        <button
                            onClick={() => setActiveTab('notes')}
                            className={`flex-1 pb-3 text-xs font-bold uppercase tracking-wider transition-all border-b-2 ${activeTab === 'notes' ? 'border-white text-white' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}
                        >
                            Upload Notes
                        </button>
                    </div>

                    {/* Tab Content */}
                    <div className="flex-1 overflow-y-auto relative bg-zinc-950 no-scrollbar">
                        {activeTab === 'chat' && (
                            <div className="h-full flex flex-col">
                                <ChatInterface videoId={videoId} currentTime={currentTime} onTimestampClick={handleSeek} />
                            </div>
                        )}
                        {activeTab === 'notes' && (
                            <NotesView
                                videoId={videoId}
                                summary={report?.artifacts?.summary || ''}
                                notes={report?.artifacts?.notes || ''}
                                reportStatus={report?.status || 'unknown'}
                                onDownloadAiNotesPdf={handleDownloadAiNotesPdf}
                                onDownloadUploadedNotesPdf={handleDownloadUploadedNotesPdf}
                            />
                        )}
                    </div>
                </div>
            </div>

            {/* Bottom Bar */}
            <div className="h-8 bg-zinc-950 border-t border-zinc-800/50 w-full shrink-0" />
        </div>
    );
};

export default VideoPage;
