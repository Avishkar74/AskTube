// VideoPage.tsx - Updated with proper JSX and reportStatus prop
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Loader, Share2, BookOpen, MessageSquare, Upload } from 'lucide-react';
import VideoPlayer from '../components/VideoPlayer';
import ChatInterface from '../components/ChatInterface';
import NotesView from '../components/NotesView';
import UploadNotesView from '../components/UploadNotesView';
import TranscriptView from '../components/TranscriptView';
import { getReport, downloadAiNotesPdf, downloadUploadedNotesPdf } from '../services/api';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/Tabs';
import Button from '../components/ui/Button';

interface Report {
    _id: string;
    youtube_url: string;
    title?: string;
    summary?: string;
    notes?: string;
    transcript?: any[];
    status: 'queued' | 'running' | 'succeeded' | 'failed';
}

const VideoPage: React.FC = () => {
    const { reportId } = useParams<{ reportId: string }>();
    const [report, setReport] = useState<Report | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('chat');
    const [currentTime, setCurrentTime] = useState(0);
    const [seekTo, setSeekTo] = useState<number | null>(null);

    useEffect(() => {
        if (!reportId) return;

        const fetchReportData = async () => {
            try {
                const data = await getReport(reportId);
                setReport(data);
            } catch (error) {
                console.error('Failed to fetch report:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchReportData();
        const interval = setInterval(fetchReportData, 5000);
        return () => clearInterval(interval);
    }, [reportId]);

    const handleProgress = (state: { playedSeconds: number }) => {
        setCurrentTime(state.playedSeconds);
    };

    const handleSeek = (time: number) => {
        setSeekTo(time);
        // Reset seekTo after a short delay to allow re-seeking to same timestamp
        setTimeout(() => setSeekTo(null), 100);
    };

    const handleDownloadAiNotesPdf = async () => {
        if (!reportId) return;
        try {
            await downloadAiNotesPdf(reportId);
        } catch (error) {
            console.error('Failed to download AI notes PDF:', error);
        }
    };

    const handleDownloadUploadedNotesPdf = async () => {
        if (!reportId) return;
        try {
            await downloadUploadedNotesPdf(reportId);
        } catch (error) {
            console.error('Failed to download uploaded notes PDF:', error);
        }
    };

    if (isLoading) {
        return (
            <div className="h-screen bg-bg flex flex-col items-center justify-center text-white">
                <Loader className="w-10 h-10 animate-spin text-primary mb-4" />
                <p className="text-zinc-400">Loading learning environment...</p>
            </div>
        );
    }

    if (!report) {
        return (
            <div className="h-screen bg-bg flex flex-col items-center justify-center text-white">
                <p className="text-error mb-4">Report not found</p>
                <Link to="/" className="text-primary hover:underline">Return to Dashboard</Link>
            </div>
        );
    }

    // Extract video ID from URL if not present in report
    const videoId = report.youtube_url.split('v=')[1]?.split('&')[0] || '';

    return (
        <div className="h-screen bg-bg text-text flex flex-col overflow-hidden">
            {/* Minimal Header */}
            <header className="h-14 border-b border-white/5 flex items-center justify-between px-4 bg-surface/50 backdrop-blur-md z-10 shrink-0">
                <div className="flex items-center gap-4">
                    <Link to="/" className="p-2 hover:bg-white/10 rounded-lg transition-colors text-zinc-400 hover:text-white">
                        <ArrowLeft size={20} />
                    </Link>
                    <h1 className="font-semibold text-sm md:text-base truncate max-w-md text-zinc-200">
                        {report.title || 'Untitled Video'}
                    </h1>
                </div>
                <div className="flex items-center gap-2">
                    <Button variant="ghost" size="sm" icon={<Share2 size={18} />} />
                </div>
            </header>

            <div className="flex-1 flex overflow-hidden">
                {/* Left Column - Player & Transcript */}
                <div className="flex-1 flex flex-col min-w-0 bg-black relative">
                    <div className="aspect-video w-full bg-black shadow-2xl z-10">
                        <VideoPlayer
                            videoId={videoId}
                            onProgress={handleProgress}
                            onReady={() => { }}
                            seekTo={seekTo}
                        />
                    </div>
                    <div className="flex-1 overflow-y-auto border-t border-white/5 bg-surface/30 relative">
                        <div className="absolute inset-0">
                            {report.transcript && report.transcript.length > 0 ? (
                                <TranscriptView
                                    segments={report.transcript}
                                    currentTime={currentTime}
                                    onSegmentClick={handleSeek}
                                />
                            ) : (
                                <div className="flex flex-col items-center justify-center h-full text-zinc-500 p-8 text-center">
                                    {report.status === 'succeeded' ? (
                                        <p>No transcript available for this video.</p>
                                    ) : (
                                        <>
                                            <Loader className="animate-spin mb-2" />
                                            <p>Processing transcript...</p>
                                        </>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Column - Tabs */}
                <div className="w-[400px] border-l border-white/5 bg-surface flex flex-col shrink-0 shadow-2xl z-20">
                    <Tabs value={activeTab} onValueChange={setActiveTab} className="flex flex-col h-full">
                        <TabsList className="px-2 pt-2 bg-surface border-b border-white/5">
                            <TabsTrigger value="chat" className="flex-1 flex items-center justify-center gap-2">
                                <MessageSquare size={16} />
                                Chat
                            </TabsTrigger>
                            <TabsTrigger value="notes" className="flex-1 flex items-center justify-center gap-2">
                                <BookOpen size={16} />
                                Notes
                            </TabsTrigger>
                            <TabsTrigger value="upload" className="flex-1 flex items-center justify-center gap-2">
                                <Upload size={16} />
                                Uploads
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value="chat" className="flex-1 flex flex-col min-h-0">
                            <ChatInterface
                                videoId={videoId}
                                currentTime={currentTime}
                                onTimestampClick={handleSeek}
                            />
                        </TabsContent>

                        <TabsContent value="notes" className="flex-1 flex flex-col min-h-0">
                            <NotesView
                                videoId={videoId}
                                summary={report.summary || ''}
                                notes={report.notes || ''}
                                reportStatus={report.status}
                                onDownloadAiNotesPdf={handleDownloadAiNotesPdf}
                                onDownloadUploadedNotesPdf={handleDownloadUploadedNotesPdf}
                            />
                        </TabsContent>

                        <TabsContent value="upload" className="flex-1 flex flex-col min-h-0">
                            <UploadNotesView
                                videoId={videoId}
                                onDownloadPdf={handleDownloadUploadedNotesPdf}
                            />
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
        </div>
    );
};

export default VideoPage;
