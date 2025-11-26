import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Upload, Check, AlertCircle, Image as ImageIcon } from 'lucide-react';
import { uploadNote } from '../services/api';

const MobileUploadPage: React.FC = () => {
    const { videoId } = useParams<{ videoId: string }>();
    const [file, setFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setError(null);
            setIsSuccess(false);
        }
    };

    const handleUpload = async () => {
        if (!file || !videoId) return;

        setIsUploading(true);
        setError(null);

        try {
            await uploadNote(videoId, file);
            setIsSuccess(true);
            setFile(null);
        } catch (err) {
            console.error('Upload failed:', err);
            setError('Failed to upload image. Please try again.');
        } finally {
            setIsUploading(false);
        }
    };

    if (!videoId) {
        return (
            <div className="min-h-screen bg-zinc-950 text-white flex items-center justify-center p-4">
                <div className="text-center">
                    <AlertCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
                    <h1 className="text-xl font-bold mb-2">Invalid Link</h1>
                    <p className="text-zinc-400">Video ID is missing.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-zinc-950 text-white p-6 flex flex-col items-center justify-center">
            <div className="w-full max-w-md space-y-8">
                <div className="text-center">
                    <h1 className="text-3xl font-bold mb-2">Upload Notes</h1>
                    <p className="text-zinc-400">Take a photo of your handwritten notes to add them to the video.</p>
                </div>

                <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800 shadow-xl">
                    {isSuccess ? (
                        <div className="text-center py-8">
                            <div className="w-16 h-16 bg-green-500/20 text-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Check size={32} />
                            </div>
                            <h2 className="text-xl font-bold mb-2">Upload Successful!</h2>
                            <p className="text-zinc-400 mb-6">Your note has been added to the video.</p>
                            <button
                                onClick={() => setIsSuccess(false)}
                                className="w-full py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl font-medium transition-colors"
                            >
                                Upload Another
                            </button>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            <div className="relative">
                                <input
                                    type="file"
                                    accept="image/*"
                                    capture="environment"
                                    onChange={handleFileChange}
                                    className="hidden"
                                    id="file-upload"
                                />
                                <label
                                    htmlFor="file-upload"
                                    className={`flex flex-col items-center justify-center w-full h-48 border-2 border-dashed rounded-xl cursor-pointer transition-all ${file
                                            ? 'border-zinc-500 bg-zinc-800/50'
                                            : 'border-zinc-700 hover:border-zinc-500 hover:bg-zinc-800/50'
                                        }`}
                                >
                                    {file ? (
                                        <div className="text-center p-4">
                                            <ImageIcon className="mx-auto h-10 w-10 text-zinc-400 mb-2" />
                                            <p className="text-sm font-medium truncate max-w-[200px]">{file.name}</p>
                                            <p className="text-xs text-zinc-500 mt-1">Tap to change</p>
                                        </div>
                                    ) : (
                                        <div className="text-center p-4">
                                            <Upload className="mx-auto h-10 w-10 text-zinc-500 mb-2" />
                                            <p className="font-medium">Tap to take photo</p>
                                            <p className="text-xs text-zinc-500 mt-1">or select from gallery</p>
                                        </div>
                                    )}
                                </label>
                            </div>

                            {error && (
                                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2 text-red-400 text-sm">
                                    <AlertCircle size={16} />
                                    {error}
                                </div>
                            )}

                            <button
                                onClick={handleUpload}
                                disabled={!file || isUploading}
                                className="w-full py-3.5 bg-white text-black rounded-xl font-bold hover:bg-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-white/5"
                            >
                                {isUploading ? 'Uploading...' : 'Upload Note'}
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MobileUploadPage;
