import React, { useState, useEffect } from 'react';
import { Smartphone, RefreshCw, Download, Image as ImageIcon } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { getLocalIp, getNotes } from '../services/api';
import Button from './ui/Button';
import Card from './ui/Card';

interface UploadNotesViewProps {
    videoId: string;
    onDownloadPdf: () => void;
}

const UploadNotesView: React.FC<UploadNotesViewProps> = ({ videoId, onDownloadPdf }) => {
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
        const interval = setInterval(fetchNotes, 5000);
        return () => clearInterval(interval);
    }, [videoId]);

    const uploadUrl = localIp ? `http://${localIp}:5173/mobile-upload/${videoId}` : '';

    return (
        <div className="h-full overflow-y-auto p-6 space-y-8">
            {/* QR Code Section */}
            <Card className="flex flex-col md:flex-row items-center gap-8 bg-gradient-to-br from-surface to-surface/50">
                <div className="bg-white p-3 rounded-xl shadow-lg">
                    {uploadUrl && (
                        <QRCodeSVG value={uploadUrl} size={140} level="M" />
                    )}
                </div>
                <div className="flex-1 text-center md:text-left space-y-3">
                    <h3 className="text-xl font-bold text-white flex items-center justify-center md:justify-start gap-2">
                        <Smartphone className="text-primary" />
                        Scan to Upload
                    </h3>
                    <p className="text-zinc-400">
                        Scan this QR code with your phone to upload handwritten notes directly to this video.
                    </p>
                    <div className="flex items-center justify-center md:justify-start gap-2 text-xs text-zinc-500 bg-black/20 py-2 px-3 rounded-lg inline-flex">
                        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                        Connect to same Wi-Fi
                    </div>
                </div>
            </Card>

            {/* Uploaded Notes Gallery */}
            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <ImageIcon size={20} className="text-secondary" />
                        Uploaded Pages ({uploadedNotes.length})
                    </h3>
                    <div className="flex gap-2">
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={fetchNotes}
                            icon={<RefreshCw size={16} className={isRefreshing ? 'animate-spin' : ''} />}
                        />
                        {uploadedNotes.length > 0 && (
                            <Button
                                variant="secondary"
                                size="sm"
                                onClick={onDownloadPdf}
                                icon={<Download size={16} />}
                            >
                                Export PDF
                            </Button>
                        )}
                    </div>
                </div>

                {uploadedNotes.length === 0 ? (
                    <div className="border-2 border-dashed border-white/10 rounded-2xl p-12 text-center">
                        <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4">
                            <ImageIcon size={32} className="text-zinc-600" />
                        </div>
                        <p className="text-zinc-400 font-medium">No notes uploaded yet</p>
                        <p className="text-zinc-600 text-sm mt-1">Use the QR code above to add your first page</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {uploadedNotes.map((note, idx) => (
                            <div key={idx} className="group relative aspect-[3/4] rounded-xl overflow-hidden border border-white/10 bg-black/20">
                                <img
                                    src={`http://localhost:8000${note.url}`}
                                    alt={note.filename}
                                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                                />
                                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
                                    <a
                                        href={`http://localhost:8000${note.url}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="p-2 bg-white/10 backdrop-blur-md rounded-lg text-white hover:bg-white/20 transition-colors"
                                    >
                                        <Download size={20} />
                                    </a>
                                </div>
                                <div className="absolute top-2 right-2 bg-black/60 backdrop-blur-sm px-2 py-1 rounded text-xs font-medium text-white">
                                    #{idx + 1}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default UploadNotesView;
