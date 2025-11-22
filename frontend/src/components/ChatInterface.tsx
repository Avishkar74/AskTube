import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, MessageSquare, Play } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { Citation } from '../types';

interface ChatInterfaceProps {
    messages: Message[];
    onSendMessage: (message: string) => Promise<void>;
    isLoading: boolean;
    onTimestampClick: (timestamp: number) => void;
}

export interface Message {
    role: 'user' | 'ai';
    content: string;
    citations?: Citation[];
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
    messages,
    onSendMessage,
    isLoading,
    onTimestampClick
}) => {
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async () => {
        if (!input.trim()) return;
        const msg = input;
        setInput('');
        await onSendMessage(msg);
    };

    const formatTime = (seconds: number) => {
        const date = new Date(seconds * 1000);
        return date.toISOString().substr(14, 5);
    };

    return (
        <div className="flex flex-col h-full bg-slate-50 dark:bg-slate-900/50">
            <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-600">
                {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-slate-400 space-y-4 opacity-60">
                        <div className="w-16 h-16 bg-indigo-100 dark:bg-indigo-900/30 rounded-2xl flex items-center justify-center">
                            <MessageSquare size={32} className="text-indigo-500" />
                        </div>
                        <p className="text-sm font-medium">Ask a question about the video!</p>
                    </div>
                ) : (
                    messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                        >
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user'
                                ? 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/50 dark:text-indigo-400'
                                : 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/50 dark:text-emerald-400'
                                }`}>
                                {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                            </div>

                            <div className={`flex flex-col max-w-[85%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                <div className={`p-3.5 rounded-2xl text-sm leading-relaxed shadow-sm ${msg.role === 'user'
                                    ? 'bg-indigo-600 text-white rounded-tr-none'
                                    : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700 rounded-tl-none'
                                    }`}>
                                    <div className="prose dark:prose-invert max-w-none text-sm">
                                        <ReactMarkdown>
                                            {msg.content}
                                        </ReactMarkdown>
                                    </div>
                                </div>

                                {msg.citations && msg.citations.length > 0 && (
                                    <div className="mt-2 flex flex-wrap gap-2">
                                        {msg.citations.map((cit, cIdx) => (
                                            <button
                                                key={cIdx}
                                                onClick={() => onTimestampClick(cit.start_sec)}
                                                className="flex items-center gap-1 text-xs bg-white dark:bg-slate-800 border border-indigo-200 dark:border-indigo-900/50 text-indigo-600 dark:text-indigo-400 px-2 py-1 rounded-full hover:bg-indigo-50 dark:hover:bg-indigo-900/30 transition-colors shadow-sm"
                                            >
                                                <Play size={10} fill="currentColor" />
                                                {formatTime(cit.start_sec)}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="p-4 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700">
                <form
                    onSubmit={(e) => {
                        e.preventDefault();
                        handleSubmit();
                    }}
                    className="relative flex items-center"
                >
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask something..."
                        disabled={isLoading}
                        className="w-full pl-4 pr-12 py-3 bg-slate-100 dark:bg-slate-900 border-0 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500/50 transition-all outline-none"
                    />
                    <button
                        type="submit"
                        disabled={isLoading || !input.trim()}
                        className="absolute right-2 p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:bg-transparent disabled:text-slate-400 transition-all"
                    >
                        {isLoading ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <Send size={18} />
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ChatInterface;
