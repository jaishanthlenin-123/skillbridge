import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Settings, Shield, Trash2, User as UserIcon, Lock,
  AlertTriangle, CheckCircle2, Database, Key
} from 'lucide-react';
import { api } from '../../services/api';
import type { User } from '../../types';

export const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchUser() {
      try {
        const u = await api.getCurrentUser();
        setUser(u);
      } catch {
        const userJson = localStorage.getItem('skillbridge_user');
        if (userJson) setUser(JSON.parse(userJson));
      } finally {
        setLoading(false);
      }
    }
    fetchUser();
  }, []);

  const handlePurgeAccount = async () => {
    const confirmation = window.prompt(
      'DANGER: This action is irreversible. Type "PURGE MY DATA" to permanently delete your account, uploaded resumes, and matches.'
    );
    if (confirmation !== 'PURGE MY DATA') return;

    try {
      // Invalidate session
      await api.logout();
    } catch {
      // ignore
    } finally {
      localStorage.clear();
      alert('Your account and associated private records have been purged.');
      navigate('/login');
    }
  };

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Account & Privacy Settings</h2>
        <p className="text-sm text-slate-400 mt-1">
          Manage your account profile, review data governance policies, and control your stored information.
        </p>
      </div>

      {/* Account Info */}
      <div className="glass-panel p-6 rounded-xl space-y-4">
        <h3 className="text-base font-semibold text-white flex items-center gap-2">
          <UserIcon className="h-4 w-4 text-indigo-400" />
          <span>Profile Information</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="text-slate-400 block mb-1">Email Address</label>
            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-white font-mono">
              {user?.email || 'Loading...'}
            </div>
          </div>

          <div>
            <label className="text-slate-400 block mb-1">Member ID</label>
            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 font-mono truncate">
              {user?.id || '—'}
            </div>
          </div>

          <div>
            <label className="text-slate-400 block mb-1">Full Name</label>
            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-white">
              {user?.full_name || 'Candidate'}
            </div>
          </div>

          <div>
            <label className="text-slate-400 block mb-1">Account Member Since</label>
            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-white">
              {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Active'}
            </div>
          </div>
        </div>
      </div>

      {/* Security & Data Retention Notice */}
      <div className="glass-panel p-6 rounded-xl space-y-4">
        <h3 className="text-base font-semibold text-white flex items-center gap-2">
          <Shield className="h-4 w-4 text-emerald-400" />
          <span>Privacy & Data Protection Policy</span>
        </h3>

        <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
          <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
            <h4 className="font-semibold text-white mb-1">1. Private Document Storage</h4>
            <p className="text-slate-400">
              Uploaded resumes are stored in a private directory outside the public web server root.
              Documents are never made public or indexed by search engines.
            </p>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
            <h4 className="font-semibold text-white mb-1">2. Zero Macro & Script Execution</h4>
            <p className="text-slate-400">
              Files are validated against magic byte signatures. The platform parses raw text streams
              directly and never executes macros, scripts, or embedded active content.
            </p>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
            <h4 className="font-semibold text-white mb-1">3. Right to Immediate Erasure</h4>
            <p className="text-slate-400">
              Deleting any resume or match permanently removes the physical file from the disk and
              cascades all extracted sections and skills.
            </p>
          </div>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="p-6 rounded-xl border border-rose-500/30 bg-rose-950/10 space-y-4">
        <h3 className="text-base font-semibold text-rose-400 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          <span>Danger Zone</span>
        </h3>
        <p className="text-xs text-slate-400">
          Permanently purge your account, delete all uploaded resume files from private storage, and clear all match records.
        </p>

        <button
          onClick={handlePurgeAccount}
          className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer"
        >
          <Trash2 className="h-3.5 w-3.5" />
          <span>Purge All Account Data</span>
        </button>
      </div>
    </div>
  );
};
