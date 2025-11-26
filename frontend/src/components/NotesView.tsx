import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Download, RefreshCw, Image as ImageIcon, AlertCircle } from 'lucide-react';
import { getNotes } from '../services/api';
import Button from './ui/Button';
import Card from './ui/Card';

interface NotesViewProps {
    videoId: string;
    summary: string;
    notes: string;
    reportStatus?: string;
    onDownloadAiNotesPdf: () => void;
    onDownloadUploadedNotesPdf: () => void;
}

const NotesView: React.FC<NotesViewProps> = ({
    videoId,
    summary,
    notes,
    reportStatus = 'unknown',
    onDownloadAiNotesPdf,
    onDownloadUploadedNotesPdf
}) => {
    const [viewMode, setViewMode] = useState<'ai' | 'handwritten'>('ai');
    const [uploadedNotes, setUploadedNotes] = useState<{ filename: string; url: string }[]>([]);
    const [isLoadingUploads, setIsLoadingUploads] = useState(false);

    const hasContent = summary && notes && summary.trim().length > 0 && notes.trim().length > 0;
    const isProcessing = reportStatus === 'queued' || reportStatus === 'running';
    const hasFailed = reportStatus === 'failed';

    const fetchUploadedNotes = async () => {
        setIsLoadingUploads(true);
        try {
            const data = await getNotes(videoId);
            setUploadedNotes(data);
        } catch (error) {
            console.error('Failed to fetch uploaded notes:', error);
        } finally {
            setIsLoadingUploads(false);
        }
    };

    useEffect(() => {
        if (viewMode === 'handwritten') {
            fetchUploadedNotes();
        }
    }, [viewMode, videoId]);

    return (
        <div className="h-full flex flex-col bg-bg">
            {/* Toolbar */}
            <div className="p-4 border-b border-white/5 flex flex-col sm:flex-row gap-4 justify-between items-center bg-surface/50 backdrop-blur-sm sticky top-0 z-10">
                <div className="flex bg-black/20 p-1 rounded-xl border border-white/5">
                    <button
                        onClick={() => setViewMode('ai')}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${viewMode === 'ai'
                            ? 'bg-primary text-black shadow-glow'
                            : 'text-zinc-400 hover:text-white'
                            }`}
                    >
                        AI Notes
                    </button>
                    <button
                        onClick={() => setViewMode('handwritten')}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${viewMode === 'handwritten'
                            ? 'bg-primary text-black shadow-glow'
                            : 'text-zinc-400 hover:text-white'
                            }`}
                    >
                        Handwritten
                    </button>
                </div>

                <div className="flex gap-2">
                    {viewMode === 'ai' && (
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={onDownloadAiNotesPdf}
                            disabled={!hasContent || isProcessing}
                            icon={<Download size={16} />}
                        >
                            PDF
                        </Button>
                    )}
                    {viewMode === 'handwritten' && (
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={onDownloadUploadedNotesPdf}
                            disabled={uploadedNotes.length === 0}
                            icon={<Download size={16} />}
                        >
                            PDF
                        </Button>
                    )}
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
                {viewMode === 'ai' ? (
                    <div className="space-y-8 max-w-3xl mx-auto">
                        {isProcessing && (
                            <Card className="flex items-center gap-4 border-primary/20 bg-primary/5">
                                <RefreshCw className="animate-spin text-primary" />
                                <div>
                                    <h3 className="font-bold text-primary">Generating Study Materials...</h3>
                                    <p className="text-sm text-zinc-400">Analyzing transcript and creating detailed notes.</p>
                                </div>
                            </Card>
                        )}

                        {hasFailed && (
                            <Card className="flex items-center gap-4 border-error/20 bg-error/5">
                                <AlertCircle className="text-error" />
                                <div>
                                    <h3 className="font-bold text-error">Generation Failed</h3>
                                    <p className="text-sm text-zinc-400">Please try refreshing the page.</p>
                                </div>
                            </Card>
                        )}

                        {hasContent && (
                            <>
                                <section>
                                    <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                                        <span className="w-1 h-6 bg-secondary rounded-full"></span>
                                        Summary
                                    </h3>
                                    <div className="prose prose-invert max-w-none prose-p:text-zinc-300 prose-headings:text-white bg-surface p-6 rounded-2xl border border-white/5 shadow-sm">
                                        <p className="leading-relaxed">{summary}</p>
                                    </div>
                                </section>

                                <section>
                                    <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                                        <span className="w-1 h-6 bg-primary rounded-full"></span>
                                        Detailed Notes
                                    </h3>
                                    <div className="prose prose-invert max-w-none prose-p:text-zinc-300 prose-headings:text-white prose-strong:text-white prose-ul:text-zinc-300">
                                        <ReactMarkdown>{notes}</ReactMarkdown>
                                    </div>
                                </section>
                            </>
                        )}
                    </div>
                ) : (
                    <div className="space-y-6">
                        {isLoadingUploads ? (
                            <div className="flex justify-center py-12">
                                <RefreshCw className="animate-spin text-zinc-500" />
                            </div>
                        ) : uploadedNotes.length === 0 ? (
                            <div className="text-center py-12">
                                <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <ImageIcon className="text-zinc-600" size={32} />
                                </div>
                                <h3 className="text-lg font-medium text-white">No handwritten notes</h3>
                                <p className="text-zinc-500">Upload notes using the "Uploads" tab.</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {uploadedNotes.map((note, idx) => (
                                    <div key={idx} className="group relative rounded-xl overflow-hidden border border-white/10 bg-black/20 shadow-lg">
                                        <img
                                            src={`http://localhost:8000${note.url}`}
                                            alt={note.filename}
                                            className="w-full h-auto object-contain"
                                        />
                                        <div className="absolute top-2 right-2 bg-black/60 backdrop-blur-sm px-2 py-1 rounded text-xs font-medium text-white">
                                            Page {idx + 1}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default NotesView;
