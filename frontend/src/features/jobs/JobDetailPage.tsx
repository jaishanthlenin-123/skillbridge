import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, Briefcase, Building2, ExternalLink, CheckCircle2,
  AlertCircle, Sparkles, Star, Tag, FileText
} from 'lucide-react';
import { api } from '../../services/api';
import type { JobDetail } from '../../types';

export const JobDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [job, setJob] = useState<JobDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchJob() {
      if (!id) return;
      try {
        setLoading(true);
        const data = await api.getJob(id);
        setJob(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load job details.');
      } finally {
        setLoading(false);
      }
    }
    fetchJob();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="h-8 w-8 border-3 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="p-8 text-center glass-panel rounded-xl">
        <AlertCircle className="h-8 w-8 text-rose-400 mx-auto mb-2" />
        <p className="text-white font-semibold">Job not found</p>
        <Link to="/jobs" className="inline-block mt-4 text-xs text-indigo-400 font-medium">
          ← Back to Jobs
        </Link>
      </div>
    );
  }

  const mandatoryReqs = job.requirements.filter((r) => r.is_mandatory);
  const preferredReqs = job.requirements.filter((r) => !r.is_mandatory);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            to="/jobs"
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">{job.title}</h2>
            <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5">
              <span>{job.company_name || 'Direct Employer'}</span>
              <span>•</span>
              <span className="text-indigo-400 font-medium">{job.requirements.length} Criteria Identified</span>
              {job.source_url && (
                <>
                  <span>•</span>
                  <a
                    href={job.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 hover:text-indigo-300 text-slate-400"
                  >
                    <span>Job Post</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </>
              )}
            </div>
          </div>
        </div>

        <Link
          to={`/matches?job_id=${job.id}`}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/20"
        >
          <Sparkles className="h-3.5 w-3.5" />
          <span>Match Against Resumes</span>
        </Link>
      </div>

      {/* Requirements Breakdown Card */}
      <div className="glass-panel p-6 rounded-xl space-y-6">
        <div>
          <h3 className="text-base font-semibold text-white">Extracted Role Requirements</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Classified by importance: mandatory criteria have higher mathematical weights than preferred skills.
          </p>
        </div>

        {/* Mandatory Requirements */}
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-rose-400 mb-3 flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-rose-500" />
            <span>Mandatory Requirements ({mandatoryReqs.length})</span>
          </h4>

          {mandatoryReqs.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No mandatory skills detected.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {mandatoryReqs.map((req) => (
                <div key={req.id} className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white">{req.skill_name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 font-semibold border border-rose-500/20">
                      Weight: {req.importance_weight}x
                    </span>
                  </div>
                  {req.evidence_text && (
                    <p className="text-[11px] text-slate-400 mt-2 font-mono bg-slate-950/60 p-2 rounded">
                      "{req.evidence_text}"
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Preferred Requirements */}
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400 mb-3 flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-amber-500" />
            <span>Preferred & Nice-to-Have Skills ({preferredReqs.length})</span>
          </h4>

          {preferredReqs.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No optional skills detected.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {preferredReqs.map((req) => (
                <div key={req.id} className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white">{req.skill_name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 font-semibold border border-amber-500/20">
                      Weight: {req.importance_weight}x
                    </span>
                  </div>
                  {req.evidence_text && (
                    <p className="text-[11px] text-slate-400 mt-2 font-mono bg-slate-950/60 p-2 rounded">
                      "{req.evidence_text}"
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Raw Description Preview */}
      <div className="glass-panel p-6 rounded-xl space-y-3">
        <h3 className="text-base font-semibold text-white flex items-center gap-2">
          <FileText className="h-4 w-4 text-indigo-400" />
          <span>Full Job Description</span>
        </h3>
        <p className="text-xs text-slate-300 font-mono whitespace-pre-line leading-relaxed bg-slate-900/60 p-4 rounded-lg border border-slate-800">
          {job.description}
        </p>
      </div>
    </div>
  );
};
