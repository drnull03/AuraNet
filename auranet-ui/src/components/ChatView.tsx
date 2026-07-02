/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useRef, useEffect } from 'react';
import { Send, Terminal, Loader2, RefreshCw, Sparkles, AlertCircle, Cpu } from 'lucide-react';
import { ChatMessage, SystemNode } from '../types';

interface ChatViewProps {
  systemNodes: SystemNode[];
}

export default function ChatView({ systemNodes }: ChatViewProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'init',
      sender: 'system',
      content: 'Alpha-AI coprocessor initialized. System telemetry synced successfully. Ask me about node health, optimization recommendations, or distributed consensus theories.',
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Suggested prompt chips to help the user interact easily
  const suggestionChips = [
    "Recommend how to optimize the network latency",
    "Identify if any nodes are currently malfunctioning",
    "Explain Paxos vs Raft consensus for Project Alpha",
    "Give me an active nodes health audit summary"
  ];

  // Scroll to bottom whenever messages list grows
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSendMessage = async (textToSend: string) => {
    if (!textToSend.trim() || loading) return;

    setError(null);
    const userMessage: ChatMessage = {
      id: `m-${Date.now()}`,
      sender: 'user',
      content: textToSend,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Gather active message logs to preserve context
      const chatHistory = [...messages, userMessage].filter(m => m.sender !== 'system');

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: chatHistory,
          networkNodes: systemNodes,
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error || "Failed to compile analytical consensus response.");
      }

      const data = await response.json();
      
      setMessages(prev => [...prev, {
        id: `m-${Date.now() + 1}`,
        sender: 'assistant',
        content: data.content,
        timestamp: new Date(),
      }]);

    } catch (err: any) {
      console.error(err);
      setError(err.message || "An issue occurred connecting with the network operator backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border border-brand-border rounded-2xl shadow-sm h-[680px] flex flex-col overflow-hidden" id="ai-operator-chat-panel">
      {/* Panel Header */}
      <div className="bg-slate-50 px-6 py-4 border-b border-brand-border flex items-center justify-between select-none">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 bg-brand-primary text-white rounded-xl flex items-center justify-center shadow-md animate-pulse">
            <Terminal size={18} />
          </div>
          <div>
            <h3 className="font-display font-bold text-sm text-brand-text">AI Operator Console</h3>
            <span className="font-mono text-[10px] text-brand-primary font-bold uppercase tracking-wider block">
              Coprocessor Status: Active
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1 bg-[#e0fbfc] text-[#006e70] px-2.5 py-1 rounded-full text-xs font-semibold">
          <Sparkles size={12} className="animate-spin-slow" />
          <span>Gemini 3.5 Flash Powered</span>
        </div>
      </div>

      {/* Messages body */}
      <div className="flex-1 p-6 overflow-y-auto space-y-4 bg-slate-50/20" id="chat-messages-container">
        {messages.map((m) => {
          if (m.sender === 'system') {
            return (
              <div key={m.id} className="mx-auto max-w-2xl bg-indigo-50/50 border border-indigo-100 rounded-xl p-3.5 text-center text-xs text-indigo-700 font-sans font-medium flex items-center gap-2">
                <Terminal size={14} className="flex-shrink-0 text-indigo-500 animate-pulse" />
                <span>{m.content}</span>
              </div>
            );
          }

          const isUser = m.sender === 'user';
          return (
            <div 
              key={m.id} 
              className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
              id={`chat-msg-row-${m.id}`}
            >
              <div className={`max-w-[80%] rounded-2xl p-4 shadow-xs text-sm ${
                isUser 
                  ? 'bg-brand-primary text-white rounded-br-xs' 
                  : 'bg-white border border-brand-border text-slate-800 rounded-bl-xs'
              }`}>
                {/* Message Author Header */}
                <div className={`flex items-center gap-1.5 mb-1 text-[10px] uppercase font-bold tracking-wider font-mono ${
                  isUser ? 'text-indigo-200' : 'text-brand-primary'
                }`}>
                  <span>{isUser ? 'Senior Architect' : 'Alpha-AI'}</span>
                  <span>•</span>
                  <span>{m.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                {/* Content body */}
                <div className="leading-relaxed font-sans prose max-w-none prose-sm">
                  <p className="whitespace-pre-line font-medium">{m.content}</p>
                </div>
              </div>
            </div>
          );
        })}

        {/* Loading Bubble */}
        {loading && (
          <div className="flex justify-start" id="chat-loading-bubble">
            <div className="bg-white border border-brand-border rounded-2xl rounded-bl-xs p-4 flex items-center gap-3 shadow-xs">
              <Loader2 className="h-5 w-5 text-brand-primary animate-spin" />
              <span className="font-mono text-xs font-bold text-slate-400 uppercase tracking-widest animate-pulse">
                Analyzing Live Telemetry...
              </span>
            </div>
          </div>
        )}

        {/* Error Notification */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-red-700 text-xs flex items-center gap-2" id="chat-error-alert">
            <AlertCircle size={16} className="text-red-500 flex-shrink-0 animate-bounce" />
            <div className="flex-1">
              <span className="font-bold block">Consensus Failure</span>
              <p>{error}</p>
            </div>
            <button 
              onClick={() => handleSendMessage(messages[messages.length - 1]?.content || '')}
              className="p-1.5 hover:bg-red-100 rounded-md text-red-600 font-bold font-mono text-[10px] uppercase"
            >
              Retry
            </button>
          </div>
        )}

        <div ref={chatBottomRef} />
      </div>

      {/* Suggestion Chips Row */}
      {messages.length === 1 && (
        <div className="px-6 py-3 border-t border-brand-border bg-slate-50/50 flex flex-wrap gap-2 select-none">
          {suggestionChips.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleSendMessage(chip)}
              className="px-3 py-1.5 bg-white border border-brand-border rounded-full text-xs font-sans font-medium text-slate-700 hover:text-brand-primary hover:border-brand-primary hover:bg-indigo-50/30 transition-all cursor-pointer"
            >
              {chip}
            </button>
          ))}
        </div>
      )}

      {/* Input container footer */}
      <div className="p-4 border-t border-brand-border bg-white select-none">
        <form 
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage(input);
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder={loading ? "Analyzing consensus data streams..." : "Ask Alpha-AI operator console..."}
            className="flex-1 px-4 py-3 bg-slate-50 border border-brand-border rounded-xl text-sm font-sans font-medium focus:outline-hidden focus:bg-white focus:border-brand-primary focus:ring-2 focus:ring-indigo-200 transition-all"
            id="chat-input-field"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className={`px-4 py-3 bg-[#4d41df] text-white rounded-xl flex items-center gap-1.5 font-bold text-xs uppercase tracking-wider transition-all cursor-pointer ${
              !input.trim() || loading 
                ? 'opacity-50 cursor-not-allowed' 
                : 'hover:bg-indigo-600 hover:scale-[1.02]'
            }`}
            id="btn-chat-send"
          >
            <span>Send</span>
            <Send size={14} />
          </button>
        </form>
      </div>
    </div>
  );
}
