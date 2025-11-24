import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChevronLeft, Check, Loader, Menu, X } from 'lucide-react';
import { getCourse } from '../services/api';
import VideoPlayer from '../components/VideoPlayer';
import ChatInterface from '../components/ChatInterface';
import NotesView from '../components/NotesView';
import { getReport, getTranscript } from '../services/api';

interface VideoInCourse {
    video_id: string;
    title: string;
    duration: number;
    thumbnail: string;
    order: number;
    report_id?: string;
    status?: string;
}

interface Course {
    _id: string;
    title: string;
    description?: string;
    thumbnail?: string;
    channel_name?: string;
    video_count: number;
    videos: VideoInCourse[];
}

const CoursePage: React.FC = () => {
    const { courseId } = useParams<{ courseId: string }>();
    const navigate = useNavigate();

    const [course, setCourse] = useState<Course | null>(null);
    const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
    const [activeTab, setActiveTab] = useState<'chat' | 'notes'>('chat');
    const [isLoading, setIsLoading] = useState(true);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);

    const [videoId, setVideoId] = useState('');
    const [report, setReport] = useState<any>(null);
    const [currentTime, setCurrentTime] = useState(0);
    const [seekTo, setSeekTo] = useState<number | null>(null);

    // Resizable sidebar state
    const [sidebarWidth, setSidebarWidth] = useState(450);
    const [isResizing, setIsResizing] = useState(false);

    useEffect(() => {
        if (courseId) {
            fetchCourse();
        }
    }, [courseId]);

    useEffect(() => {
        if (course && course.videos[currentVideoIndex]) {
            loadVideo(course.videos[currentVideoIndex]);
        }
    }, [currentVideoIndex, course]);

    // Handle resizing
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!isResizing) return;
            const newWidth = window.innerWidth - e.clientX;
            setSidebarWidth(Math.max(300, Math.min(800, newWidth)));
        };

        const handleMouseUp = () => {
            setIsResizing(false);
        };

        if (isResizing) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
        }

        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isResizing]);

    const fetchCourse = async () => {
        try {
            const data = await getCourse(courseId!);
            setCourse(data);
            setIsLoading(false);
        } catch (error) {
            console.error('Failed to fetch course:', error);
            setIsLoading(false);
        }
    };

    const loadVideo = async (video: VideoInCourse) => {
        setVideoId(video.video_id);

        if (video.report_id) {
            try {
                const reportData = await getReport(video.report_id);
                setReport(reportData);

                await getTranscript(video.video_id);
            } catch (error) {
                console.error('Failed to load video data:', error);
            }
        }
    };

    const handleVideoClick = (index: number) => {
        setCurrentVideoIndex(index);
        setCurrentTime(0);
        setSeekTo(null);
    };

    const handleTimestampClick = (timestamp: number) => {
        setSeekTo(timestamp);
        setTimeout(() => setSeekTo(null), 100);
    };

    const formatDuration = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#37353E' }}>
                <Loader className="animate-spin" size={48} style={{ color: '#D3DAD9' }} />
            </div>
        );
    }

    if (!course) {
        return (
            <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#37353E', color: '#D3DAD9' }}>
                <div className="text-center">
                    <h1 className="text-2xl font-bold mb-2">Course Not Found</h1>
                    <button onClick={() => navigate('/')} className="hover:opacity-80" style={{ color: '#715A5A' }}>
                        ← Back to Dashboard
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="h-screen flex flex-col" style={{ backgroundColor: '#37353E', color: '#D3DAD9' }}>
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b backdrop-blur-md" style={{ borderColor: '#44444E', backgroundColor: '#37353E' }}>
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => navigate('/')}
                        className="p-2 -ml-2 rounded-lg transition-all hover:opacity-80"
                        style={{ color: '#D3DAD9', backgroundColor: '#44444E' }}
                        title="Back to Dashboard"
                    >
                        <ChevronLeft size={20} />
                    </button>
                    <button
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                        className="p-2 rounded-lg transition-all hover:opacity-80"
                        style={{ color: '#D3DAD9', backgroundColor: '#44444E' }}
                        title={isSidebarOpen ? "Close Playlist" : "Open Playlist"}
                    >
                        {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
                    </button>
                    <div>
                        <h1 className="text-xl font-bold" style={{ color: '#D3DAD9' }}>{course.title}</h1>
                        <div className="flex items-center gap-3 mt-1">
                            <p className="text-sm opacity-70">
                                Video {currentVideoIndex + 1} of {course.video_count}
                            </p>
                            <div className="h-1 w-32 rounded-full overflow-hidden" style={{ backgroundColor: '#44444E' }}>
                                <div
                                    className="h-full transition-all duration-300"
                                    style={{
                                        backgroundColor: '#715A5A',
                                        width: `${((currentVideoIndex + 1) / course.video_count) * 100}%`
                                    }}
                                />
                            </div>
                        </div>
                    </div>
                </div>
                {course.channel_name && (
                    <p className="text-sm opacity-60">by {course.channel_name}</p>
                )}
            </div>

            {/* Main Content */}
            <div className="flex-1 flex overflow-hidden">
                {/* Sidebar - Collapsible */}
                <div
                    className={`border-r overflow-y-auto no-scrollbar transition-all duration-300 ${isSidebarOpen ? 'w-80' : 'w-0'
                        }`}
                    style={{ borderColor: '#44444E', backgroundColor: '#44444E' }}
                >
                    <div className={`${isSidebarOpen ? 'opacity-100' : 'opacity-0'} transition-opacity duration-300`}>
                        <div className="p-3 border-b" style={{ borderColor: '#37353E' }}>
                            <h2 className="text-xs font-semibold uppercase tracking-wider px-2 opacity-70">
                                Course Content
                            </h2>
                        </div>
                        <div className="p-2 space-y-1">
                            {course.videos.map((video, index) => {
                                const isActive = index === currentVideoIndex;
                                const isCompleted = video.status === 'succeeded';

                                return (
                                    <button
                                        key={video.video_id}
                                        onClick={() => handleVideoClick(index)}
                                        className="w-full text-left p-3 rounded-xl transition-all border"
                                        style={{
                                            backgroundColor: isActive ? '#715A5A' : 'transparent',
                                            borderColor: isActive ? '#715A5A' : 'transparent'
                                        }}
                                        onMouseEnter={(e) => {
                                            if (!isActive) e.currentTarget.style.backgroundColor = '#37353E';
                                        }}
                                        onMouseLeave={(e) => {
                                            if (!isActive) e.currentTarget.style.backgroundColor = 'transparent';
                                        }}
                                    >
                                        <div className="flex items-start gap-3">
                                            <div className="flex-shrink-0 mt-0.5">
                                                {isCompleted ? (
                                                    <div className="w-5 h-5 rounded-full flex items-center justify-center" style={{ backgroundColor: '#715A5A' }}>
                                                        <Check size={12} style={{ color: '#D3DAD9' }} />
                                                    </div>
                                                ) : isActive ? (
                                                    <div className="w-5 h-5 rounded-full flex items-center justify-center" style={{ backgroundColor: '#D3DAD9' }}>
                                                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: '#37353E' }} />
                                                    </div>
                                                ) : (
                                                    <div className="w-5 h-5 rounded-full border-2" style={{ borderColor: '#715A5A' }} />
                                                )}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-start justify-between gap-2 mb-1">
                                                    <span className="text-xs font-mono" style={{ color: isActive ? '#D3DAD9' : '#715A5A' }}>
                                                        {String(index + 1).padStart(2, '0')}
                                                    </span>
                                                    <span className="text-xs opacity-60">
                                                        {formatDuration(video.duration)}
                                                    </span>
                                                </div>
                                                <h3 className="text-sm font-medium line-clamp-2 leading-snug">
                                                    {video.title}
                                                </h3>
                                            </div>
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                </div>

                {/* Video and Chat Area */}
                <div className="flex-1 flex overflow-hidden">
                    {/* Video Player */}
                    <div className="flex-1 bg-black flex flex-col justify-center relative border-r p-6 min-w-0" style={{ borderColor: '#44444E' }}>
                        <div className="w-full h-full border rounded-xl overflow-hidden shadow-2xl" style={{ borderColor: '#44444E' }}>
                            <VideoPlayer
                                videoId={videoId}
                                onProgress={(state) => setCurrentTime(state.playedSeconds)}
                                onReady={() => console.log('Video ready')}
                                seekTo={seekTo}
                            />
                        </div>
                    </div>

                    {/* Resizer Handle */}
                    <div
                        className="w-1 hover:w-1.5 -ml-0.5 bg-transparent cursor-col-resize transition-all z-40 flex items-center justify-center group"
                        style={{ backgroundColor: isResizing ? '#715A5A' : 'transparent' }}
                        onMouseDown={() => setIsResizing(true)}
                    >
                        <div className="h-12 w-0.5 rounded-full transition-colors" style={{ backgroundColor: isResizing ? '#715A5A' : '#44444E' }} />
                    </div>

                    {/* Right Panel: Tabs */}
                    <div
                        className="flex flex-col z-20 shrink-0"
                        style={{ width: sidebarWidth, backgroundColor: '#37353E' }}
                    >
                        {/* Tab Headers */}
                        <div className="flex border-b shrink-0 px-4 pt-2 gap-2" style={{ borderColor: '#44444E' }}>
                            <button
                                onClick={() => setActiveTab('chat')}
                                className={`flex-1 pb-3 text-xs font-bold uppercase tracking-wider transition-all border-b-2 ${activeTab === 'chat' ? '' : 'hover:opacity-70'
                                    }`}
                                style={{
                                    borderColor: activeTab === 'chat' ? '#715A5A' : 'transparent',
                                    color: activeTab === 'chat' ? '#D3DAD9' : '#715A5A'
                                }}
                            >
                                Chat
                            </button>
                            <button
                                onClick={() => setActiveTab('notes')}
                                className={`flex-1 pb-3 text-xs font-bold uppercase tracking-wider transition-all border-b-2 ${activeTab === 'notes' ? '' : 'hover:opacity-70'
                                    }`}
                                style={{
                                    borderColor: activeTab === 'notes' ? '#715A5A' : 'transparent',
                                    color: activeTab === 'notes' ? '#D3DAD9' : '#715A5A'
                                }}
                            >
                                Upload Notes
                            </button>
                        </div>

                        {/* Tab Content */}
                        <div className="flex-1 overflow-y-auto relative no-scrollbar" style={{ backgroundColor: '#44444E' }}>
                            {activeTab === 'chat' && (
                                <div className="h-full flex flex-col">
                                    <ChatInterface
                                        videoId={videoId}
                                        currentTime={currentTime}
                                        onTimestampClick={handleTimestampClick}
                                    />
                                </div>
                            )}
                            {activeTab === 'notes' && (
                                <NotesView
                                    videoId={videoId}
                                    summary={report?.summary || 'Summary not available yet.'}
                                    notes={report?.notes || 'Detailed notes not available yet.'}
                                    onDownloadPdf={() => console.log('Download PDF')}
                                />
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CoursePage;
