import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  LifeBuoy, Send, Search, CheckCircle2, AlertCircle, Clock,
  FileQuestion, Bug, Wrench, Shield, ArrowRight, Edit3, Trash2, X, Check
} from 'lucide-react';
import { api } from '../../services/api';
import type { SupportTicket } from '../../types';

export const SupportPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const tabParam = searchParams.get('tab');
  const [activeTab, setActiveTab] = useState<'submit' | 'lookup' | 'history'>(() => {
    if (tabParam === 'lookup') return 'lookup';
    if (tabParam === 'history') return 'history';
    return 'submit';
  });

  useEffect(() => {
    if (tabParam === 'submit' || tabParam === 'lookup' || tabParam === 'history') {
      setActiveTab(tabParam);
    }
  }, [tabParam]);

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

  // CRUD Edit / Delete State
  const [editingTicketId, setEditingTicketId] = useState<string | null>(null);
  const [editSubject, setEditSubject] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editCategory, setEditCategory] = useState('general');
  const [editStatus, setEditStatus] = useState('open');
  const [editLoading, setEditLoading] = useState(false);
  const [deletingTicketId, setDeletingTicketId] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

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
    setActionMessage(null);

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
    setActionMessage(null);
    setEditingTicketId(null);

    if (!lookupNumber.trim() || !lookupEmail.trim()) {
      setLookupError('Both Ticket Number and Contact Email are required.');
      return;
    }

    setLookupLoading(true);
    try {
      const ticket = await api.lookupSupportTicket(lookupNumber.trim(), lookupEmail.trim());
      setLookupResult(ticket);
    } catch (err: any) {
      setLookupError(err.message || 'No matching active support ticket found.');
    } finally {
      setLookupLoading(false);
    }
  };

  const handleStartEdit = (ticket: SupportTicket) => {
    setEditingTicketId(ticket.id);
    setEditSubject(ticket.subject);
    setEditDescription(ticket.description);
    setEditCategory(ticket.category);
    setEditStatus(ticket.status);
    setActionMessage(null);
  };

  const handleCancelEdit = () => {
    setEditingTicketId(null);
  };

  const handleSaveEdit = async (ticketId: string) => {
    setEditLoading(true);
    setActionMessage(null);
    try {
      const updated = await api.updateSupportTicket(ticketId, {
        subject: editSubject.trim(),
        description: editDescription.trim(),
        category: editCategory,
        status: editStatus,
      });
      setMyTickets((prev) => prev.map((t) => (t.id === ticketId ? { ...t, ...updated } : t)));
      if (lookupResult && lookupResult.id === ticketId) {
        setLookupResult((prev) => (prev ? { ...prev, ...updated } : null));
      }
      setEditingTicketId(null);
      setActionMessage({ type: 'success', text: `Ticket ${updated.ticket_number} updated successfully.` });
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.message || 'Failed to update ticket.' });
    } finally {
      setEditLoading(false);
    }
  };

  const handleDeleteTicket = async (ticket: SupportTicket) => {
    if (!window.confirm(`Are you sure you want to cancel / delete ticket ${ticket.ticket_number}?`)) {
      return;
    }
    setDeletingTicketId(ticket.id);
    setActionMessage(null);
    try {
      await api.deleteSupportTicket(ticket.id);
      setMyTickets((prev) => prev.filter((t) => t.id !== ticket.id));
      if (lookupResult && lookupResult.id === ticket.id) {
        setLookupResult(null);
      }
      setActionMessage({ type: 'success', text: `Ticket ${ticket.ticket_number} deleted successfully.` });
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.message || 'Failed to delete ticket.' });
    } finally {
      setDeletingTicketId(null);
    }
  };

  const handleSaveLookupEdit = async () => {
    if (!lookupResult) return;
    setEditLoading(true);
    setActionMessage(null);
    try {
      const updated = await api.updateLookupSupportTicket({
        ticket_number: lookupNumber.trim(),
        email: lookupEmail.trim(),
        subject: editSubject.trim(),
        description: editDescription.trim(),
        category: editCategory,
        status: editStatus,
      });
      setLookupResult(updated);
      setEditingTicketId(null);
      setActionMessage({ type: 'success', text: `Ticket ${updated.ticket_number} updated successfully.` });
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.message || 'Failed to update ticket.' });
    } finally {
      setEditLoading(false);
    }
  };

  const handleDeleteLookupTicket = async () => {
    if (!lookupResult) return;
    if (!window.confirm(`Are you sure you want to cancel / delete ticket ${lookupResult.ticket_number}?`)) {
      return;
    }
    setEditLoading(true);
    setActionMessage(null);
    try {
      await api.deleteLookupSupportTicket(lookupNumber.trim(), lookupEmail.trim());
      setLookupResult(null);
      setActionMessage({ type: 'success', text: 'Support ticket deleted successfully.' });
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.message || 'Failed to delete ticket.' });
    } finally {
      setEditLoading(false);
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

      {/* Global Action Message Banner */}
      {actionMessage && (
        <div className={`p-4 rounded-xl text-xs flex items-center justify-between border ${
          actionMessage.type === 'success'
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
            : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
        }`}>
          <span>{actionMessage.text}</span>
          <button onClick={() => setActionMessage(null)} className="p-1 hover:text-white cursor-pointer">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

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
            <div className="mb-6 p-3.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          <form onSubmit={handleSubmitTicket} className="space-y-4">
            {!token && (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Your Email Address <span className="text-rose-400">*</span>
                </label>
                <input
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Issue Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="general">General Inquiry</option>
                <option value="matching">Resume Matching Issue</option>
                <option value="parsing">Resume Parsing Error</option>
                <option value="account">Account / Login Issue</option>
                <option value="bug">Bug Report</option>
                <option value="feature">Feature Request</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Priority Level
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="low">Low Priority</option>
                <option value="normal">Normal</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Subject <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                placeholder="Brief summary of the issue"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                required
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Description & Steps to Reproduce <span className="text-rose-400">*</span>
              </label>
              <textarea
                rows={4}
                placeholder="Provide clear details, including any correlation IDs (X-Request-ID) or displayed error codes (e.g. SB-1001)..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
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
            <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-700 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-white">{lookupResult.ticket_number}</span>
                <span className={`text-[11px] font-bold px-2 py-0.5 rounded border uppercase ${getStatusBadge(lookupResult.status)}`}>
                  {lookupResult.status}
                </span>
              </div>

              {editingTicketId === lookupResult.id ? (
                <div className="space-y-3 pt-2 border-t border-slate-800">
                  <div>
                    <label className="block text-[11px] font-medium text-slate-400 mb-1">Subject</label>
                    <input
                      type="text"
                      value={editSubject}
                      onChange={(e) => setEditSubject(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-slate-400 mb-1">Description</label>
                    <textarea
                      rows={3}
                      value={editDescription}
                      onChange={(e) => setEditDescription(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-white"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-[11px] font-medium text-slate-400 mb-1">Category</label>
                      <select
                        value={editCategory}
                        onChange={(e) => setEditCategory(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1.5 text-xs text-white"
                      >
                        <option value="general">General</option>
                        <option value="matching">Matching</option>
                        <option value="parsing">Parsing</option>
                        <option value="account">Account</option>
                        <option value="bug">Bug</option>
                        <option value="feature">Feature</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-[11px] font-medium text-slate-400 mb-1">Status</label>
                      <select
                        value={editStatus}
                        onChange={(e) => setEditStatus(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1.5 text-xs text-white"
                      >
                        <option value="open">Open</option>
                        <option value="closed">Closed (Cancel Ticket)</option>
                      </select>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 pt-1">
                    <button
                      onClick={handleSaveLookupEdit}
                      disabled={editLoading}
                      className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold flex items-center gap-1 cursor-pointer"
                    >
                      <Check className="h-3.5 w-3.5" />
                      <span>{editLoading ? 'Saving...' : 'Save Updates'}</span>
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs cursor-pointer"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <h4 className="text-sm font-semibold text-slate-200">{lookupResult.subject}</h4>
                  <p className="text-xs text-slate-400 whitespace-pre-wrap">{lookupResult.description}</p>
                  <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
                    <span>Category: {lookupResult.category}</span>
                    <span>Created: {new Date(lookupResult.created_at).toLocaleString()}</span>
                  </div>

                  <div className="pt-2 border-t border-slate-800 flex items-center gap-2">
                    <button
                      onClick={() => handleStartEdit(lookupResult)}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-750 text-indigo-300 border border-indigo-500/30 rounded text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
                    >
                      <Edit3 className="h-3.5 w-3.5" />
                      <span>Edit Details</span>
                    </button>
                    <button
                      onClick={handleDeleteLookupTicket}
                      disabled={editLoading}
                      className="px-3 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 rounded text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      <span>Cancel Ticket</span>
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: My Tickets (Authenticated) */}
      {activeTab === 'history' && (
        <div className="glass-panel rounded-2xl overflow-hidden border border-slate-800">
          <div className="p-5 border-b border-slate-800 flex items-center justify-between">
            <h3 className="text-base font-semibold text-white">Your Support Tickets ({myTickets.length})</h3>
            <button
              onClick={loadMyTickets}
              disabled={loadingTickets}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium cursor-pointer"
            >
              Refresh
            </button>
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
                <div key={t.id} className="p-5 hover:bg-slate-900/40 transition-colors">
                  {editingTicketId === t.id ? (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono font-bold text-indigo-400">{t.ticket_number}</span>
                        <span className="text-[11px] text-slate-500">Editing Ticket</span>
                      </div>
                      <div>
                        <label className="block text-[11px] font-medium text-slate-400 mb-1">Subject</label>
                        <input
                          type="text"
                          value={editSubject}
                          onChange={(e) => setEditSubject(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-white"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-medium text-slate-400 mb-1">Description</label>
                        <textarea
                          rows={3}
                          value={editDescription}
                          onChange={(e) => setEditDescription(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-white"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[11px] font-medium text-slate-400 mb-1">Category</label>
                          <select
                            value={editCategory}
                            onChange={(e) => setEditCategory(e.target.value)}
                            className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1.5 text-xs text-white"
                          >
                            <option value="general">General</option>
                            <option value="matching">Matching</option>
                            <option value="parsing">Parsing</option>
                            <option value="account">Account</option>
                            <option value="bug">Bug</option>
                            <option value="feature">Feature</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-[11px] font-medium text-slate-400 mb-1">Status</label>
                          <select
                            value={editStatus}
                            onChange={(e) => setEditStatus(e.target.value)}
                            className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1.5 text-xs text-white"
                          >
                            <option value="open">Open</option>
                            <option value="closed">Closed (Cancel Ticket)</option>
                          </select>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 pt-1">
                        <button
                          onClick={() => handleSaveEdit(t.id)}
                          disabled={editLoading}
                          className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold flex items-center gap-1 cursor-pointer"
                        >
                          <Check className="h-3.5 w-3.5" />
                          <span>{editLoading ? 'Saving...' : 'Save Changes'}</span>
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs cursor-pointer"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="space-y-1 pr-4 min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono font-bold text-indigo-400">{t.ticket_number}</span>
                          <span className={`text-[10px] uppercase font-bold px-1.5 py-0.2 rounded border ${getStatusBadge(t.status)}`}>
                            {t.status}
                          </span>
                        </div>
                        <h4 className="text-sm font-semibold text-white truncate">{t.subject}</h4>
                        <p className="text-xs text-slate-400 line-clamp-2">{t.description}</p>
                        <div className="text-[11px] text-slate-500 flex items-center gap-3 pt-1">
                          <span>Category: {t.category}</span>
                          <span>Priority: {t.priority}</span>
                          <span>Created: {new Date(t.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>

                      <div className="flex sm:flex-col items-center sm:items-end gap-2 shrink-0">
                        <button
                          onClick={() => handleStartEdit(t)}
                          className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-750 text-indigo-300 border border-indigo-500/20 rounded text-xs font-medium flex items-center gap-1 transition-colors cursor-pointer"
                        >
                          <Edit3 className="h-3 w-3" />
                          <span>Edit</span>
                        </button>
                        <button
                          onClick={() => handleDeleteTicket(t)}
                          disabled={deletingTicketId === t.id}
                          className="px-2.5 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 rounded text-xs font-medium flex items-center gap-1 transition-colors cursor-pointer"
                        >
                          <Trash2 className="h-3 w-3" />
                          <span>{deletingTicketId === t.id ? 'Deleting...' : 'Cancel'}</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
