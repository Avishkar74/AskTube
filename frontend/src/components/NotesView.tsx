import React from 'react';
import ReactMarkdown from 'react-markdown';
import { FileText, Download } from 'lucide-react';

interface NotesViewProps {
    summary: string;
    notes: string; // Markdown content
    onDownloadPdf: () => void;
}

const NotesView: React.FC<NotesViewProps> = ({ summary, notes, onDownloadPdf }) => {
    return (
        <div className="h-full overflow-y-auto p-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
                    <FileText className="text-blue-600" />
                    Study Notes
                </h2>
                <button
                    onClick={onDownloadPdf}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors shadow-sm"
                >
                    <Download size={18} />
                    Download PDF
                </button>
            </div>

            <div className="mb-8">
                <h3 className="text-xl font-semibold text-gray-700 dark:text-gray-200 mb-3 border-b pb-2 border-gray-200 dark:border-gray-700">
                    Summary
                </h3>
                <div className="prose dark:prose-invert max-w-none text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
                    <p>{summary}</p>
                </div>
            </div>

            <div>
                <h3 className="text-xl font-semibold text-gray-700 dark:text-gray-200 mb-3 border-b pb-2 border-gray-200 dark:border-gray-700">
                    Detailed Notes
                </h3>
                <div className="prose dark:prose-invert max-w-none text-gray-600 dark:text-gray-300">
                    <ReactMarkdown>{notes}</ReactMarkdown>
                </div>
            </div>
        </div>
    );
};

export default NotesView;
