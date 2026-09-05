'use client';

import React, { useState, useRef, useEffect } from 'react';
import { generateCopilotResponse, ChatMessage } from '@/lib/copilot-engine';
import { useGridStore } from '@/store/grid-store';
import { MessageSquare, X, Send, Bot, User, Loader2, Wifi, WifiOff } from 'lucide-react';

export default function GridCopilot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: '1', role: 'assistant', text: 'GridCopilot online. I am connected to live grid state. Ask me about faults, recommendations, or what-if scenarios.' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isGroqConnected, setIsGroqConnected] = useState<boolean | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { gridState, activityLog } = useGridStore();

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const buildGridContext = () => {
    const failedAssets = [
      ...gridState.buses.filter(b => b.status === 'failed').map(b => b.name),
      ...gridState.lines.filter(l => l.status === 'failed').map(l => l.id),
      ...gridState.transformers.filter(t => t.status !== 'healthy').map(t => `${t.name} (${t.status})`),
    ];
    const offlineServices = gridState.services.filter(s => s.status === 'offline').map(s => s.name);
    return {
      scenario: gridState.scenario.name,
      restorationProgress: `${gridState.restoration.pct_complete}%`,
      failedAssets: failedAssets.slice(0, 10),
      offlineServices,
      currentRecommendation: gridState.recommendation?.action?.name || 'None — restoration complete',
      customersAffected: gridState.impact.customers_affected,
      criticalFacilitiesOffline: gridState.impact.critical_facilities_offline,
      recentLog: activityLog[0]?.message || 'No recent activity',
    };
  };

  const handleSend = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isTyping) return;

    const userMsg: ChatMessage = { id: Date.now().toString(), role: 'user', text: input.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg.text, context: buildGridContext() }),
      });

      const data = await response.json();

      if (!response.ok) {
        // If API key missing → fall back to local rules engine silently
        setIsGroqConnected(false);
        const fallback = generateCopilotResponse(userMsg.text);
        setMessages(prev => [...prev, { id: Date.now().toString(), role: 'assistant', text: fallback }]);
      } else {
        setIsGroqConnected(true);
        setMessages(prev => [...prev, { id: Date.now().toString(), role: 'assistant', text: data.text }]);
      }
    } catch (_e: unknown) {
      // Network error → fall back gracefully
      setIsGroqConnected(false);
      const fallback = generateCopilotResponse(userMsg.text);
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'assistant', text: fallback }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <>
      {/* Floating Action Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 p-4 bg-blue-600 text-white rounded-full shadow-2xl hover:bg-blue-700 transition-all flex items-center justify-center z-50 animate-bounce"
          title="Open GridCopilot AI"
        >
          <MessageSquare className="w-6 h-6" />
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 bg-white border border-slate-200 rounded-2xl shadow-2xl flex flex-col z-50 overflow-hidden" style={{ height: '530px' }}>

          {/* Header */}
          <div className="bg-blue-600 p-4 text-white flex justify-between items-center shadow-md z-10">
            <div className="flex items-center gap-2">
              <Bot className="w-5 h-5 text-blue-200" />
              <div>
                <h3 className="font-semibold text-sm">GridCopilot</h3>
                <div className="flex items-center gap-1.5">
                  {isGroqConnected === true && (
                    <><Wifi className="w-3 h-3 text-green-300" /><p className="text-[10px] text-green-300">Groq AI Connected</p></>
                  )}
                  {isGroqConnected === false && (
                    <><WifiOff className="w-3 h-3 text-amber-300" /><p className="text-[10px] text-amber-300">Local Mode — add GROQ_API_KEY for full AI</p></>
                  )}
                  {isGroqConnected === null && (
                    <p className="text-[10px] text-blue-200">AI Operator Assistant · Powered by Groq</p>
                  )}
                </div>
              </div>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-blue-200 hover:text-white transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-blue-100 text-blue-700' : 'bg-slate-200 text-slate-700'}`}>
                  {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>
                <div className={`p-3 rounded-2xl text-sm shadow-sm whitespace-pre-wrap max-w-[78%] ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-tr-none'
                    : 'bg-white border border-slate-100 text-slate-700 rounded-tl-none'
                }`}>
                  {msg.text}
                </div>
              </div>
            ))}

            {/* Typing Indicator */}
            {isTyping && (
              <div className="flex gap-3 flex-row">
                <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-slate-200 text-slate-700">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="p-3 rounded-2xl bg-white border border-slate-100 rounded-tl-none flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
                  <span className="text-xs text-slate-400">Analyzing grid parameters...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts */}
          <div className="px-3 pt-2 pb-1 bg-white border-t border-slate-100 flex gap-1.5 flex-wrap">
            {['Grid status?', 'Inspect T3', 'Best next action?', 'What if T3 fails?'].map(prompt => (
              <button
                key={prompt}
                onClick={() => { setInput(prompt); }}
                className="text-[11px] px-2.5 py-1 bg-slate-100 hover:bg-blue-50 hover:text-blue-600 text-slate-600 rounded-full border border-slate-200 transition-colors"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Input Area */}
          <form onSubmit={handleSend} className="p-3 bg-white border-t border-slate-100 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about faults, crews, recovery plan..."
              className="flex-1 px-4 py-2 bg-slate-50 border border-slate-200 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <button
              type="submit"
              disabled={!input.trim() || isTyping}
              className="p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}
    </>
  );
}
