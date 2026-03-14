import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Send, Bot, User, Loader, Sparkles, ChevronRight } from 'lucide-react';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';

const WELCOME_MSG = {
    id: 0,
    role: 'assistant',
    text: "Hi! I'm OralVision AI 🤖 — your oral cancer clinical assistant.\n\nI have comprehensive knowledge about oral cancer signs, risk factors, treatment, government schemes, referral pathways, and clinical protocols for ASHA workers.\n\nI'm now powered by Gemini 1.5 Flash with multi-turn memory — ask me anything!",
};

function MessageBubble({ msg }) {
    const isUser = msg.role === 'user';
    const methodColors = {
        gemini_rag: 'bg-violet-500/10 border-violet-500/20 text-violet-400',
        semantic:   'bg-teal-500/10 border-teal-500/20 text-teal-400',
        keyword:    'bg-slate-500/10 border-slate-500/20 text-slate-400',
        keyword_fallback: 'bg-slate-500/10 border-slate-500/20 text-slate-400',
    };
    const methodLabel = { gemini_rag: '🔮 Gemini RAG', semantic: '🧠 Semantic Search', keyword: '🔑 Keyword', keyword_fallback: '🔑 Keyword' };
    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex gap-2.5 ${isUser ? 'flex-row-reverse' : ''}`}
        >
            <div className={`w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-xs
                ${isUser ? 'bg-blue-600' : 'bg-gradient-to-br from-teal-500 to-blue-600'}`}>
                {isUser ? <User className="w-3.5 h-3.5 text-white" /> : <Bot className="w-3.5 h-3.5 text-white" />}
            </div>
            <div className={`max-w-[80%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
                <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap
                    ${isUser
                        ? 'bg-blue-600 text-white rounded-tr-sm'
                        : 'bg-white/8 border border-white/10 text-slate-200 rounded-tl-sm'
                    }`}
                >
                    {msg.text}
                </div>
                {msg.method && !isUser && (
                    <span className={`text-[10px] px-2 py-0.5 rounded-full border ${methodColors[msg.method] || methodColors.semantic}`}>
                        {methodLabel[msg.method] || msg.method}
                    </span>
                )}
                {msg.relatedTopics?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                        {msg.relatedTopics.map((t, i) => (
                            <span key={i} className="text-xs bg-teal-500/10 border border-teal-500/20 text-teal-400 rounded-full px-2 py-0.5">
                                {t}
                            </span>
                        ))}
                    </div>
                )}
            </div>
        </motion.div>
    );
}

export default function ChatWidget() {
    const [open, setOpen] = useState(false);
    const [messages, setMessages] = useState([WELCOME_MSG]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [suggestions, setSuggestions] = useState([]);
    // Full conversation history for multi-turn Gemini context
    const [history, setHistory] = useState([]);
    const { isAuthenticated } = useAuth();
    const bottomRef = useRef();
    const inputRef = useRef();

    useEffect(() => {
        if (isAuthenticated) {
            client.get('/chat/suggestions')
                .then(r => setSuggestions(r.data.suggestions || []))
                .catch(() => { });
        }
    }, [isAuthenticated]);

    useEffect(() => {
        if (open) {
            setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
            inputRef.current?.focus();
        }
    }, [open, messages]);

    const sendMessage = async (text) => {
        const msg = text || input.trim();
        if (!msg || loading) return;
        setInput('');
        const userMsg = { id: Date.now(), role: 'user', text: msg };
        setMessages(prev => [...prev, userMsg]);
        setLoading(true);
        try {
            const { data } = await client.post('/chat', {
                message: msg,
                history: history.slice(-10), // send last 5 exchanges for context
            });
            const assistantMsg = {
                id: Date.now() + 1,
                role: 'assistant',
                text: data.answer,
                relatedTopics: data.related_topics || [],
                method: data.method,
            };
            setMessages(prev => [...prev, assistantMsg]);
            // Update history for next turn
            setHistory(prev => [
                ...prev,
                { role: 'user', content: msg },
                { role: 'assistant', content: data.answer },
            ]);
        } catch {
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                role: 'assistant',
                text: 'Sorry, I could not process your question. Please make sure you are logged in and the backend is running.',
            }]);
        } finally {
            setLoading(false);
        }
    };

    if (!isAuthenticated) return null;

    return (
        <>
            {/* Floating Button */}
            <motion.button
                onClick={() => setOpen(o => !o)}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-gradient-to-br from-teal-500 to-blue-600 shadow-2xl flex items-center justify-center"
                style={{ boxShadow: '0 0 20px rgba(20,184,166,0.4)' }}
            >
                <AnimatePresence mode="wait">
                    {open
                        ? <motion.span key="x" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }}><X className="w-6 h-6 text-white" /></motion.span>
                        : <motion.span key="chat" initial={{ rotate: 90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }}><MessageCircle className="w-6 h-6 text-white" /></motion.span>
                    }
                </AnimatePresence>
                {!open && (
                    <span className="absolute -top-1 -right-1 w-4 h-4 bg-teal-400 rounded-full animate-pulse" />
                )}
            </motion.button>

            {/* Chat Panel */}
            <AnimatePresence>
                {open && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                        className="fixed bottom-24 right-6 z-50 w-96 max-w-[calc(100vw-1.5rem)] rounded-2xl overflow-hidden shadow-2xl"
                        style={{
                            background: 'linear-gradient(135deg, rgba(15,23,42,0.98) 0%, rgba(2,6,23,0.98) 100%)',
                            border: '1px solid rgba(255,255,255,0.08)',
                            backdropFilter: 'blur(20px)',
                        }}
                    >
                        {/* Header */}
                        <div className="p-4 bg-gradient-to-r from-teal-600/20 to-blue-600/20 border-b border-white/8 flex items-center gap-3">
                            <div className="w-9 h-9 bg-gradient-to-br from-teal-500 to-blue-600 rounded-xl flex items-center justify-center">
                                <Sparkles className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <p className="font-semibold text-sm text-white">OralVision AI</p>
                                <p className="text-xs text-teal-400">36-Topic KB · Gemini RAG · Multi-turn</p>
                            </div>
                            <div className="ml-auto flex items-center gap-1">
                                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                                <span className="text-xs text-slate-500">Live</span>
                            </div>
                        </div>

                        {/* Messages */}
                        <div className="h-80 overflow-y-auto p-4 space-y-4 scrollbar-thin">
                            {messages.map(m => <MessageBubble key={m.id} msg={m} />)}
                            {loading && (
                                <div className="flex gap-2.5">
                                    <div className="w-7 h-7 rounded-full bg-gradient-to-br from-teal-500 to-blue-600 flex items-center justify-center">
                                        <Bot className="w-3.5 h-3.5 text-white" />
                                    </div>
                                    <div className="bg-white/8 border border-white/10 rounded-2xl rounded-tl-sm px-4 py-3">
                                        <div className="flex gap-1 items-center h-4">
                                            {[0, 0.2, 0.4].map((d, i) => (
                                                <motion.div key={i} animate={{ y: [-2, 2, -2] }} transition={{ repeat: Infinity, duration: 0.8, delay: d }}
                                                    className="w-1.5 h-1.5 bg-teal-400 rounded-full" />
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={bottomRef} />
                        </div>

                        {/* Suggestions */}
                        {messages.length <= 1 && suggestions.length > 0 && (
                            <div className="px-4 pb-2">
                                <p className="text-xs text-slate-600 mb-2">Suggested questions:</p>
                                <div className="flex flex-col gap-1">
                                    {suggestions.slice(0, 4).map((s, i) => (
                                        <button key={i} onClick={() => sendMessage(s)}
                                            className="text-left text-xs text-slate-400 hover:text-teal-400 transition-colors flex items-center gap-1.5 py-1">
                                            <ChevronRight className="w-3 h-3 flex-shrink-0" />
                                            {s}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Input */}
                        <div className="p-3 border-t border-white/8">
                            <div className="flex gap-2">
                                <input
                                    ref={inputRef}
                                    value={input}
                                    onChange={e => setInput(e.target.value)}
                                    onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                                    placeholder="Ask about oral cancer..."
                                    className="flex-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-teal-500/50 transition-colors"
                                    disabled={loading}
                                />
                                <motion.button
                                    whileTap={{ scale: 0.9 }}
                                    onClick={() => sendMessage()}
                                    disabled={!input.trim() || loading}
                                    className="w-10 h-10 bg-gradient-to-br from-teal-500 to-blue-600 rounded-xl flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed transition-opacity flex-shrink-0"
                                >
                                    {loading ? <Loader className="w-4 h-4 text-white animate-spin" /> : <Send className="w-4 h-4 text-white" />}
                                </motion.button>
                            </div>
                            <p className="text-center text-slate-700 text-xs mt-2">Powered by local RAG · Not medical advice</p>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}
