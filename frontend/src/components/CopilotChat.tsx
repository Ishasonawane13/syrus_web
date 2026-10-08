import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, Terminal, Shield, RefreshCw } from 'lucide-react';
import { api, ChatResponse, OrderProposalCard } from '../api';
import { OrderConfirmationCard } from './OrderConfirmationCard';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  orderProposal?: OrderProposalCard | null;
  toolCalls?: Array<{ tool: string; args: any; result: any }>;
  timestamp: Date;
}

const QUICK_PROMPTS = [
  'What is my available cash?',
  'Show my TCS position',
  'Buy 50 TCS at market price',
  'Sell 20 RELIANCE',
  'How much did I make today?',
  'Buy 10000 RELIANCE', // Tests deterministic risk engine rejection
];

interface Props {
  onTradeExecuted?: () => void;
}

export const CopilotChat: React.FC<Props> = ({ onTradeExecuted }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: "👋 Welcome to your **AI Trading Copilot**. I can help you inspect your paper portfolio, view stock quotes, and create verified trading proposals with deterministic safety checks.\n\nTry clicking one of the suggested prompts below or type your instruction!",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (userPrompt?: string) => {
    const messageText = (userPrompt || input).trim();
    if (!messageText || loading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: messageText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!userPrompt) setInput('');
    setLoading(true);

    try {
      const response: ChatResponse = await api.sendChat(messageText, conversationId);
      setConversationId(response.conversation_id);

      const botMsg: Message = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        text: response.message,
        orderProposal: response.order_proposal,
        toolCalls: response.tool_calls,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          sender: 'assistant',
          text: `⚠️ Error processing request: ${err.message || 'Server error'}`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const formatMarkdown = (text: string) => {
    // Simple inline bold and list formatting
    return text.split('\n').map((line, idx) => {
      let formatted = line;
      // Bold **text**
      const parts = formatted.split(/(\*\*.*?\*\*)/g);
      return (
        <div key={idx} className={line.startsWith('- ') ? 'pl-3 my-0.5' : 'my-1'}>
          {parts.map((p, pIdx) => {
            if (p.startsWith('**') && p.endsWith('**')) {
              return <strong key={pIdx} className="font-semibold text-white">{p.slice(2, -2)}</strong>;
            }
            return <span key={pIdx}>{p}</span>;
          })}
        </div>
      );
    });
  };

  return (
    <div className="glass-panel flex flex-col h-[580px] overflow-hidden">
      {/* Copilot Header */}
      <div className="p-4 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 text-white">
            <Bot size={20} />
          </div>
          <div>
            <div className="font-semibold text-sm flex items-center gap-2 text-white">
              AI Trading Copilot
              <span className="glow-pill green text-[10px] py-0 px-2">Safety Guard Active</span>
            </div>
            <div className="text-xs text-slate-400">Natural Language &bull; 8 Risk Rules &bull; Explicit Approval</div>
          </div>
        </div>

        <button
          onClick={() => {
            setMessages([
              {
                id: 'reset',
                sender: 'assistant',
                text: 'Chat history cleared. How can I assist you with your simulated portfolio today?',
                timestamp: new Date(),
              },
            ]);
          }}
          className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-white/5 transition-colors text-xs flex items-center gap-1"
          title="Reset Chat"
        >
          <RefreshCw size={13} />
          Clear
        </button>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4 text-sm">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          return (
            <div key={msg.id} className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}>
              {!isUser && (
                <div className="w-8 h-8 rounded-lg bg-indigo-950/80 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0 mt-0.5">
                  <Bot size={16} />
                </div>
              )}

              <div className={`max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
                <div
                  className={`p-3.5 rounded-2xl ${
                    isUser
                      ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white rounded-tr-none shadow-md shadow-indigo-600/20'
                      : 'bg-slate-900/80 border border-white/10 text-slate-200 rounded-tl-none'
                  }`}
                >
                  <div className="text-[13px] leading-relaxed">{formatMarkdown(msg.text)}</div>

                  {/* Embedded Tool Call Badge */}
                  {msg.toolCalls && msg.toolCalls.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-white/10 flex flex-wrap gap-1.5 text-[11px] text-slate-400 font-mono">
                      {msg.toolCalls.map((tc, idx) => (
                        <span key={idx} className="bg-black/40 px-2 py-0.5 rounded flex items-center gap-1 border border-white/5">
                          <Terminal size={11} className="text-cyan-400" />
                          {tc.tool}()
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Embedded Order Confirmation Card */}
                  {msg.orderProposal && (
                    <OrderConfirmationCard
                      proposal={msg.orderProposal}
                      onExecuted={(orderId) => {
                        onTradeExecuted?.();
                      }}
                      onCancelled={(orderId) => {
                        onTradeExecuted?.();
                      }}
                    />
                  )}
                </div>

                <div className="text-[10px] text-slate-500 mt-1 px-1 font-mono">
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>

              {isUser && (
                <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-slate-200 shrink-0 mt-0.5">
                  <User size={16} />
                </div>
              )}
            </div>
          );
        })}

        {loading && (
          <div className="flex gap-3 justify-start animate-fade-in">
            <div className="w-8 h-8 rounded-lg bg-indigo-950/80 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
              <Bot size={16} />
            </div>
            <div className="bg-slate-900/80 border border-white/10 p-3.5 rounded-2xl rounded-tl-none flex items-center gap-2 text-xs text-slate-400">
              <Sparkles size={14} className="text-indigo-400 animate-spin" />
              Evaluating intent & executing safety tools...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Prompts */}
      <div className="px-4 py-2 bg-black/20 border-t border-white/5 overflow-x-auto flex gap-2 no-scrollbar">
        {QUICK_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            onClick={() => handleSend(prompt)}
            disabled={loading}
            className="text-[11px] whitespace-nowrap bg-white/5 hover:bg-indigo-500/20 text-slate-300 hover:text-indigo-200 border border-white/5 hover:border-indigo-500/30 px-3 py-1 rounded-full transition-all shrink-0 cursor-pointer"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Input Field */}
      <div className="p-3 border-t border-white/5 bg-white/[0.02]">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything or propose a trade (e.g. 'Buy 50 TCS at market')..."
            className="flex-1 bg-slate-900/90 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all font-sans"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="btn-primary py-2.5 px-4 text-sm shrink-0"
          >
            <Send size={15} />
          </button>
        </form>
      </div>
    </div>
  );
};
