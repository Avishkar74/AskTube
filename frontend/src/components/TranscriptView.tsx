import React, { useEffect, useRef } from 'react';

interface Segment {
    text: string;
    start: number;
    duration: number;
}

interface TranscriptViewProps {
    segments: Segment[];
    currentTime: number;
    onSegmentClick: (start: number) => void;
}

const TranscriptView: React.FC<TranscriptViewProps> = ({ segments = [], currentTime, onSegmentClick }) => {
    const activeRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (activeRef.current) {
            activeRef.current.scrollIntoView({
                behavior: 'smooth',
                block: 'center',
            });
        }
    }, [currentTime]);

    return (
        <div className="h-full overflow-y-auto p-4 space-y-1 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-600">
            {segments.map((segment, index) => {
                const isActive = currentTime >= segment.start && currentTime < (segment.start + segment.duration);
                return (
                    <div
                        key={index}
                        ref={isActive ? activeRef : null}
                        onClick={() => onSegmentClick(segment.start)}
                        className={`p-3 rounded-xl cursor-pointer transition-all duration-300 border ${isActive
                            ? 'bg-indigo-50 dark:bg-indigo-900/20 border-indigo-200 dark:border-indigo-500/30 shadow-sm transform scale-[1.02]'
                            : 'bg-transparent border-transparent hover:bg-slate-100 dark:hover:bg-slate-800 hover:border-slate-200 dark:hover:border-slate-700'
                            }`}
                    >
                        <div className="flex gap-3">
                            <span className={`text-xs font-mono mt-1 flex-shrink-0 ${isActive ? 'text-indigo-600 dark:text-indigo-400 font-semibold' : 'text-slate-400 dark:text-slate-500'}`}>
                                {new Date(segment.start * 1000).toISOString().substr(14, 5)}
                            </span>
                            <p className={`text-sm leading-relaxed ${isActive ? 'text-slate-900 dark:text-white font-medium' : 'text-slate-600 dark:text-slate-400'}`}>
                                {segment.text}
                            </p>
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

export default TranscriptView;
