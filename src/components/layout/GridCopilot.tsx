'use client';

import React, { useState, useRef, useEffect } from 'react';
import { generateCopilotResponse, ChatMessage } from '@/lib/copilot-engine';
import { MessageSquare, X, Send, Bot, User, Loader2 } from 'lucide-react';

export default function GridCopilot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: '1', role: 'assistant', text: 'GridGuard Copilot online. How can I help you recover the grid today?' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim()) return;

    const userMsg: ChatMessage = { id: Date.now().toString(), role: 'user', text: input.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMsg.text,
          context: { 
            // We could pass gridStore context here in the future
            gridStatus: "Grid has faults", 
          }
        })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to get response');
      }

      const botMsg: ChatMessage = { id: Date.now().toString(), role: 'assistant', text: data.text };
      setMessages(prev => [...prev, botMsg]);
    } catch (error: any) {
      const errorMsg: ChatMessage = { 
        id: Date.now().toString(), 
        role: 'assistant', 
        text: `Error: ${error.message}. Make sure GROQ_API_KEY is set in your environment.` 
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <>
      {/* Floating Action Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 p-4 bg-blue-600 text-white rounded-full shadow-2xl hover:bg-blue-700 transition-all flex items-center justify-center z-50 animate-bounce"
        >
          <MessageSquare className="w-6 h-6" />
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 bg-white border border-slate-200 rounded-2xl shadow-2xl flex flex-col z-50 overflow-hidden" style={{ height: '500px' }}>
          
          {/* Header */}
          <div className="bg-blue-600 p-4 text-white flex justify-between items-center shadow-md z-10">
            <div className="flex items-center gap-2">
              <Bot className="w-5 h-5 text-blue-200" />
              <div>
                <h3 className="font-semibold text-sm">GridCopilot</h3>
                <p className="text-[10px] text-blue-200">AI Operator Assistant</p>
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
                <div className={`p-3 rounded-2xl text-sm shadow-sm whitespace-pre-wrap ${
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

          {/* Input Area */}
          <form onSubmit={handleSend} className="p-3 bg-white border-t border-slate-100 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about T3, request a summary..."
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
