import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, MessageSquare, Play, Mic, MicOff, Volume2, VolumeX, Settings } from 'lucide-react';
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

// Add types for Web Speech API
declare global {
    interface Window {
        SpeechRecognition: any;
        webkitSpeechRecognition: any;
    }
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
    messages,
    onSendMessage,
    isLoading,
    onTimestampClick
}) => {
    const [input, setInput] = useState('');
    const [isListening, setIsListening] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [autoSpeak, setAutoSpeak] = useState(true);
    const [lang, setLang] = useState<'en-US' | 'hi-IN'>('en-US');
    const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
    const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
    const [rate, setRate] = useState(1.0);
    const [showSettings, setShowSettings] = useState(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const recognitionRef = useRef<any>(null);
    const synth = window.speechSynthesis;

    // Streaming TTS Refs
    const lastSpokenLengthRef = useRef(0);
    const currentMessageRef = useRef('');

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Load voices
    useEffect(() => {
        const loadVoices = () => {
            const voices = synth.getVoices();
            setAvailableVoices(voices);
        };

        loadVoices();
        if (synth.onvoiceschanged !== undefined) {
            synth.onvoiceschanged = loadVoices;
        }
    }, []);

    // Update selected voice when lang changes or voices load
    useEffect(() => {
        if (availableVoices.length > 0) {
            const voicesForLang = availableVoices.filter(v => v.lang === lang);
            // Default to Google or first available
            const defaultVoice = voicesForLang.find(v => v.name.includes('Google')) || voicesForLang[0];
            setSelectedVoice(defaultVoice || null);
        }
    }, [lang, availableVoices]);

    // Initialize Speech Recognition
    useEffect(() => {
        if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.continuous = false;
            recognitionRef.current.interimResults = false;
            recognitionRef.current.lang = lang; // Dynamic language

            recognitionRef.current.onresult = (event: any) => {
                const transcript = event.results[0][0].transcript;
                setInput(transcript);
                handleSendMessage(transcript);
            };

            recognitionRef.current.onend = () => {
                setIsListening(false);
            };

            recognitionRef.current.onerror = (event: any) => {
                console.error('Speech recognition error', event.error);
                setIsListening(false);
            };
        }
    }, [lang]); // Re-init on lang change

    const speak = (text: string) => {
        // Do NOT cancel here, as we want to queue sentences during streaming.

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = lang;
        utterance.rate = rate;

        if (selectedVoice) {
            utterance.voice = selectedVoice;
        }

        utterance.onstart = () => setIsSpeaking(true);
        utterance.onend = () => {
            // Only set to false if queue is empty
            if (!synth.pending) {
                setIsSpeaking(false);
            }
        };

        synth.speak(utterance);
    };

    const stopSpeaking = () => {
        synth.cancel();
        setIsSpeaking(false);
    };

    // Streaming TTS Logic
    useEffect(() => {
        if (!autoSpeak) return;

        const lastMsg = messages[messages.length - 1];
        if (!lastMsg || lastMsg.role !== 'ai') {
            lastSpokenLengthRef.current = 0;
            currentMessageRef.current = '';
            return;
        }

        const fullText = lastMsg.content;
        const newText = fullText.slice(lastSpokenLengthRef.current);

        // If we have new text
        if (newText.length > 0) {
            // Look for sentence boundaries
            const sentenceMatch = newText.match(/([.?!।\n]+)\s/);

            if (sentenceMatch && sentenceMatch.index !== undefined) {
                const endIdx = sentenceMatch.index + sentenceMatch[0].length;
                const sentenceToSpeak = newText.slice(0, endIdx).trim();

                if (sentenceToSpeak) {
                    speak(sentenceToSpeak);
                    lastSpokenLengthRef.current += endIdx;
                }
            }
        }

        // If loading finished, speak the remainder
        if (!isLoading && lastSpokenLengthRef.current < fullText.length) {
            const remainder = fullText.slice(lastSpokenLengthRef.current).trim();
            if (remainder) {
                speak(remainder);
                lastSpokenLengthRef.current = fullText.length;
            }
        }

    }, [messages, isLoading, autoSpeak, lang, selectedVoice, rate]);

    const startListening = () => {
        stopSpeaking(); // Stop AI speech when user wants to talk
        if (recognitionRef.current) {
            try {
                recognitionRef.current.lang = lang; // Ensure correct lang
                recognitionRef.current.start();
                setIsListening(true);
            } catch (e) {
                console.error(e);
            }
        } else {
            alert("Speech recognition not supported in this browser.");
        }
    };

    const stopListening = () => {
        if (recognitionRef.current) {
            recognitionRef.current.stop();
            setIsListening(false);
        }
    };

    const handleSendMessage = async (text: string) => {
        if (!text.trim()) return;
        stopSpeaking(); // Stop any ongoing speech when user sends new message
        setInput('');
        await onSendMessage(text);
    };

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
            {/* Toolbar */}
            <div className="px-4 py-2 flex flex-col gap-2 border-b border-slate-200 dark:border-slate-700">
                <div className="flex justify-between items-center">
                    <div className="flex gap-2">
                        <button
                            onClick={() => setLang('en-US')}
                            className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${lang === 'en-US'
                                ? 'bg-indigo-600 text-white'
                                : 'bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-300 dark:hover:bg-slate-700'}`}
                        >
                            English
                        </button>
                        <button
                            onClick={() => setLang('hi-IN')}
                            className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${lang === 'hi-IN'
                                ? 'bg-indigo-600 text-white'
                                : 'bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-300 dark:hover:bg-slate-700'}`}
                        >
                            हिंदी (Hindi)
                        </button>
                    </div>

                    <div className="flex gap-2">
                        <button
                            onClick={() => setShowSettings(!showSettings)}
                            className={`p-2 rounded-full transition-colors ${showSettings ? 'bg-slate-200 dark:bg-slate-700 text-indigo-600' : 'text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'}`}
                            title="Voice Settings"
                        >
                            <Settings size={18} />
                        </button>
                        <button
                            onClick={() => {
                                if (isSpeaking) stopSpeaking();
                                setAutoSpeak(!autoSpeak);
                            }}
                            className={`p-2 rounded-full transition-colors ${autoSpeak ? 'text-indigo-600 bg-indigo-50 dark:bg-indigo-900/20' : 'text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'}`}
                            title={autoSpeak ? "Auto-speak ON" : "Auto-speak OFF"}
                        >
                            {autoSpeak ? <Volume2 size={18} /> : <VolumeX size={18} />}
                        </button>
                    </div>
                </div>

                {/* Settings Panel */}
                {showSettings && (
                    <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl text-xs space-y-3 animate-in slide-in-from-top-2">
                        <div className="space-y-1">
                            <label className="block text-slate-500 dark:text-slate-400 font-medium">Voice</label>
                            <select
                                value={selectedVoice?.name || ''}
                                onChange={(e) => {
                                    const voice = availableVoices.find(v => v.name === e.target.value);
                                    setSelectedVoice(voice || null);
                                }}
                                className="w-full p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 outline-none focus:ring-2 focus:ring-indigo-500/50"
                            >
                                {availableVoices.filter(v => v.lang === lang).map(v => (
                                    <option key={v.name} value={v.name}>
                                        {v.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div className="space-y-1">
                            <label className="block text-slate-500 dark:text-slate-400 font-medium">
                                Speed: {rate}x
                            </label>
                            <input
                                type="range"
                                min="0.5"
                                max="2"
                                step="0.1"
                                value={rate}
                                onChange={(e) => setRate(parseFloat(e.target.value))}
                                className="w-full accent-indigo-600"
                            />
                        </div>
                    </div>
                )}
            </div>

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

                                {/* Manual speak button for AI messages */}
                                {msg.role === 'ai' && (
                                    <button
                                        onClick={() => speak(msg.content)}
                                        className="mt-1 text-slate-400 hover:text-indigo-500 opacity-0 group-hover:opacity-100 transition-opacity"
                                        title="Read aloud"
                                    >
                                        <Volume2 size={14} />
                                    </button>
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
                    className="relative flex items-center gap-2"
                >
                    <div className="relative flex-1">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Ask something..."
                            disabled={isLoading || isListening}
                            className="w-full pl-4 pr-12 py-3 bg-slate-100 dark:bg-slate-900 border-0 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500/50 transition-all outline-none"
                        />
                        <button
                            type="button"
                            onClick={isListening ? stopListening : startListening}
                            className={`absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg transition-all ${isListening
                                ? 'bg-red-100 text-red-600 animate-pulse'
                                : 'text-slate-400 hover:text-indigo-600'
                                }`}
                            title="Voice input"
                        >
                            {isListening ? <MicOff size={18} /> : <Mic size={18} />}
                        </button>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading || !input.trim()}
                        className="p-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:bg-slate-200 disabled:text-slate-400 transition-all shadow-sm hover:shadow-md"
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
