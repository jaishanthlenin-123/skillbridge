import React, { useState, useEffect, useRef } from 'react';
import {
  MessageSquare, X, Send, Bot, User, Sparkles, ThumbsUp, ThumbsDown,
  AlertCircle, CheckCircle2, Ticket, RefreshCw, ChevronDown
} from 'lucide-react';
import { api } from '../../services/api';
import type { ChatMessage } from '../../types';

export const ChatWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const saved = sessionStorage.getItem('skillbridge_chat_history');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        // ignore
      }
    }
    return [
      {
        role: 'assistant',
        content: 'Hello! I am your SkillBridge Career Assistant. You can ask me how skill matching works, explore personalized learning roadmaps, ask for tips to improve your resume, or request support.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        mode: 'welcome',
      },
    ];
  });

  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [conversationId, setConversationId] = useState<string>(() => {
    const savedId = sessionStorage.getItem('skillbridge_conv_id');
    if (savedId) return savedId;
    const newId = `conv_${Math.random().toString(36).substring(2, 11)}`;
    sessionStorage.setItem('skillbridge_conv_id', newId);
    return newId;
  });

  const [feedbackGiven, setFeedbackGiven] = useState<Record<number, number>>({});
  const [ticketModalOpen, setTicketModalOpen] = useState(false);
  const [ticketEmail, setTicketEmail] = useState('');
  const [ticketSubject, setTicketSubject] = useState('');
  const [serviceStatus, setServiceStatus] = useState<'checking' | 'ready' | 'offline'>('checking');

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let mounted = true;
    const checkStatus = async () => {
      try {
        const res = await api.checkHealth();
        if (mounted) {
          setServiceStatus(res?.status === 'healthy' ? 'ready' : 'offline');
        }
      } catch {
        if (mounted) setServiceStatus('offline');
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    const handleOpenChat = (e?: any) => {
      setIsOpen(true);
      if (e?.detail?.prompt) {
        handleSendMessage(e.detail.prompt);
      }
    };
    window.addEventListener('skillbridge:open-chat', handleOpenChat);
    return () => window.removeEventListener('skillbridge:open-chat', handleOpenChat);
  }, []);

  useEffect(() => {
    sessionStorage.setItem('skillbridge_chat_history', JSON.stringify(messages));
    if (isOpen && typeof messagesEndRef.current?.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  const handleSendMessage = async (customText?: string) => {
    const textToSend = customText || input;
    if (!textToSend.trim() || sending) return;

    const userMsg: ChatMessage = {
      role: 'user',
      content: textToSend.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!customText) setInput('');
    setSending(true);

    try {
      const resp = await api.sendAssistantChat({
        message: textToSend.trim(),
        conversation_id: conversationId,
      });

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: resp.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        mode: resp.mode,
        ticket_number: resp.ticket_number,
        ticket_created: resp.ticket_created,
        can_create_ticket: resp.can_create_ticket,
        grounded_faqs: resp.grounded_faqs,
        persisted_to_mongo: resp.persisted_to_mongo,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errMsg: ChatMessage = {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${err.message || 'Unable to connect to assistant service.'}. Would you like to submit a support ticket?`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        can_create_ticket: true,
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setSending(false);
    }
  };

  const handleCreateTicketFromChat = async () => {
    setSending(true);
    try {
      const resp = await api.sendAssistantChat({
        action: 'create_ticket',
        message: input || 'User requested ticket creation via chat widget',
        conversation_id: conversationId,
        email: ticketEmail || undefined,
        subject: ticketSubject || undefined,
      });

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: resp.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        mode: 'support_ticket_created',
        ticket_number: resp.ticket_number,
        ticket_created: true,
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setTicketModalOpen(false);
    } catch (err: any) {
      alert(`Failed to create ticket: ${err.message}`);
    } finally {
      setSending(false);
    }
  };

  const handleFeedback = async (msgIndex: number, rating: number) => {
    try {
      await api.sendAssistantFeedback({
        conversation_id: conversationId,
        rating,
      });
      setFeedbackGiven((prev) => ({ ...prev, [msgIndex]: rating }));
    } catch {
      // ignore
    }
  };

  const handleClearHistory = () => {
    const freshId = `conv_${Math.random().toString(36).substring(2, 11)}`;
    sessionStorage.setItem('skillbridge_conv_id', freshId);
    setConversationId(freshId);
    setMessages([
      {
        role: 'assistant',
        content: 'Conversation history cleared. How can I help you today?',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
    sessionStorage.removeItem('skillbridge_chat_history');
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 select-none">
      {/* Floating Launcher Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="h-14 w-14 rounded-full bg-gradient-to-tr from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-xl shadow-indigo-600/40 flex items-center justify-center transition-all transform hover:scale-105 active:scale-95 cursor-pointer relative group"
          aria-label="Open AI Assistant"
        >
          <Bot className="h-7 w-7" />
          <span
            className={`absolute -top-1 -right-1 h-3.5 w-3.5 rounded-full border-2 border-slate-950 animate-pulse ${
              serviceStatus === 'ready'
                ? 'bg-emerald-500'
                : serviceStatus === 'checking'
                ? 'bg-amber-500'
                : 'bg-rose-500'
            }`}
          />
          <span className="absolute right-16 bg-slate-900 border border-slate-700 text-white text-xs px-2.5 py-1 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap shadow-lg pointer-events-none">
            Ask AI Assistant
          </span>
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="w-[360px] sm:w-[420px] h-[580px] bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in duration-200">
          {/* Header */}
          <div className="p-4 bg-slate-850 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="h-8 w-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-600/30">
                <Sparkles className="h-4 w-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white flex items-center gap-1.5">
                  Career Assistant
                  {serviceStatus === 'ready' && (
                    <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded">
                      Ready
                    </span>
                  )}
                  {serviceStatus === 'checking' && (
                    <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded">
                      Connecting
                    </span>
                  )}
                  {serviceStatus === 'offline' && (
                    <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded">
                      Offline
                    </span>
                  )}
                </h3>
                <p className="text-[11px] text-slate-400">Career & Resume Guidance</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={handleClearHistory}
                title="Clear conversation"
                className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                title="Close Assistant"
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Quick Suggestion Chips */}
          <div className="px-3 py-2 bg-slate-950/60 border-b border-slate-800/80 flex items-center gap-1.5 overflow-x-auto text-[11px] scrollbar-none">
            <button
              onClick={() => handleSendMessage('How does resume matching work?')}
              className="shrink-0 px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            >
              How matching works
            </button>
            <button
              onClick={() => handleSendMessage('How can I create a personalized learning roadmap?')}
              className="shrink-0 px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            >
              Skill roadmaps
            </button>
            <button
              onClick={() => handleSendMessage('What are key tips to improve my resume for technical roles?')}
              className="shrink-0 px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            >
              Resume tips
            </button>
            <button
              onClick={() => setTicketModalOpen(true)}
              className="shrink-0 px-2.5 py-1 rounded-full bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/30 transition-colors flex items-center gap-1"
            >
              <Ticket className="h-3 w-3" />
              Contact Support
            </button>
          </div>

          {/* Messages Feed */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4 text-xs">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-2.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="h-7 w-7 rounded-lg bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-indigo-400 shrink-0 mt-0.5">
                    <Bot className="h-4 w-4" />
                  </div>
                )}

                <div className={`max-w-[82%] space-y-1.5 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div
                    className={`p-3 rounded-2xl ${
                      msg.role === 'user'
                        ? 'bg-indigo-600 text-white rounded-br-none shadow-md shadow-indigo-600/20'
                        : 'bg-slate-800 border border-slate-700/60 text-slate-200 rounded-bl-none'
                    }`}
                  >
                    <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>

                    {msg.ticket_created && (
                      <div className="mt-2.5 p-2 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 flex items-center gap-1.5 font-semibold">
                        <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
                        <span>Ticket Number: {msg.ticket_number}</span>
                      </div>
                    )}
                  </div>

                  {/* Actions & Feedback for Assistant Messages */}
                  {msg.role === 'assistant' && (
                    <div className="flex items-center gap-2 text-[10px] text-slate-400 px-1">
                      <span>{msg.timestamp}</span>

                      {msg.can_create_ticket && !msg.ticket_created && (
                        <button
                          onClick={() => setTicketModalOpen(true)}
                          className="text-indigo-400 hover:text-indigo-300 font-semibold underline flex items-center gap-1"
                        >
                          <Ticket className="h-3 w-3" />
                          Open Support Ticket
                        </button>
                      )}

                      <div className="ml-auto flex items-center gap-1">
                        <button
                          onClick={() => handleFeedback(idx, 5)}
                          disabled={feedbackGiven[idx] !== undefined}
                          className={`p-1 rounded hover:bg-slate-800 transition-colors ${
                            feedbackGiven[idx] === 5 ? 'text-emerald-400' : 'hover:text-slate-200'
                          }`}
                          title="Helpful"
                        >
                          <ThumbsUp className="h-3 w-3" />
                        </button>
                        <button
                          onClick={() => handleFeedback(idx, 1)}
                          disabled={feedbackGiven[idx] !== undefined}
                          className={`p-1 rounded hover:bg-slate-800 transition-colors ${
                            feedbackGiven[idx] === 1 ? 'text-rose-400' : 'hover:text-slate-200'
                          }`}
                          title="Not helpful"
                        >
                          <ThumbsDown className="h-3 w-3" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {msg.role === 'user' && (
                  <div className="h-7 w-7 rounded-lg bg-slate-700 flex items-center justify-center text-slate-300 shrink-0 mt-0.5">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}

            {sending && (
              <div className="flex gap-2.5 justify-start">
                <div className="h-7 w-7 rounded-lg bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-indigo-400 shrink-0">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="p-3 bg-slate-800 border border-slate-700/60 rounded-2xl rounded-bl-none text-slate-400 flex items-center gap-1.5">
                  <div className="h-2 w-2 bg-indigo-400 rounded-full animate-bounce" />
                  <div className="h-2 w-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.2s]" />
                  <div className="h-2 w-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.4s]" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Ticket Creation Modal Overlay */}
          {ticketModalOpen && (
            <div className="p-3 bg-slate-850 border-t border-slate-700 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-white flex items-center gap-1.5">
                  <Ticket className="h-3.5 w-3.5 text-indigo-400" />
                  Open Direct Support Ticket
                </span>
                <button
                  onClick={() => setTicketModalOpen(false)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
              <input
                type="email"
                placeholder="Your email address (for reply)"
                value={ticketEmail}
                onChange={(e) => setTicketEmail(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white placeholder-slate-500 text-xs focus:outline-none focus:border-indigo-500"
              />
              <input
                type="text"
                placeholder="Ticket Subject"
                value={ticketSubject}
                onChange={(e) => setTicketSubject(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white placeholder-slate-500 text-xs focus:outline-none focus:border-indigo-500"
              />
              <button
                onClick={handleCreateTicketFromChat}
                disabled={sending}
                className="w-full py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg text-xs transition-colors"
              >
                Confirm & Create Support Ticket
              </button>
            </div>
          )}

          {/* Input Footer */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="p-3 bg-slate-950 border-t border-slate-800 flex items-center gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about career planning, skills, or resume advice..."
              disabled={sending}
              className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
            <button
              type="submit"
              disabled={!input.trim() || sending}
              className="p-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-xl transition-colors cursor-pointer shrink-0"
              aria-label="Send Message"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      )}
    </div>
  );
};
