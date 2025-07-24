import React, { useEffect, useRef, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { getToken } from '../services/auth';
import ReactMarkdown from 'react-markdown';

const API_URL = import.meta.env.VITE_API_URL || '';

interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

const Chat: React.FC = () => {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatWindowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!loading && !user) {
      navigate('/auth');
    }
  }, [user, loading, navigate]);

  useEffect(() => {
    const token = getToken();
    if (user && token) {
      fetch(`${API_URL}/chat/history`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((res) => res.json())
        .then((data) => setMessages(data.history || []));
    }
  }, [user]);

  // Only scroll the chat window, not the whole page
  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex justify-center items-center w-full py-4">
      <div
        className="max-w-2xl lg:max-w-3xl w-full mx-4 bg-white/10 backdrop-blur-sm rounded-xl shadow-xl flex flex-col"
        style={{
          height: 'calc(100vh - 220px)',
          maxHeight: '650px',
          minHeight: '450px',
        }}
      >
        {/* Chat Header */}
        <div className="p-6 border-b border-white/20">
          <h2 className="text-2xl font-bold text-white mb-2">
            AI Training Assistant
          </h2>
          <p className="text-gray-300">
            Ask me about your training, routes, performance, or anything cycling
            related!
          </p>
        </div>

        {/* Messages Container */}
        <div
          ref={chatWindowRef}
          className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-hide"
        >
          {messages.length === 0 && (
            <div className="text-center text-gray-400 py-12">
              <div className="mb-4">💬</div>
              <div className="text-lg mb-2">
                No messages yet. Start the conversation!
              </div>
              <div className="text-sm">
                Try asking about your training plan, recent rides, or cycling
                advice.
              </div>
            </div>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}
            >
              <div
                className={`px-6 py-3 rounded-2xl max-w-[85%] shadow-lg ${
                  msg.role === 'user'
                    ? 'bg-reroute-primary text-white ml-12'
                    : 'bg-white/15 backdrop-blur-sm text-white mr-12'
                }`}
              >
                {msg.role === 'assistant' ? (
                  <div className="prose prose-invert prose-sm max-w-none">
                    <ReactMarkdown
                      components={{
                        p: ({ children }) => (
                          <p className="mb-3 last:mb-0 leading-relaxed">
                            {children}
                          </p>
                        ),
                        ul: ({ children }) => (
                          <ul className="mb-3 pl-4 space-y-1">{children}</ul>
                        ),
                        ol: ({ children }) => (
                          <ol className="mb-3 pl-4 space-y-1">{children}</ol>
                        ),
                        li: ({ children }) => (
                          <li className="text-gray-200">{children}</li>
                        ),
                        strong: ({ children }) => (
                          <strong className="text-white font-semibold">
                            {children}
                          </strong>
                        ),
                        em: ({ children }) => (
                          <em className="text-blue-200">{children}</em>
                        ),
                        code: ({ children }) => (
                          <code className="bg-black/30 px-1.5 py-0.5 rounded text-sm font-mono text-blue-200">
                            {children}
                          </code>
                        ),
                        pre: ({ children }) => (
                          <pre className="bg-black/30 p-3 rounded-lg overflow-x-auto mb-3">
                            {children}
                          </pre>
                        ),
                        h1: ({ children }) => (
                          <h1 className="text-xl font-bold mb-3 text-white">
                            {children}
                          </h1>
                        ),
                        h2: ({ children }) => (
                          <h2 className="text-lg font-bold mb-2 text-white">
                            {children}
                          </h2>
                        ),
                        h3: ({ children }) => (
                          <h3 className="text-base font-bold mb-2 text-white">
                            {children}
                          </h3>
                        ),
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <div className="leading-relaxed">{msg.content}</div>
                )}
              </div>
            </div>
          ))}
          {sending && (
            <div className="flex justify-start mb-4">
              <div className="bg-white/15 backdrop-blur-sm text-white px-6 py-3 rounded-2xl mr-12">
                <div className="flex items-center space-x-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: '0.1s' }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: '0.2s' }}
                    ></div>
                  </div>
                  <span className="text-sm text-gray-300">
                    AI is thinking...
                  </span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!input.trim()) return;
            setSending(true);
            const newMsg: ChatMessage = { role: 'user', content: input };
            setMessages((prev) => [...prev, newMsg]);
            setInput('');
            (async () => {
              try {
                const token = getToken();
                const res = await fetch(`${API_URL}/chat/message`, {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                  },
                  body: JSON.stringify({ messages: [newMsg] }),
                });
                const data = await res.json();
                if (data.message) {
                  setMessages((prev) => [...prev, data.message]);
                }
              } catch {
                setMessages((prev) => [
                  ...prev,
                  {
                    role: 'assistant',
                    content: 'Error sending message. Please try again.',
                  },
                ]);
              } finally {
                setSending(false);
              }
            })();
          }}
          className="p-6 border-t border-white/20 bg-white/5"
        >
          <div className="flex gap-3">
            <input
              type="text"
              className="flex-1 rounded-xl px-4 py-3 bg-white/90 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-reroute-primary focus:bg-white transition-all"
              placeholder="Ask about your training, performance, routes..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={sending}
            />
            <button
              type="submit"
              className="bg-reroute-primary hover:bg-reroute-primary/90 text-white px-6 py-3 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2 font-medium"
              disabled={sending || !input.trim()}
            >
              {sending ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  Sending
                </>
              ) : (
                <>
                  <span>Send</span>
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                    />
                  </svg>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Chat;

/* Tailwind custom class for hiding scrollbars */
// In your global CSS (e.g., App.css):
// .scrollbar-hide::-webkit-scrollbar { display: none; }
// .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
