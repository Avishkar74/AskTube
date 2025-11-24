import React, { useState, useRef, useEffect } from 'react';
import { User, Bot, MessageSquare, Plus, Mic, AudioLines, MicOff, Send } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { chatWithVideo, getChatHistory } from '../services/api';
import type { ChatResponse, Citation } from '../types';

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

// eslint-disable-next-line @typescript-eslint/no-unused-vars
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

    // Fetch Chat History
    useEffect(() => {
        if (!videoId) return;

        const fetchHistory = async () => {
            try {
                const history = await getChatHistory(videoId);
                if (history && history.length > 0) {
                    setMessages(history);
                } else {
                    setMessages([]);
                }
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
        // Removed setVoiceMode(false) to allow TTS if mode was active

        try {
            console.log('[ChatInterface] Sending message:', text);
            const response: ChatResponse = await chatWithVideo({
                video_id: videoId,
                message: text,
                use_rag: true,
            });
            console.log('[ChatInterface] Received response:', response);

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

    // Initialize Speech Recognition Instance (Once)
    useEffect(() => {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.continuous = false;
            recognitionRef.current.interimResults = true;
        }
    }, []);

    // Update Speech Recognition Handlers (On Dependency Change)
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
                    // Auto-send in voice mode
                    // We append final to input just in case user typed something before speaking
                    const fullText = (input + (input ? ' ' : '') + final).trim();
                    handleSend(fullText);
                } else {
                    // Dictation mode: just update input
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
            // Only disable voice mode on critical errors, or maybe not at all?
            // setVoiceMode(false); 
            if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
                setVoiceMode(false);
            }
        };

        recognitionRef.current.onend = () => {
            setIsListening(false);
            setInterimTranscript('');
        };

    }, [voiceMode, input, handleSend]); // Dependencies ensure handlers have fresh state

    const lastSpokenMessageId = useRef<string | null>(null);

    const startListeningSafe = () => {
        try {
            recognitionRef.current?.start();
            setIsListening(true);
        } catch (error: any) {
            console.error("Error starting speech recognition:", error);
            // If it's already started, ensure state reflects that
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
            console.error("Error stopping speech recognition:", error);
            setIsListening(false);
        }
    };

    // Handle Voice Mode (TTS)
    useEffect(() => {
        if (messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            if (lastMessage.role === 'ai' && !isLoading) {
                if (voiceMode) {
                    if (lastMessage.id !== lastSpokenMessageId.current) {
                        speakText(lastMessage.content);
                    } else if (!isListening && !isSpeaking) {
                        // Auto-start listening if we enable voice mode but have nothing to say
                        startListeningSafe();
                    }
                }
                // Mark as seen so we don't speak it later just by toggling voice mode
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
                // Small delay to ensure state is clean
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
            // If we are in voice mode and manually stop listening, we should probably exit voice mode too
            // or just pause? User request implies separation. 
            // Let's keep it simple: Mic button just controls Mic. 
            // But if Voice Mode is ON, stopping Mic breaks the loop. 
            // Let's disable Voice Mode if manually stopped to be safe and avoid auto-restart loops.
            setVoiceMode(false);
        } else {
            startListeningSafe();
            // setVoiceMode(true); // REMOVED: Mic button does NOT enable Voice Mode anymore
        }
    };

    const toggleVoiceMode = () => {
        const newMode = !voiceMode;
        setVoiceMode(newMode);

        if (newMode) {
            // Enabling Voice Mode: Start listening immediately if not already
            if (!isListening) {
                startListeningSafe();
            }
        } else {
            // Disabling Voice Mode: Stop listening and cancel speech
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

    // handleSend is already defined above

    return (
        <div className="flex flex-col h-full" style={{ backgroundColor: '#44444E' }}>
            <div className="flex-1 overflow-y-auto p-4 space-y-6 no-scrollbar">
                {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full space-y-4 opacity-50" style={{ color: '#715A5A' }}>
                        <MessageSquare size={48} strokeWidth={1.5} />
                        <p className="text-sm font-medium">Start a conversation about this video</p>
                    </div>
                ) : (
                    messages.map((message) => (
                        <div
                            key={message.id}
                            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[85%] p-4 rounded-2xl shadow-sm ${message.role === 'user' ? 'rounded-br-sm' : 'border rounded-bl-sm'
                                    }`}
                                style={{
                                    backgroundColor: message.role === 'user' ? '#D3DAD9' : '#37353E',
                                    color: message.role === 'user' ? '#37353E' : '#D3DAD9',
                                    borderColor: message.role === 'user' ? 'transparent' : '#715A5A'
                                }}
                            >
                                <div className="flex items-start gap-3">
                                    <div
                                        className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center"
                                        style={{ backgroundColor: '#715A5A' }}
                                    >
                                        {message.role === 'user' ? (
                                            <User size={16} style={{ color: '#D3DAD9' }} />
                                        ) : (
                                            <Bot size={16} style={{ color: '#D3DAD9' }} />
                                        )}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <ReactMarkdown>
                                            {message.content}
                                        </ReactMarkdown>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))
                )}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="p-4 rounded-2xl rounded-bl-sm flex items-center gap-2 border" style={{ backgroundColor: '#37353E', borderColor: '#715A5A' }}>
                            <div className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ backgroundColor: '#715A5A', animationDelay: '0ms' }} />
                            <div className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ backgroundColor: '#715A5A', animationDelay: '150ms' }} />
                            <div className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ backgroundColor: '#715A5A', animationDelay: '300ms' }} />
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t p-4" style={{ borderColor: '#37353E', backgroundColor: '#37353E' }}>
                <div className="flex gap-2">
                    <button
                        onClick={handleNewChat}
                        className="p-2 rounded-lg transition-all hover:opacity-80"
                        style={{ backgroundColor: '#44444E', color: '#D3DAD9' }}
                        title="New Chat"
                    >
                        <Plus size={20} />
                    </button>
                    <div className="flex-1 flex gap-2 p-2 rounded-lg" style={{ backgroundColor: '#44444E' }}>
                        <input
                            type="text"
                            value={isListening ? input + (input && interimTranscript ? ' ' : '') + interimTranscript : input}
                            onChange={(e) => {
                                setInput(e.target.value);
                                setVoiceMode(false); // Typing disables voice mode
                            }}
                            onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                            placeholder={isListening ? "Listening..." : "Ask about the video..."}
                            className="flex-1 bg-transparent outline-none text-sm"
                            style={{ color: '#D3DAD9' }}
                            disabled={isLoading}
                        />
                        <button
                            onClick={toggleVoiceMode}
                            className={`p-1.5 rounded transition-all ${voiceMode ? 'opacity-100' : 'opacity-50 hover:opacity-100'}`}
                            style={{ color: voiceMode ? '#715A5A' : '#D3DAD9' }}
                            title="Voice Mode (Auto-enabled by Mic)"
                        >
                            {isSpeaking ? <AudioLines size={18} className="animate-pulse" /> : <AudioLines size={18} />}
                        </button>
                        <button
                            onClick={toggleListening}
                            className={`p-1.5 rounded transition-all ${isListening ? 'opacity-100' : 'opacity-50 hover:opacity-100'}`}
                            style={{ color: isListening ? '#715A5A' : '#D3DAD9' }}
                            title={isListening ? "Stop Listening" : "Start Listening"}
                            disabled={isLoading}
                        >
                            {isListening ? <MicOff size={18} /> : <Mic size={18} />}
                        </button>
                    </div>
                    <button
                        onClick={() => handleSend()}
                        disabled={!input.trim() || isLoading}
                        className="p-2 rounded-lg transition-all disabled:opacity-30 hover:opacity-80"
                        style={{ backgroundColor: '#715A5A', color: '#D3DAD9' }}
                        title="Send"
                    >
                        <Send size={20} />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ChatInterface;
