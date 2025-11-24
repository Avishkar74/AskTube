import React, { useState, useRef, useEffect } from 'react';
import { User, Bot, MessageSquare, Plus, Mic, AudioLines, MicOff, Send } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { chatWithVideo } from '../services/api';
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
    const [voiceMode, setVoiceMode] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const recognitionRef = useRef<any>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Initialize Speech Recognition
    useEffect(() => {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.continuous = false;
            recognitionRef.current.interimResults = false;

            recognitionRef.current.onresult = (event: any) => {
                const transcript = event.results[0][0].transcript;
                setInput((prev) => prev + (prev ? ' ' : '') + transcript);
                setIsListening(false);
            };

            recognitionRef.current.onerror = (event: any) => {
                console.error('Speech recognition error', event.error);
                setIsListening(false);
            };

            recognitionRef.current.onend = () => {
                setIsListening(false);
            };
        }
    }, []);

    // Handle Voice Mode (TTS)
    useEffect(() => {
        if (voiceMode && messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            if (lastMessage.role === 'ai' && !isLoading) {
                speakText(lastMessage.content);
            }
        }
    }, [messages, voiceMode, isLoading]);

    const speakText = (text: string) => {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        window.speechSynthesis.speak(utterance);
    };

    const toggleListening = () => {
        if (isListening) {
            recognitionRef.current?.stop();
        } else {
            recognitionRef.current?.start();
            setIsListening(true);
        }
    };

    const toggleVoiceMode = () => {
        setVoiceMode(!voiceMode);
        if (voiceMode) {
            window.speechSynthesis.cancel();
        }
    };

    const handleNewChat = () => {
        setMessages([]);
        setInput('');
        window.speechSynthesis.cancel();
    };

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
            timestamp: currentTime
        };
        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);
        window.speechSynthesis.cancel();

        try {
            console.log('[ChatInterface] Sending message:', input);
            const response: ChatResponse = await chatWithVideo({
                video_id: videoId,
                message: input,
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
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                            placeholder="Ask about the video..."
                            className="flex-1 bg-transparent outline-none text-sm"
                            style={{ color: '#D3DAD9' }}
                            disabled={isLoading}
                        />
                        <button
                            onClick={toggleVoiceMode}
                            className={`p-1.5 rounded transition-all ${voiceMode ? 'opacity-100' : 'opacity-50 hover:opacity-100'}`}
                            style={{ color: voiceMode ? '#715A5A' : '#D3DAD9' }}
                            title="Voice Mode"
                        >
                            <AudioLines size={18} />
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
                        onClick={handleSend}
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
