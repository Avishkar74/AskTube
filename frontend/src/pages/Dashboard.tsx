import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Play, FileText, Clock, BookOpen, Loader } from 'lucide-react';
import { getReports, processVideo, getCourses, importCourse } from '../services/api';

interface Report {
    _id: string;
    youtube_url: string;
    video_id?: string;
    title?: string;
    status: 'queued' | 'running' | 'succeeded' | 'failed';
    created_at: string;
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
    const [activeTab, setActiveTab] = useState<'videos' | 'courses'>('videos');
    const [reports, setReports] = useState<Report[]>([]);
    const [courses, setCourses] = useState<Course[]>([]);
    const [url, setUrl] = useState('');
    const [playlistUrl, setPlaylistUrl] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);
    const [isImporting, setIsImporting] = useState(false);
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
            if (result._id || result.id) {
                navigate(`/video/${result._id || result.id}`);
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

    return (
        <div className="min-h-screen bg-zinc-950 p-8">
            <div className="max-w-6xl mx-auto">
                <header className="mb-12 text-center">
                    <h1 className="text-4xl font-extrabold text-white tracking-tight">
                        AskTube
                    </h1>
                    <p className="text-zinc-400 mt-3 text-lg">
                        Transform YouTube videos into interactive learning experiences.
                    </p>
                </header>

                {/* Tabs */}
                <div className="flex gap-4 mb-8 border-b border-zinc-800">
                    <button
                        onClick={() => setActiveTab('videos')}
                        className={`px-6 py-3 font-medium transition-all ${activeTab === 'videos'
                                ? 'text-white border-b-2 border-white'
                                : 'text-zinc-500 hover:text-zinc-300'
                            }`}
                    >
                        Recent Videos
                    </button>
                    <button
                        onClick={() => setActiveTab('courses')}
                        className={`px-6 py-3 font-medium transition-all ${activeTab === 'courses'
                                ? 'text-white border-b-2 border-white'
                                : 'text-zinc-500 hover:text-zinc-300'
                            }`}
                    >
                        My Courses
                    </button>
                </div>

                {/* Video Tab */}
                {activeTab === 'videos' && (
                    <>
                        <div className="max-w-2xl mx-auto mb-16">
                            <div className="bg-zinc-900 rounded-2xl shadow-xl p-2 flex items-center gap-2 border border-zinc-800">
                                <div className="pl-4 text-zinc-400">
                                    <Plus size={20} />
                                </div>
                                <input
                                    type="text"
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                    placeholder="Paste a YouTube URL to start learning..."
                                    className="flex-1 p-3 bg-transparent text-white placeholder-zinc-500 outline-none text-lg"
                                />
                                <button
                                    onClick={handleProcess}
                                    disabled={isProcessing || !url}
                                    className="px-6 py-3 bg-white hover:bg-zinc-200 text-black rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
                                >
                                    {isProcessing ? (
                                        <>
                                            <Loader className="animate-spin" size={18} />
                                            Processing
                                        </>
                                    ) : (
                                        <>
                                            Start Learning
                                            <Play size={18} fill="currentColor" />
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            {reports.map((report) => (
                                <Link
                                    to={`/video/${report._id}`}
                                    key={report._id}
                                    className="group"
                                >
                                    <div className="bg-zinc-900 rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden border border-zinc-800 group-hover:-translate-y-1 h-full flex flex-col">
                                        <div className="relative aspect-video bg-zinc-800 overflow-hidden">
                                            {report.video_id ? (
                                                <img
                                                    src={`https://img.youtube.com/vi/${report.video_id}/mqdefault.jpg`}
                                                    alt="Thumbnail"
                                                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                                                />
                                            ) : (
                                                <div className="flex items-center justify-center h-full text-zinc-600">
                                                    <Play size={48} />
                                                </div>
                                            )}
                                            <div className={`absolute top-3 right-3 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${report.status === 'succeeded' ? 'bg-green-500/90 text-white' :
                                                    report.status === 'failed' ? 'bg-red-500/90 text-white' :
                                                        'bg-yellow-500/90 text-black'
                                                }`}>
                                                {report.status}
                                            </div>
                                        </div>
                                        <div className="p-5 flex-1 flex flex-col">
                                            <h3 className="text-lg font-bold text-white mb-3 line-clamp-2">
                                                {report.title || report.youtube_url}
                                            </h3>
                                            <div className="mt-auto flex items-center justify-between text-sm text-zinc-400 border-t border-zinc-800 pt-4">
                                                <span className="flex items-center gap-1.5">
                                                    <Clock size={14} />
                                                    {new Date(report.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                                                </span>
                                                {report.status === 'succeeded' && (
                                                    <span className="flex items-center gap-1.5 text-green-400 font-medium">
                                                        <FileText size={14} />
                                                        Ready
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    </>
                )}

                {/* Courses Tab */}
                {activeTab === 'courses' && (
                    <>
                        <div className="max-w-2xl mx-auto mb-16">
                            <div className="bg-zinc-900 rounded-2xl shadow-xl p-2 flex items-center gap-2 border border-zinc-800">
                                <div className="pl-4 text-zinc-400">
                                    <BookOpen size={20} />
                                </div>
                                <input
                                    type="text"
                                    value={playlistUrl}
                                    onChange={(e) => setPlaylistUrl(e.target.value)}
                                    placeholder="Paste a YouTube Playlist URL to import a course..."
                                    className="flex-1 p-3 bg-transparent text-white placeholder-zinc-500 outline-none text-lg"
                                />
                                <button
                                    onClick={handleImportCourse}
                                    disabled={isImporting || !playlistUrl}
                                    className="px-6 py-3 bg-white hover:bg-zinc-200 text-black rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
                                >
                                    {isImporting ? (
                                        <>
                                            <Loader className="animate-spin" size={18} />
                                            Importing
                                        </>
                                    ) : (
                                        <>
                                            Import Course
                                            <Plus size={18} />
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            {courses.map((course) => (
                                <Link
                                    to={`/course/${course._id}`}
                                    key={course._id}
                                    className="group"
                                >
                                    <div className="bg-zinc-900 rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden border border-zinc-800 group-hover:-translate-y-1 h-full flex flex-col">
                                        <div className="relative aspect-video bg-zinc-800 overflow-hidden">
                                            {course.thumbnail ? (
                                                <img
                                                    src={course.thumbnail}
                                                    alt={course.title}
                                                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                                                />
                                            ) : (
                                                <div className="flex items-center justify-center h-full text-zinc-600">
                                                    <BookOpen size={48} />
                                                </div>
                                            )}
                                            <div className="absolute top-3 right-3 px-2.5 py-1 rounded-full text-xs font-bold bg-white/90 text-black">
                                                {course.video_count} videos
                                            </div>
                                        </div>
                                        <div className="p-5 flex-1 flex flex-col">
                                            <h3 className="text-lg font-bold text-white mb-2 line-clamp-2">
                                                {course.title}
                                            </h3>
                                            {course.channel_name && (
                                                <p className="text-sm text-zinc-400 mb-3">
                                                    by {course.channel_name}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
