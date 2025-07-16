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
    <div className="flex justify-center items-center min-h-[60vh] w-full">
      <div className="max-w-xl w-full bg-white/10 rounded-lg shadow-lg flex flex-col h-[60vh] justify-center my-auto">
        <div
          ref={chatWindowRef}
          className="flex-1 overflow-y-auto p-4 space-y-2 scrollbar-hide"
          style={{ maxHeight: '40vh', minHeight: '20vh' }}
        >
          {messages.length === 0 && (
            <div className="text-center text-gray-400">No messages yet. Start the conversation!</div>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`px-4 py-1 rounded-lg max-w-[80%] whitespace-pre-line text-sm shadow
                  ${msg.role === 'user' ? 'bg-reroute-primary text-white' : 'bg-transparent text-white'}`}
                style={msg.role === 'assistant' ? { background: 'none', boxShadow: 'none', color: '#fff' } : {}}
              >
                {msg.role === 'assistant' ? (
                  <ReactMarkdown className="prose prose-invert prose-chat max-w-none">{msg.content}</ReactMarkdown>
                ) : (
                  msg.content
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        <form onSubmit={(e) => {
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
              setMessages((prev) => [...prev, { role: 'assistant', content: 'Error sending message.' }]);
            } finally {
              setSending(false);
            }
          })();
        }} className="p-4 border-t border-reroute-card flex gap-2 bg-reroute-card">
          <input
            type="text"
            className="flex-1 rounded px-3 py-2 bg-white/80 text-gray-900 focus:outline-none"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={sending}
          />
          <button
            type="submit"
            className="bg-reroute-primary text-white px-4 py-2 rounded disabled:opacity-50"
            disabled={sending || !input.trim()}
          >
            {sending ? 'Sending...' : 'Send'}
          </button>
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