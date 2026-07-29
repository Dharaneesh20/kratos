import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Bot, Send, User, Sparkles, Zap, Wifi, WifiOff, ChevronRight, RefreshCw } from 'lucide-react';
import { SpectatorMetrics } from '../types';

interface DisasterChatbotProps {
  workflowId?: string;
  spectatorMetrics?: SpectatorMetrics | null;
  fullScreen?: boolean;
}

interface Message {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  time: string;
  isStreaming?: boolean;
}

const QUICK_QUERIES = [
  'Why was this evacuation route chosen?',
  'Which bridge needs immediate repair?',
  'What is the network resilience status?',
  'Explain the disaster simulation results',
];

// Simple markdown renderer for bold, bullet points, and headers
function renderMarkdown(text: string): React.ReactNode {
  const lines = text.split('\n');
  return lines.map((line, i) => {
    // ### Headers
    if (line.startsWith('### ')) {
      return (
        <p key={i} className="font-bold text-violet-300 mt-3 mb-1 text-xs tracking-wide uppercase">
          {line.replace('### ', '')}
        </p>
      );
    }
    // ## Headers
    if (line.startsWith('## ')) {
      return (
        <p key={i} className="font-bold text-cyan-300 mt-3 mb-1 text-sm">
          {line.replace('## ', '')}
        </p>
      );
    }
    // Numbered list
    if (/^\d+\.\s/.test(line)) {
      const content = line.replace(/^\d+\.\s/, '');
      return (
        <div key={i} className="flex gap-2 my-1">
          <span className="text-violet-400 font-bold font-mono text-xs">{line.match(/^\d+/)?.[0]}.</span>
          <span>{renderInline(content)}</span>
        </div>
      );
    }
    // Bullet
    if (line.startsWith('- ') || line.startsWith('* ')) {
      return (
        <div key={i} className="flex gap-2 my-0.5">
          <span className="text-cyan-400 mt-1">•</span>
          <span>{renderInline(line.replace(/^[-*]\s/, ''))}</span>
        </div>
      );
    }
    // Empty line
    if (!line.trim()) return <div key={i} className="h-2" />;
    return <p key={i} className="my-0.5">{renderInline(line)}</p>;
  });
}

function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="text-white font-semibold">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={i} className="text-violet-300">{part.slice(1, -1)}</em>;
    }
    return part;
  });
}

export function DisasterChatbot({ workflowId, spectatorMetrics, fullScreen }: DisasterChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      sender: 'bot',
      text: `I am **KRATOS Intelligence Agent** — powered by **NVIDIA NeMoTron LLM**.\n\nAsk me:\n- Why specific evacuation routes were chosen\n- Which road junctions need immediate repair\n- How the disaster simulation impacted network resilience\n\nRun a workflow first, then I can provide grounded tactical analysis.`,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const nimOnline = spectatorMetrics?.nvidia_nim_status === 'ONLINE';

  const handleSendMessage = async (customQuery?: string) => {
    const query = customQuery || inputMessage.trim();
    if (!query || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text: query,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!customQuery) setInputMessage('');
    setIsLoading(true);

    // Add streaming placeholder
    const streamId = (Date.now() + 1).toString();
    setMessages((prev) => [
      ...prev,
      { id: streamId, sender: 'bot', text: '', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), isStreaming: true },
    ]);

    try {
      const resp = await axios.post('/api/chatbot/chat', {
        workflow_id: workflowId,
        message: query,
      });

      const botText = resp.data?.response || 'No explanation returned from Chatbot Agent.';
      setMessages((prev) =>
        prev.map((m) =>
          m.id === streamId ? { ...m, text: botText, isStreaming: false } : m
        )
      );
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === streamId
            ? { ...m, text: '⚠️ Unable to connect to Chatbot Agent. Ensure backend coordinator is running.', isStreaming: false }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`glass-card flex flex-col overflow-hidden ${fullScreen ? 'h-[calc(100vh-160px)]' : 'h-[520px]'}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-white/[0.06] bg-white/[0.02]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600/30 to-cyan-600/20 border border-violet-500/30 flex items-center justify-center">
            <Bot className="w-[18px] h-[18px] text-violet-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              NeMoTron Intelligence
              <span
                className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${
                  nimOnline
                    ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                    : 'bg-white/[0.06] text-muted-foreground border-white/10'
                }`}
              >
                {nimOnline ? '● NIM ONLINE' : '○ FALLBACK'}
              </span>
            </h3>
            <p className="text-[10px] text-muted-foreground">
              Tactical disaster reasoning · Agent 9 · Chatbot Controller
            </p>
          </div>
        </div>

        <button
          onClick={() => handleSendMessage('Explain why this evacuation route was chosen and which bridge repair is most critical.')}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-violet-600/15 hover:bg-violet-600/25 text-violet-300 border border-violet-500/25 transition-all cursor-pointer"
        >
          <Sparkles className="w-3.5 h-3.5" />
          Auto Explain
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 animate-fade-in ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.sender === 'bot' && (
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-600/30 to-cyan-600/20 border border-violet-500/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Bot className="w-3.5 h-3.5 text-violet-400" />
              </div>
            )}

            <div
              className={`max-w-[82%] rounded-xl px-4 py-3 text-xs leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-gradient-to-br from-violet-600/40 to-violet-800/40 text-white border border-violet-500/30 shadow-lg'
                  : 'bg-white/[0.04] text-foreground border border-white/[0.06]'
              }`}
            >
              {msg.isStreaming ? (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <div className="flex gap-1">
                    <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  <span>NeMoTron analyzing telemetry...</span>
                </div>
              ) : msg.sender === 'bot' ? (
                <div className="prose-custom">{renderMarkdown(msg.text)}</div>
              ) : (
                <div className="whitespace-pre-wrap">{msg.text}</div>
              )}
              <div
                className={`text-[10px] mt-1.5 text-right font-mono ${
                  msg.sender === 'user' ? 'text-violet-300/60' : 'text-muted-foreground'
                }`}
              >
                {msg.time}
              </div>
            </div>

            {msg.sender === 'user' && (
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-600 to-violet-800 flex items-center justify-center flex-shrink-0 mt-0.5">
                <User className="w-3.5 h-3.5 text-white" />
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Query Chips */}
      <div className="px-4 pb-2 flex gap-2 overflow-x-auto">
        {QUICK_QUERIES.map((q) => (
          <button
            key={q}
            onClick={() => handleSendMessage(q)}
            disabled={isLoading}
            className="flex-shrink-0 text-[10px] px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.08] text-muted-foreground hover:text-foreground hover:border-violet-500/40 hover:bg-violet-500/10 transition-all cursor-pointer disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input */}
      <form
        onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
        className="p-3 border-t border-white/[0.06] bg-white/[0.02] flex items-center gap-2"
      >
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Ask about evacuation routes, repair priorities, resilience..."
          className="flex-1 bg-white/[0.04] border border-white/[0.08] text-foreground rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-violet-500/50 focus:bg-violet-500/5 transition-all placeholder:text-muted-foreground/60"
        />
        <button
          type="submit"
          disabled={isLoading || !inputMessage.trim()}
          className="flex items-center gap-1.5 px-4 py-2.5 bg-gradient-to-r from-violet-600 to-violet-700 hover:from-violet-500 hover:to-violet-600 text-white rounded-xl text-xs font-semibold transition-all disabled:opacity-50 cursor-pointer shadow-lg glow-violet"
        >
          <Send className="w-3.5 h-3.5" />
          Send
        </button>
      </form>
    </div>
  );
}
