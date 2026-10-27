import React, { useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import {
  GitCompare, Plus, Eye, Trash2, AlertCircle, CheckCircle2,
  Sparkles, FileText, Briefcase, Download, ArrowRight
} from 'lucide-react';
import { api } from '../../services/api';
import type { MatchListItem, ResumeListItem, JobListItem } from '../../types';

export const MatchesPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [matches, setMatches] = useState<MatchListItem[]>([]);
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Match formulation form
  const [selectedResumeId, setSelectedResumeId] = useState(searchParams.get('resume_id') || '');
  const [selectedJobId, setSelectedJobId] = useState(searchParams.get('job_id') || '');
  const [calculating, setCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [matchesData, resumesData, jobsData] = await Promise.all([
        api.getMatches(),
        api.getResumes(),
        api.getJobs(),
      ]);
      setMatches(matchesData);
      setResumes(resumesData);
      setJobs(jobsData);

      if (!selectedResumeId && resumesData.length > 0) {
        setSelectedResumeId(resumesData[0].id);
      }
      if (!selectedJobId && jobsData.length > 0) {
        setSelectedJobId(jobsData[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load matching records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRunMatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedResumeId || !selectedJobId) {
      setError('Please select both a resume and a job description.');
      return;
    }

    setError(null);
    setCalculating(true);

    try {
      const match = await api.createMatch(selectedResumeId, selectedJobId);
      navigate(`/matches/${match.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to analyze skill match.');
    } finally {
      setCalculating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this match record?')) return;
    try {
      await api.deleteMatch(id);
      setMatches(matches.filter((m) => m.id !== id));
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Skill Match Analysis</h2>
        <p className="text-sm text-slate-400 mt-1">
          Compare your resume against any target job to discover your strengths, skill gaps, and recommended next steps.
        </p>
      </div>

      {/* Match Creation Panel */}
      <div className="glass-panel p-6 rounded-2xl border border-indigo-500/20">
        <h3 className="text-base font-semibold text-white flex items-center gap-2 mb-4">
          <Sparkles className="h-4 w-4 text-indigo-400" />
          <span>Compare Resume with Job</span>
        </h3>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
            {error}
          </div>
        )}

        {resumes.length === 0 && !loading && (
          <div className="mb-4 p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
            <span className="text-indigo-200">
              Please upload a resume first to evaluate qualification fit against our job library.
            </span>
            <Link
              to="/resumes"
              className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shrink-0 shadow-md transition-all flex items-center gap-1.5"
            >
              <FileText className="h-3.5 w-3.5" />
              <span>Upload Resume First</span>
            </Link>
          </div>
        )}

        <form onSubmit={handleRunMatch} className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Select Resume</label>
            <select
              value={selectedResumeId}
              onChange={(e) => setSelectedResumeId(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              {resumes.length === 0 && <option value="">No resumes found - upload one first</option>}
              {resumes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.title} ({r.original_filename})
                </option>
              ))}
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Select Target Job</label>
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              {jobs.length === 0 && <option value="">No jobs found - create one or seed samples</option>}
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.is_sample ? '📋 [Sample] ' : '💼 '}{j.title} {j.company_name ? `(${j.company_name})` : ''}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={calculating || resumes.length === 0 || jobs.length === 0}
            className="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-xs rounded-lg flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 cursor-pointer h-[34px]"
          >
            {calculating ? (
              <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <GitCompare className="h-3.5 w-3.5" />
                <span>Analyze Match</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* Match History Table */}
      <div className="glass-panel rounded-xl overflow-hidden">
        <div className="p-5 border-b border-slate-800">
          <h3 className="text-base font-semibold text-white">Match Evaluations ({matches.length})</h3>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading evaluations...</div>
        ) : matches.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <GitCompare className="h-8 w-8 mx-auto mb-2 text-slate-600" />
            <p className="text-sm font-medium">No match analyses found</p>
            <p className="text-xs mt-1">Select a resume and job description above to compute your first match score.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {matches.map((m) => (
              <div key={m.id} className="p-4 sm:p-5 hover:bg-slate-900/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-colors">
                <div className="flex items-center gap-3 sm:gap-4 min-w-0 pr-0 sm:pr-4">
                  <div className="h-12 w-12 rounded-xl bg-gradient-to-tr from-indigo-950 to-slate-800 border border-indigo-500/30 flex items-center justify-center shrink-0">
                    <span className="text-sm font-bold text-indigo-400">{m.overall_score}%</span>
                  </div>
                  <div className="truncate">
                    <Link
                      to={`/matches/${m.id}`}
                      className="text-sm font-semibold text-white hover:text-indigo-400 transition-colors truncate block"
                    >
                      {m.job_title}
                    </Link>
                    <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs text-slate-400 mt-1">
                      <span>Resume: {m.resume_title}</span>
                      <span>•</span>
                      <span>Weighted: {m.weighted_coverage_score}%</span>
                      <span>•</span>
                      <span>Overlap: {m.coverage_score}%</span>
                      <span>•</span>
                      <span>{new Date(m.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0 self-start sm:self-auto">
                  <Link
                    to={`/matches/${m.id}`}
                    className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-md"
                  >
                    <span>View Analysis</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>

                  <button
                    onClick={() => handleDelete(m.id)}
                    className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
                    title="Delete Match"
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
