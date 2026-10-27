import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Upload, FileText, Trash2, Eye, AlertCircle, CheckCircle2,
  Clock, Plus, ShieldCheck, ArrowRight
} from 'lucide-react';
import { api } from '../../services/api';
import type { ResumeListItem } from '../../types';

export const ResumesPage: React.FC = () => {
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchResumes = async () => {
    try {
      setLoading(true);
      const data = await api.getResumes();
      setResumes(data);
    } catch (err: any) {
      setUploadError(err.message || 'Failed to load resumes.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResumes();
  }, []);

  const handleFileUpload = async (file: File) => {
    setUploadError(null);
    setUploadSuccess(null);

    // Frontend validation
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'pdf' && ext !== 'docx') {
      setUploadError('Invalid format. Only PDF and DOCX files are supported.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setUploadError('File size exceeds the 10MB limit.');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', file.name.replace(/\.[^/.]+$/, ''));

    try {
      const created = await api.uploadResume(formData);
      setUploadSuccess(`"${created.title}" successfully uploaded and analyzed.`);
      fetchResumes();
    } catch (err: any) {
      setUploadError(err.message || 'Failed to parse resume document.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string, title: string) => {
    if (!window.confirm(`Are you sure you want to permanently delete "${title}"?`)) {
      return;
    }
    try {
      await api.deleteResume(id);
      setResumes((prev) => prev.filter((r) => r.id !== id));
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleDiscardGuest = async () => {
    if (!window.confirm('Discard your guest session and delete your temporary uploads?')) {
      return;
    }
    await api.discardGuestSession();
    setResumes([]);
    setUploadSuccess('Guest session cleared.');
  };

  const isGuest = api.isGuest();

  return (
    <div className="space-y-8">
      {isGuest && (
        <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Sparkles className="h-5 w-5 text-indigo-400 shrink-0" />
            <p className="text-xs text-indigo-200">
              <strong>Guest Exploration Mode:</strong> You can upload your resume, inspect extracted skills, and run skill match analyses freely. Sign up or log in anytime to preserve your work permanently.
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Link
              to="/register"
              className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md transition-all"
            >
              Save Profile
            </Link>
            {resumes.length > 0 && (
              <button
                onClick={handleDiscardGuest}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors cursor-pointer"
              >
                Discard Session
              </button>
            )}
          </div>
        </div>
      )}

      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Resume Management</h2>
        <p className="text-sm text-slate-400 mt-1">
          Upload resumes in PDF or DOCX format (up to 10MB) to analyze your skills and match against jobs. Your files are stored securely in your private session.
        </p>
      </div>

      {/* Upload Zone */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileUpload(e.dataTransfer.files[0]);
          }
        }}
        onClick={() => fileInputRef.current?.click()}
        className="glass-panel p-8 rounded-2xl border-2 border-dashed border-slate-700/80 hover:border-indigo-500/80 transition-all cursor-pointer text-center group"
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
          accept=".pdf,.docx"
          className="hidden"
        />

        <div className="mx-auto w-12 h-12 rounded-xl bg-indigo-600/10 text-indigo-400 group-hover:bg-indigo-600 group-hover:text-white flex items-center justify-center transition-all mb-4 shadow-md">
          {uploading ? (
            <div className="h-5 w-5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
          ) : (
            <Upload className="h-6 w-6" />
          )}
        </div>

        <h3 className="text-base font-semibold text-white">
          {uploading ? 'Analyzing resume skills...' : 'Drop your resume here, or click to browse'}
        </h3>
        <p className="text-xs text-slate-400 mt-1">Supports PDF and DOCX up to 10MB • Private Secure Storage</p>

        <div className="mt-4 flex items-center justify-center gap-4 text-[11px] text-slate-500">
          <span className="flex items-center gap-1">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" /> Secure file verification
          </span>
          <span>•</span>
          <span>Automatic skill extraction</span>
        </div>
      </div>

      {uploadError && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-start gap-3">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
          <span>{uploadError}</span>
        </div>
      )}

      {uploadSuccess && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-start gap-3">
          <CheckCircle2 className="h-5 w-5 shrink-0 mt-0.5" />
          <span>{uploadSuccess}</span>
        </div>
      )}

      {/* Resumes List Table */}
      <div className="glass-panel rounded-xl overflow-hidden">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-base font-semibold text-white">Uploaded Resumes ({resumes.length})</h3>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading resumes...</div>
        ) : resumes.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <FileText className="h-8 w-8 mx-auto mb-2 text-slate-600" />
            <p className="text-sm font-medium">No resumes uploaded yet</p>
            <p className="text-xs mt-1">Upload your first resume using the box above.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {resumes.map((resume) => (
              <div key={resume.id} className="p-5 hover:bg-slate-900/40 flex items-center justify-between transition-colors">
                <div className="flex items-center gap-4 min-w-0 pr-4">
                  <div className="h-10 w-10 rounded-lg bg-slate-800 flex items-center justify-center shrink-0 text-slate-300">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div className="truncate">
                    <Link
                      to={`/resumes/${resume.id}`}
                      className="text-sm font-semibold text-white hover:text-indigo-400 transition-colors truncate block"
                    >
                      {resume.title}
                    </Link>
                    <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                      <span>{resume.original_filename}</span>
                      <span>•</span>
                      <span>{(resume.file_size_bytes / 1024).toFixed(1)} KB</span>
                      <span>•</span>
                      <span className="text-indigo-400 font-medium">{resume.skills_count} skills extracted</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <span
                    className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                      resume.parsing_status === 'COMPLETED'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : resume.parsing_status === 'FAILED'
                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    }`}
                  >
                    {resume.parsing_status_display}
                  </span>

                  {resume.parsing_status === 'COMPLETED' && (
                    <Link
                      to={`/matches?resume_id=${resume.id}`}
                      className="px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-semibold flex items-center gap-1.5 transition-colors"
                    >
                      <span>Analyze Match</span>
                      <ArrowRight className="h-3 w-3" />
                    </Link>
                  )}

                  <Link
                    to={`/resumes/${resume.id}`}
                    className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                    title="View Extracted Details"
                  >
                    <Eye className="h-4 w-4" />
                  </Link>

                  <button
                    onClick={() => handleDelete(resume.id, resume.title)}
                    className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
                    title="Delete Resume"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
