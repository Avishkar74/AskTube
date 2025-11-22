import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Play, FileText, Clock } from 'lucide-react';
import { getReports, processVideo } from '../services/api';

interface Report {
    _id: string;
    youtube_url: string;
    video_id?: string;
    title?: string; // Assuming backend adds this
    status: 'queued' | 'running' | 'succeeded' | 'failed';
    created_at: string;
}

const Dashboard: React.FC = () => {
    const [reports, setReports] = useState<Report[]>([]);
    const [url, setUrl] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);

    useEffect(() => {
        fetchReports();
    }, []);

    const fetchReports = async () => {
        console.log('[Dashboard] Fetching reports...');
        try {
            const data = await getReports();
            console.log(`[Dashboard] Fetched ${data.items?.length || 0} reports`);
            setReports(data.items || []); // Adjust based on actual API response structure
        } catch (error) {
            console.error('[Dashboard] Failed to fetch reports:', error);
        }
    };

    const handleProcess = async () => {
        if (!url) return;
        console.log(`[Dashboard] Processing video URL: ${url}`);
        setIsProcessing(true);
        try {
            const result = await processVideo(url);
            console.log('[Dashboard] Process initiated successfully:', result);
            setUrl('');
            fetchReports(); // Refresh list
            // Optionally poll for status updates
        } catch (error) {
            console.error('[Dashboard] Failed to process video:', error);
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 p-8">
            <div className="max-w-6xl mx-auto">
                <header className="mb-12 text-center">
                    <h1 className="text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                        Ask<span className="text-indigo-600">Tube</span>
                    </h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-3 text-lg">
                        Transform YouTube videos into interactive learning experiences.
                    </p>
                </header>

                <div className="max-w-2xl mx-auto mb-16 relative">
                    <div className="absolute inset-0 bg-indigo-500/20 blur-3xl rounded-full -z-10" />
                    <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-2 flex items-center gap-2 border border-slate-200 dark:border-slate-700 transition-all focus-within:ring-4 focus-within:ring-indigo-500/20 focus-within:border-indigo-500">
                        <div className="pl-4 text-slate-400">
                            <Plus size={20} />
                        </div>
                        <input
                            type="text"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            placeholder="Paste a YouTube URL to start learning..."
                            className="flex-1 p-3 bg-transparent text-slate-900 dark:text-white placeholder-slate-400 outline-none text-lg"
                        />
                        <button
                            onClick={handleProcess}
                            disabled={isProcessing || !url}
                            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all transform active:scale-95 flex items-center gap-2"
                        >
                            {isProcessing ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
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
                            className="group relative"
                        >
                            <div className="absolute inset-0 bg-indigo-500/0 group-hover:bg-indigo-500/5 rounded-2xl transition-colors -z-10" />
                            <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden border border-slate-200 dark:border-slate-700 group-hover:-translate-y-1 h-full flex flex-col">
                                <div className="relative aspect-video bg-slate-200 dark:bg-slate-700 overflow-hidden">
                                    {report.video_id ? (
                                        <img
                                            src={`https://img.youtube.com/vi/${report.video_id}/mqdefault.jpg`}
                                            alt="Thumbnail"
                                            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                                        />
                                    ) : (
                                        <div className="flex items-center justify-center h-full text-slate-400">
                                            <Play size={48} />
                                        </div>
                                    )}
                                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-4">
                                        <span className="text-white font-medium flex items-center gap-2">
                                            <Play size={16} fill="currentColor" />
                                            Watch & Learn
                                        </span>
                                    </div>
                                    <div className={`absolute top-3 right-3 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider shadow-sm backdrop-blur-md ${report.status === 'succeeded' ? 'bg-emerald-500/90 text-white' :
                                            report.status === 'failed' ? 'bg-rose-500/90 text-white' :
                                                'bg-amber-500/90 text-white'
                                        }`}>
                                        {report.status}
                                    </div>
                                </div>
                                <div className="p-5 flex-1 flex flex-col">
                                    <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-3 line-clamp-2 group-hover:text-indigo-600 transition-colors">
                                        {report.title || report.youtube_url}
                                    </h3>
                                    <div className="mt-auto flex items-center justify-between text-sm text-slate-500 dark:text-slate-400 border-t border-slate-100 dark:border-slate-700 pt-4">
                                        <span className="flex items-center gap-1.5">
                                            <Clock size={14} />
                                            {new Date(report.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                                        </span>
                                        {report.status === 'succeeded' && (
                                            <span className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-medium">
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
            </div>
        </div>
    );
};

export default Dashboard;
