import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { FileText, Download, Smartphone, RefreshCw } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { getLocalIp, getNotes } from '../services/api';

interface NotesViewProps {
    videoId: string;
    summary: string;
    notes: string; // Markdown content
    onDownloadPdf: () => void;
}

const NotesView: React.FC<NotesViewProps> = ({ videoId, summary, notes, onDownloadPdf }) => {
    const [localIp, setLocalIp] = useState<string>('');
    const [uploadedNotes, setUploadedNotes] = useState<{ filename: string; url: string }[]>([]);
    const [isRefreshing, setIsRefreshing] = useState(false);

    useEffect(() => {
        const fetchIp = async () => {
            try {
                const ip = await getLocalIp();
                setLocalIp(ip);
            } catch (error) {
                console.error('Failed to get local IP:', error);
            }
        };
        fetchIp();
    }, []);

    const fetchNotes = async () => {
        setIsRefreshing(true);
        try {
            const notes = await getNotes(videoId);
            setUploadedNotes(notes);
        } catch (error) {
            console.error('Failed to fetch notes:', error);
        } finally {
            setIsRefreshing(false);
        }
    };

    useEffect(() => {
        fetchNotes();
        const interval = setInterval(fetchNotes, 5000); // Poll every 5 seconds
        return () => clearInterval(interval);
    }, [videoId]);

    const uploadUrl = localIp ? `http://${localIp}:5173/mobile-upload/${videoId}` : '';

    return (
        <div className="h-full overflow-y-auto p-6 bg-zinc-950 text-zinc-100 space-y-8">
            {/* Header */}
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    <FileText className="text-zinc-400" />
                    Study Notes
                </h2>
                <button
                    onClick={onDownloadPdf}
                    className="flex items-center gap-2 px-4 py-2 bg-white text-black rounded-lg hover:bg-zinc-200 transition-colors shadow-sm font-medium"
                >
                    <Download size={18} />
                    Download PDF
                </button>
            </div>

            {/* QR Code Section */}
            <div className="bg-zinc-900 rounded-xl p-6 border border-zinc-800 flex flex-col md:flex-row items-center gap-6">
                <div className="bg-white p-2 rounded-lg">
                    {uploadUrl && (
                        <QRCodeSVG value={uploadUrl} size={120} level="M" />
                    )}
                </div>
                <div className="flex-1 text-center md:text-left">
                    <h3 className="text-lg font-semibold text-white mb-1 flex items-center justify-center md:justify-start gap-2">
                        <Smartphone size={20} className="text-zinc-400" />
                        Upload Handwritten Notes
                    </h3>
                    <p className="text-zinc-400 text-sm mb-3">
                        Scan this QR code with your phone to take photos of your notes and upload them directly to this video.
                    </p>
                    <p className="text-xs text-zinc-500">
                        Make sure your phone is connected to the same Wi-Fi network.
                    </p>
                </div>
            </div>

            {/* Uploaded Notes Gallery */}
            {uploadedNotes.length > 0 && (
                <div>
                    <div className="flex items-center justify-between mb-3">
                        <h3 className="text-xl font-semibold text-zinc-200 border-b pb-2 border-zinc-800 flex-1">
                            Uploaded Notes
                        </h3>
                        <button
                            onClick={fetchNotes}
                            className={`p-2 text-zinc-400 hover:text-white transition-colors ${isRefreshing ? 'animate-spin' : ''}`}
                            title="Refresh notes"
                        >
                            <RefreshCw size={16} />
                        </button>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {uploadedNotes.map((note, idx) => (
                            <a
                                key={idx}
                                href={`http://localhost:8000${note.url}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="block group relative aspect-[3/4] rounded-lg overflow-hidden border border-zinc-800 bg-zinc-900"
                            >
                                <img
                                    src={`http://localhost:8000${note.url}`}
                                    alt={note.filename}
                                    className="w-full h-full object-cover transition-transform group-hover:scale-105"
                                />
                                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors" />
                            </a>
                        ))}
                    </div>
                </div>
            )}

            {/* AI Summary */}
            <div>
                <h3 className="text-xl font-semibold text-zinc-200 mb-3 border-b pb-2 border-zinc-800">
                    Summary
                </h3>
                <div className="prose prose-invert max-w-none text-zinc-300 bg-zinc-900 p-4 rounded-lg border border-zinc-800">
                    <p>{summary}</p>
                </div>
            </div>

            {/* Detailed Notes */}
            <div>
                <h3 className="text-xl font-semibold text-zinc-200 mb-3 border-b pb-2 border-zinc-800">
                    Detailed Notes
                </h3>
                <div className="prose prose-invert max-w-none text-zinc-300">
                    <ReactMarkdown>{notes}</ReactMarkdown>
                </div>
            </div>
        </div>
    );
};

export default NotesView;
