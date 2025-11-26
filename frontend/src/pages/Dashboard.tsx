import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Play, FileText, Clock, BookOpen, Loader, Search, ExternalLink } from 'lucide-react';
import { getReports, processVideo, getCourses, importCourse } from '../services/api';
import Header from '../components/Header';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';

interface Report {
    _id: string;
    youtube_url: string;
    video_id?: string;
    title?: string;
    status: 'queued' | 'running' | 'succeeded' | 'failed';
    created_at: string;
    report_id?: string;
}

interface Course {
    _id: string;
    title: string;
    description?: string;
    thumbnail?: string;
    channel_name?: string;
    video_count: number;
}

const Dashboard: React.FC = () => {
    const [reports, setReports] = useState<Report[]>([]);
    const [courses, setCourses] = useState<Course[]>([]);
    const [url, setUrl] = useState('');
    const [playlistUrl, setPlaylistUrl] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);
    const [isImporting, setIsImporting] = useState(false);
    const [showImportInput, setShowImportInput] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        fetchReports();
        fetchCourses();
    }, []);

    const fetchReports = async () => {
        try {
            const data = await getReports();
            setReports(data.items || []);
        } catch (error) {
            console.error('Failed to fetch reports:', error);
        }
    };

    const fetchCourses = async () => {
        try {
            const data = await getCourses();
            setCourses(data.items || []);
        } catch (error) {
            console.error('Failed to fetch courses:', error);
        }
    };

    const handleProcess = async () => {
        if (!url) return;
        setIsProcessing(true);
        try {
            const result = await processVideo(url);
            setUrl('');
            const reportId = result.report_id || result._id || result.id;
            if (reportId) {
                navigate(`/video/${reportId}`);
            } else {
                fetchReports();
            }
        } catch (error) {
            console.error('Failed to process video:', error);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleImportCourse = async () => {
        if (!playlistUrl) return;
        setIsImporting(true);
        try {
            const result = await importCourse(playlistUrl);
            setPlaylistUrl('');
            setShowImportInput(false);
            if (result.course_id) {
                navigate(`/course/${result.course_id}`);
            } else {
                fetchCourses();
            }
        } catch (error) {
            console.error('Failed to import course:', error);
        } finally {
            setIsImporting(false);
        }
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'succeeded': return <Badge variant="success">Completed</Badge>;
            case 'failed': return <Badge variant="error">Failed</Badge>;
            case 'running': return <Badge variant="running">Analyzing...</Badge>;
            case 'queued': return <Badge variant="warning">Queued</Badge>;
            default: return <Badge variant="default">{status}</Badge>;
        }
    };

    return (
        <div className="min-h-screen bg-bg text-text font-sans selection:bg-primary/30 pb-20">
            {isProcessing && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center">
                    <div className="relative">
                        <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full animate-pulse"></div>
                        <Loader className="w-16 h-16 text-primary animate-spin relative z-10" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mt-8">Analyzing Video Content...</h2>
                    <p className="text-zinc-400 mt-2">Generating transcript, summary, and study notes</p>
                </div>
            )}

            <div className="max-w-7xl mx-auto px-6">
                <Header />

                {/* Hero Section */}
                <div className="flex flex-col items-center justify-center py-12 mb-16">
                    <h1 className="text-4xl md:text-5xl font-bold text-center mb-8 bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-white/50 leading-tight">
                        What do you want to learn today?
                    </h1>
                    <div className="w-full max-w-2xl relative group z-10">
                        <div className="absolute -inset-1 bg-gradient-to-r from-primary to-secondary rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000"></div>
                        <div className="relative flex gap-2 bg-surface p-2 rounded-2xl border border-white/10 shadow-2xl">
                            <div className="flex-1 flex items-center px-4">
                                <Search className="text-zinc-500 mr-3" size={20} />
                                <input
                                    type="text"
                                    placeholder="Paste a YouTube URL..."
                                    className="flex-1 bg-transparent border-none focus:ring-0 text-lg text-white placeholder-zinc-500 outline-none"
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleProcess()}
                                />
                            </div>
                            <Button onClick={handleProcess} isLoading={isProcessing} disabled={!url}>
                                Start Learning
                            </Button>
                        </div>
                    </div>
                </div>

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">

                    {/* Sidebar: Courses */}
                    <div className="lg:col-span-1 space-y-6">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                <BookOpen size={20} className="text-primary" />
                                Your Courses
                            </h2>
                            <Button
                                variant="ghost"
                                size="sm"
                                icon={<Plus size={18} />}
                                onClick={() => setShowImportInput(!showImportInput)}
                                className="!p-2"
                            />
                        </div>

                        {showImportInput && (
                            <div className="bg-surface p-4 rounded-xl border border-white/10 animate-in slide-in-from-top-2">
                                <input
                                    type="text"
                                    placeholder="Playlist URL..."
                                    className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-sm text-white mb-3 focus:border-primary/50 outline-none"
                                    value={playlistUrl}
                                    onChange={(e) => setPlaylistUrl(e.target.value)}
                                />
                                <Button
                                    size="sm"
                                    className="w-full"
                                    onClick={handleImportCourse}
                                    isLoading={isImporting}
                                    disabled={!playlistUrl}
                                >
                                    Import
                                </Button>
                            </div>
                        )}

                        <div className="space-y-3">
                            {courses.map((course) => (
                                <Link key={course._id} to={`/course/${course._id}`}>
                                    <div className="group bg-surface/50 hover:bg-surface border border-white/5 hover:border-primary/30 rounded-xl p-3 transition-all cursor-pointer flex gap-3 items-center">
                                        <div className="w-12 h-12 rounded-lg bg-black/40 flex-shrink-0 overflow-hidden">
                                            {course.thumbnail ? (
                                                <img src={course.thumbnail} alt="" className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
                                            ) : (
                                                <div className="w-full h-full flex items-center justify-center text-zinc-600">
                                                    <BookOpen size={16} />
                                                </div>
                                            )}
                                        </div>
                                        <div className="min-w-0">
                                            <h3 className="font-medium text-sm text-zinc-200 truncate group-hover:text-primary transition-colors">
                                                {course.title}
                                            </h3>
                                            <p className="text-xs text-zinc-500 truncate">
                                                {course.video_count} videos • {course.channel_name || 'Unknown'}
                                            </p>
                                        </div>
                                    </div>
                                </Link>
                            ))}
                            {courses.length === 0 && !showImportInput && (
                                <div className="text-center py-8 text-zinc-500 bg-surface/30 rounded-xl border border-dashed border-white/5">
                                    <p className="text-sm">No courses yet</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Main: Recent Videos */}
                    <div className="lg:col-span-3 space-y-6">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                <Clock size={20} className="text-secondary" />
                                Recent Videos
                            </h2>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {reports.map((report) => (
                                <Card key={report._id} hover className="group relative overflow-hidden flex flex-col h-full !p-0" onClick={() => navigate(`/video/${report.report_id || report._id}`)}>
                                    {/* Thumbnail Area */}
                                    <div className="aspect-video bg-black/50 relative overflow-hidden">
                                        <img
                                            src={`https://img.youtube.com/vi/${report.video_id || report.youtube_url.split('v=')[1]}/hqdefault.jpg`}
                                            alt={report.title}
                                            className="w-full h-full object-cover opacity-80 group-hover:opacity-100 group-hover:scale-105 transition-all duration-500"
                                            onError={(e) => {
                                                (e.target as HTMLImageElement).src = 'https://via.placeholder.com/640x360?text=Video+Thumbnail';
                                            }}
                                        />
                                        <div className="absolute inset-0 bg-gradient-to-t from-surface via-transparent to-transparent opacity-60"></div>

                                        {/* Status Badge */}
                                        <div className="absolute top-3 right-3">
                                            {getStatusBadge(report.status)}
                                        </div>

                                        {/* Play Overlay */}
                                        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-black/30 backdrop-blur-[2px]">
                                            <div className="w-12 h-12 rounded-full bg-primary/90 text-black flex items-center justify-center transform scale-50 group-hover:scale-100 transition-transform duration-300 shadow-glow">
                                                <Play size={20} fill="currentColor" className="ml-1" />
                                            </div>
                                        </div>
                                    </div>

                                    {/* Content Area */}
                                    <div className="p-5 flex flex-col flex-1">
                                        <h3 className="font-bold text-lg text-white mb-2 line-clamp-2 leading-snug group-hover:text-primary transition-colors">
                                            {report.title || 'Untitled Video'}
                                        </h3>
                                        <div className="mt-auto pt-4 flex items-center justify-between text-xs text-zinc-500 border-t border-white/5">
                                            <span className="flex items-center gap-1">
                                                <Clock size={12} />
                                                {new Date(report.created_at).toLocaleDateString()}
                                            </span>
                                            <span className="flex items-center gap-1 hover:text-white transition-colors">
                                                Open <ExternalLink size={12} />
                                            </span>
                                        </div>
                                    </div>
                                </Card>
                            ))}

                            {reports.length === 0 && (
                                <div className="col-span-full py-20 text-center bg-surface/30 rounded-2xl border border-dashed border-white/10">
                                    <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <Play size={32} className="text-zinc-600" />
                                    </div>
                                    <h3 className="text-lg font-medium text-white mb-2">No videos yet</h3>
                                    <p className="text-zinc-500 max-w-sm mx-auto">
                                        Paste a YouTube URL above to start learning from your first video.
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
