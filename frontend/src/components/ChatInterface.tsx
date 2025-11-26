import React, { useState, useRef, useEffect } from 'react';
import { Plus, Mic, AudioLines, MicOff, Send, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { chatWithVideo, getChatHistory } from '../services/api';
import type { ChatResponse, Citation } from '../types';
import Button from './ui/Button';

interface ChatInterfaceProps {
    videoId: string;
    currentTime: number;
    onTimestampClick: (timestamp: number) => void;
}

interface Message {
    id?: string;
    role: 'user' | 'ai';
    content: string;
    citations?: Citation[];
    timestamp?: number;
}

const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

const ChatInterface: React.FC<ChatInterfaceProps> = ({ videoId, currentTime, onTimestampClick }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isListening, setIsListening] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [interimTranscript, setInterimTranscript] = useState('');
    const [voiceMode, setVoiceMode] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const recognitionRef = useRef<any>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        if (!videoId) return;
        const fetchHistory = async () => {
            try {
                const history = await getChatHistory(videoId);
                setMessages(history && history.length > 0 ? history : []);
            } catch (error) {
                console.error("Failed to load chat history:", error);
            }
        };
        fetchHistory();
    }, [videoId]);

    const handleSend = async (textOverride?: string) => {
        const text = typeof textOverride === 'string' ? textOverride : input;
        if (!text.trim()) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: text,
            timestamp: currentTime
        };
        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);
        window.speechSynthesis.cancel();
        setIsSpeaking(false);

        try {
            const response: ChatResponse = await chatWithVideo({
                video_id: videoId,
                message: text,
                use_rag: true,
            });

            const aiMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'ai',
                content: response.answer,
                citations: response.citations,
            };
            setMessages((prev) => [...prev, aiMessage]);
        } catch (error) {
            console.error('[ChatInterface] Chat error:', error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'ai',
                content: 'Sorry, I encountered an error processing your request.'
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.continuous = false;
            recognitionRef.current.interimResults = true;
        }
    }, []);

    useEffect(() => {
        if (!recognitionRef.current) return;

        recognitionRef.current.onresult = (event: any) => {
            let interim = '';
            let final = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    final += event.results[i][0].transcript;
                } else {
                    interim += event.results[i][0].transcript;
                }
            }

            if (final) {
                if (voiceMode) {
                    const fullText = (input + (input ? ' ' : '') + final).trim();
                    handleSend(fullText);
                } else {
                    setInput((prev) => prev + (prev ? ' ' : '') + final);
                    setInterimTranscript('');
                    setIsListening(false);
                }
            } else {
                setInterimTranscript(interim);
            }
        };

        recognitionRef.current.onerror = (event: any) => {
            console.error('Speech recognition error', event.error);
            setIsListening(false);
            setInterimTranscript('');
            if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
                setVoiceMode(false);
            }
        };

        recognitionRef.current.onend = () => {
            setIsListening(false);
            setInterimTranscript('');
        };

    }, [voiceMode, input, handleSend]);

    const lastSpokenMessageId = useRef<string | null>(null);

    const startListeningSafe = () => {
        try {
            recognitionRef.current?.start();
            setIsListening(true);
        } catch (error: any) {
            if (error.name === 'InvalidStateError') {
                setIsListening(true);
            }
        }
    };

    const stopListeningSafe = () => {
        try {
            recognitionRef.current?.stop();
            setIsListening(false);
        } catch (error) {
            setIsListening(false);
        }
    };

    useEffect(() => {
        if (messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            if (lastMessage.role === 'ai' && !isLoading) {
                if (voiceMode) {
                    if (lastMessage.id !== lastSpokenMessageId.current) {
                        speakText(lastMessage.content);
                    } else if (!isListening && !isSpeaking) {
                        startListeningSafe();
                    }
                }
                lastSpokenMessageId.current = lastMessage.id || null;
            }
        }
    }, [messages, voiceMode, isLoading, isListening, isSpeaking]);

    const speakText = (text: string) => {
        window.speechSynthesis.cancel();
        setIsSpeaking(true);
        const utterance = new SpeechSynthesisUtterance(text);

        utterance.onend = () => {
            setIsSpeaking(false);
            if (voiceMode) {
                setTimeout(() => {
                    if (!isListening) {
                        startListeningSafe();
                    }
                }, 100);
            }
        };

        utterance.onerror = () => {
            setIsSpeaking(false);
        };

        window.speechSynthesis.speak(utterance);
    };

    const toggleListening = () => {
        if (isListening) {
            stopListeningSafe();
            setVoiceMode(false);
        } else {
            startListeningSafe();
        }
    };

    const toggleVoiceMode = () => {
        const newMode = !voiceMode;
        setVoiceMode(newMode);

        if (newMode) {
            if (!isListening) {
                startListeningSafe();
            }
        } else {
            window.speechSynthesis.cancel();
            setIsSpeaking(false);
            if (isListening) {
                stopListeningSafe();
            }
        }
    };

    const handleNewChat = () => {
        setMessages([]);
        setInput('');
        window.speechSynthesis.cancel();
    };

    return (
        <div className="flex flex-col h-full bg-bg">
            <div className="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar">
                {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full space-y-4 opacity-50 text-zinc-500">
                        <div className="w-16 h-16 bg-surface rounded-2xl flex items-center justify-center border border-white/5">
                            <Sparkles size={32} className="text-primary" />
                        </div>
                        <p className="text-sm font-medium">Ask anything about the video</p>
                    </div>
                ) : (
                    messages.map((message) => (
                        <div
                            key={message.id}
                            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[85%] p-4 shadow-sm ${message.role === 'user'
                                    ? 'bg-primary text-black rounded-2xl rounded-br-none'
                                    : 'bg-surface border border-white/10 text-zinc-100 rounded-2xl rounded-bl-none'
                                    }`}
                            >
                                <div className="flex items-start gap-3">
                                    {message.role === 'ai' && (
                                        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center mt-1">
                                            <Sparkles size={14} className="text-primary" />
                                        </div>
                                    )}
                                    <div className="flex-1 min-w-0">
                                        <div className="prose prose-invert max-w-none prose-p:leading-snug prose-sm">
                                            <ReactMarkdown>{message.content}</ReactMarkdown>
                                        </div>
                                        {message.citations && message.citations.length > 0 && (
                                            <div className="mt-3 flex flex-wrap gap-2 pt-2 border-t border-white/5">
                                                {message.citations.map((citation, index) => (
                                                    <button
                                                        key={index}
                                                        onClick={() => onTimestampClick(citation.start_sec)}
                                                        className="text-xs px-2 py-1 rounded-md bg-black/20 hover:bg-black/40 transition-colors flex items-center gap-1 text-primary/80"
                                                        title={citation.text}
                                                    >
                                                        <span>▶ {formatTime(citation.start_sec)}</span>
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))
                )}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-surface border border-white/10 p-4 rounded-2xl rounded-bl-none flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0ms' }} />
                            <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '150ms' }} />
                            <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t border-white/5 p-4 bg-surface/50 backdrop-blur-sm">
                <div className="flex gap-2">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleNewChat}
                        className="!px-3"
                        title="New Chat"
                    >
                        <Plus size={20} />
                    </Button>

                    <div className="flex-1 flex gap-2 p-1.5 bg-black/20 border border-white/10 rounded-xl focus-within:border-primary/50 transition-colors">
                        <input
                            type="text"
                            value={isListening ? input + (input && interimTranscript ? ' ' : '') + interimTranscript : input}
                            onChange={(e) => {
                                setInput(e.target.value);
                                setVoiceMode(false);
                            }}
                            onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                            placeholder={isListening ? "Listening..." : "Ask a question..."}
                            className="flex-1 bg-transparent outline-none text-sm px-2 text-white placeholder-zinc-500"
                            disabled={isLoading}
                        />
                        <button
                            onClick={toggleVoiceMode}
                            className={`p-2 rounded-lg transition-all ${voiceMode ? 'text-primary bg-primary/10' : 'text-zinc-400 hover:text-white'}`}
                            title="Voice Mode"
                        >
                            {isSpeaking ? <AudioLines size={18} className="animate-pulse" /> : <AudioLines size={18} />}
                        </button>
                        <button
                            onClick={toggleListening}
                            className={`p-2 rounded-lg transition-all ${isListening ? 'text-error bg-error/10' : 'text-zinc-400 hover:text-white'}`}
                            title={isListening ? "Stop Listening" : "Start Listening"}
                        >
                            {isListening ? <MicOff size={18} /> : <Mic size={18} />}
                        </button>
                    </div>

                    <Button
                        onClick={() => handleSend()}
                        disabled={!input.trim() || isLoading}
                        className="!px-3"
                        variant="primary"
                    >
                        <Send size={20} />
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default ChatInterface;
