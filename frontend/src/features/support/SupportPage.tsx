import React, { useState, useEffect } from 'react';
import {
  LifeBuoy, Send, Search, CheckCircle2, AlertCircle, Clock,
  FileQuestion, Bug, Wrench, Shield, ArrowRight
} from 'lucide-react';
import { api } from '../../services/api';
import type { SupportTicket } from '../../types';

export const SupportPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'submit' | 'lookup' | 'history'>('submit');
  const token = localStorage.getItem('skillbridge_token');
  const userJson = localStorage.getItem('skillbridge_user');
  const user = userJson ? JSON.parse(userJson) : null;

  // Form State
  const [email, setEmail] = useState(user?.email || '');
  const [subject, setSubject] = useState('');
  const [category, setCategory] = useState('general');
  const [priority, setPriority] = useState('normal');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [createdTicket, setCreatedTicket] = useState<SupportTicket | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  // Lookup State
  const [lookupNumber, setLookupNumber] = useState('');
  const [lookupEmail, setLookupEmail] = useState('');
  const [lookupResult, setLookupResult] = useState<SupportTicket | null>(null);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupError, setLookupError] = useState<string | null>(null);

  // My Tickets State
  const [myTickets, setMyTickets] = useState<SupportTicket[]>([]);
  const [loadingTickets, setLoadingTickets] = useState(false);

  useEffect(() => {
    if (activeTab === 'history' && token) {
      loadMyTickets();
    }
  }, [activeTab]);

  const loadMyTickets = async () => {
    try {
      setLoadingTickets(true);
      const data = await api.getSupportTickets();
      setMyTickets(data);
    } catch {
      // ignore
    } finally {
      setLoadingTickets(false);
    }
  };

  const handleSubmitTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setCreatedTicket(null);

    if (!email.trim() && !token) {
      setFormError('Contact email is required.');
      return;
    }
    if (!subject.trim() || !description.trim()) {
      setFormError('Subject and description cannot be empty.');
      return;
    }

    setSubmitting(true);
    try {
      const ticket = await api.createSupportTicket({
        contact_email: email.trim(),
        subject: subject.trim(),
        category,
        priority,
        description: description.trim(),
      });
      setCreatedTicket(ticket);
      setSubject('');
      setDescription('');
    } catch (err: any) {
      setFormError(err.message || 'Failed to submit support ticket.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLookupError(null);
    setLookupResult(null);

    if (!lookupNumber.trim() || !lookupEmail.trim()) {
      setLookupError('Both Ticket Number and Contact Email are required.');
      return;
    }

    setLookupLoading(true);
    try {
      const ticket = await api.lookupSupportTicket(lookupNumber.trim(), lookupEmail.trim());
      setLookupResult(ticket);
    } catch (err: any) {
      setLookupError(err.message || 'No matching support ticket found.');
    } finally {
      setLookupLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'resolved':
      case 'closed':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'in_progress':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      default:
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto py-4">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold">
          <LifeBuoy className="h-3.5 w-3.5" />
          Technical Support & Inquiries
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight sm:text-4xl">
          Support Desk
        </h1>
        <p className="text-slate-400 text-sm max-w-lg mx-auto">
          Need help with resume parsing, matching analysis, or account issues? Submit a ticket to our engineering team.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 justify-start sm:justify-center gap-2 sm:gap-4 text-xs sm:text-sm font-semibold overflow-x-auto scrollbar-none pb-0.5">
        <button
          onClick={() => setActiveTab('submit')}
          className={`pb-3 px-3 sm:px-4 transition-colors border-b-2 cursor-pointer whitespace-nowrap shrink-0 ${
            activeTab === 'submit'
              ? 'border-indigo-500 text-white'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Submit Ticket
        </button>
        <button
          onClick={() => setActiveTab('lookup')}
          className={`pb-3 px-3 sm:px-4 transition-colors border-b-2 cursor-pointer whitespace-nowrap shrink-0 ${
            activeTab === 'lookup'
              ? 'border-indigo-500 text-white'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Track Ticket Status
        </button>
        {token && (
          <button
            onClick={() => setActiveTab('history')}
            className={`pb-3 px-3 sm:px-4 transition-colors border-b-2 cursor-pointer whitespace-nowrap shrink-0 ${
              activeTab === 'history'
                ? 'border-indigo-500 text-white'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            My Submitted Tickets
          </button>
        )}
      </div>

      {/* Tab 1: Submit Form */}
      {activeTab === 'submit' && (
        <div className="glass-panel p-6 sm:p-8 rounded-2xl max-w-2xl mx-auto border border-slate-800">
          {createdTicket && (
            <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 space-y-1">
              <div className="flex items-center gap-2 font-semibold">
                <CheckCircle2 className="h-4 w-4" />
                <span>Ticket Created Successfully!</span>
              </div>
              <p className="text-xs text-emerald-400">
                Your ticket number is <strong className="text-white underline">{createdTicket.ticket_number}</strong>.
                We have recorded your inquiry in our database and will respond to <span className="text-white">{createdTicket.contact_email}</span>.
              </p>
            </div>
          )}

          {formError && (
            <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          <form onSubmit={handleSubmitTicket} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Contact Email Address <span className="text-rose-400">*</span>
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="general">General Inquiry</option>
                  <option value="parsing">Resume Parsing Issue (SB-1001)</option>
                  <option value="matching">Match Scoring Issue</option>
                  <option value="account">Account & Permissions</option>
                  <option value="bug">Bug Report</option>
                  <option value="feature">Feature Request</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Priority</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="low">Low</option>
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Subject / Summary <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Brief summary of the issue..."
                required
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Detailed Description <span className="text-rose-400">*</span>
              </label>
              <textarea
                rows={5}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Please include any correlation IDs (X-Request-ID), error codes, or document steps to help us troubleshoot..."
                required
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-sm rounded-lg flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30 transition-colors cursor-pointer"
            >
              {submitting ? (
                <div className="h-5 w-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <Send className="h-4 w-4" />
                  <span>Submit Support Ticket</span>
                </>
              )}
            </button>
          </form>
        </div>
      )}

      {/* Tab 2: Track Ticket Lookup */}
      {activeTab === 'lookup' && (
        <div className="glass-panel p-6 sm:p-8 rounded-2xl max-w-xl mx-auto border border-slate-800 space-y-6">
          <form onSubmit={handleLookup} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Ticket Number</label>
              <input
                type="text"
                placeholder="e.g. SB-2026-12345"
                value={lookupNumber}
                onChange={(e) => setLookupNumber(e.target.value)}
                required
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Registered Contact Email</label>
              <input
                type="email"
                placeholder="The email provided when creating the ticket"
                value={lookupEmail}
                onChange={(e) => setLookupEmail(e.target.value)}
                required
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            {lookupError && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
                {lookupError}
              </div>
            )}

            <button
              type="submit"
              disabled={lookupLoading}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-sm rounded-lg flex items-center justify-center gap-2 transition-colors cursor-pointer"
            >
              {lookupLoading ? 'Searching...' : 'Find Ticket Status'}
            </button>
          </form>

          {lookupResult && (
            <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-700 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-white">{lookupResult.ticket_number}</span>
                <span className={`text-[11px] font-bold px-2 py-0.5 rounded border uppercase ${getStatusBadge(lookupResult.status)}`}>
                  {lookupResult.status}
                </span>
              </div>
              <h4 className="text-sm font-semibold text-slate-200">{lookupResult.subject}</h4>
              <p className="text-xs text-slate-400 whitespace-pre-wrap">{lookupResult.description}</p>
              <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
                <span>Category: {lookupResult.category}</span>
                <span>Created: {new Date(lookupResult.created_at).toLocaleString()}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: My Tickets (Authenticated) */}
      {activeTab === 'history' && (
        <div className="glass-panel rounded-2xl overflow-hidden border border-slate-800">
          <div className="p-5 border-b border-slate-800">
            <h3 className="text-base font-semibold text-white">Your Support Tickets ({myTickets.length})</h3>
          </div>

          {loadingTickets ? (
            <div className="p-12 text-center text-slate-400">Loading your tickets...</div>
          ) : myTickets.length === 0 ? (
            <div className="p-12 text-center text-slate-500">
              <FileQuestion className="h-8 w-8 mx-auto mb-2 text-slate-600" />
              <p className="text-sm font-medium">No support tickets found</p>
              <p className="text-xs mt-1">If you experience any issues, submit a ticket above.</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-800/80">
              {myTickets.map((t) => (
                <div key={t.id} className="p-5 hover:bg-slate-900/40 flex items-center justify-between transition-colors">
                  <div className="space-y-1 pr-4 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-indigo-400">{t.ticket_number}</span>
                      <span className={`text-[10px] uppercase font-bold px-1.5 py-0.2 rounded border ${getStatusBadge(t.status)}`}>
                        {t.status}
                      </span>
                    </div>
                    <h4 className="text-sm font-semibold text-white truncate">{t.subject}</h4>
                    <p className="text-xs text-slate-400 line-clamp-1">{t.description}</p>
                  </div>
                  <div className="text-right shrink-0 text-xs text-slate-500">
                    <div>{new Date(t.created_at).toLocaleDateString()}</div>
                    <div className="capitalize text-[11px] mt-0.5">{t.priority} priority</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
