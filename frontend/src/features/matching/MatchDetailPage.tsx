import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Download, Compass, CheckCircle2, AlertCircle,
  HelpCircle, Sparkles, BookOpen, Layers, Info, ShieldAlert
} from 'lucide-react';
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip
} from 'recharts';
import { api } from '../../services/api';
import type { MatchDetail } from '../../types';

export const MatchDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [match, setMatch] = useState<MatchDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generatingRoadmap, setGeneratingRoadmap] = useState(false);

  useEffect(() => {
    async function fetchMatch() {
      if (!id) return;
      try {
        setLoading(true);
        const data = await api.getMatch(id);
        setMatch(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load match report.');
      } finally {
        setLoading(false);
      }
    }
    fetchMatch();
  }, [id]);

  const handleGenerateRoadmap = async () => {
    if (!match) return;
    setGeneratingRoadmap(true);
    try {
      const roadmap = await api.createRoadmap(match.id);
      navigate(`/roadmap/${roadmap.id}`);
    } catch (err: any) {
      alert(`Roadmap generation failed: ${err.message}`);
    } finally {
      setGeneratingRoadmap(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="h-8 w-8 border-3 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !match) {
    return (
      <div className="p-8 text-center glass-panel rounded-xl">
        <AlertCircle className="h-8 w-8 text-rose-400 mx-auto mb-2" />
        <p className="text-white font-semibold">Evaluation not found</p>
        <Link to="/matches" className="inline-block mt-4 text-xs text-indigo-400 font-medium">
          ← Back to Matches
        </Link>
      </div>
    );
  }

  // Radar chart data comparing components
  const radarData = [
    { metric: 'Weighted Coverage', score: match.weighted_coverage_score, fullMark: 100 },
    { metric: 'Skill Overlap', score: match.coverage_score, fullMark: 100 },
    { metric: 'Semantic Fit', score: match.semantic_score, fullMark: 100 },
    { metric: 'Overall Hybrid', score: match.overall_score, fullMark: 100 },
  ];

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/matches"
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Match Report: {match.job_title}
            </h2>
            <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5">
              <span>Resume: {match.resume_title}</span>
              <span>•</span>
              <span className="text-indigo-400">AI-Assisted Analysis</span>
              <span>•</span>
              <span>Evaluated {new Date(match.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <a
            href={api.getReportUrl(match.id)}
            target="_blank"
            rel="noreferrer"
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Export Printable Report</span>
          </a>

          <button
            onClick={handleGenerateRoadmap}
            disabled={generatingRoadmap}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/20 cursor-pointer"
          >
            <Compass className="h-3.5 w-3.5" />
            <span>{generatingRoadmap ? 'Formulating...' : 'Generate Learning Roadmap'}</span>
          </button>
        </div>
      </div>

      {api.isGuest() && (
        <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Sparkles className="h-5 w-5 text-indigo-400 shrink-0" />
            <p className="text-xs text-indigo-200">
              <strong>Guest Session:</strong> This match evaluation is saved in your current session. Sign up to permanently keep your results and track learning progress.
            </p>
          </div>
          <Link
            to="/register"
            className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shrink-0 transition-all"
          >
            Create Free Account
          </Link>
        </div>
      )}

      {/* Main Score Hero Card */}
      <div className="p-6 md:p-8 rounded-2xl bg-gradient-to-tr from-indigo-950/60 via-slate-900 to-slate-900 border border-indigo-500/25 grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
        <div className="md:col-span-2 space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-semibold">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Match Alignment Score</span>
          </div>

          <div className="flex items-baseline gap-4">
            <div className="text-5xl md:text-6xl font-black text-white tracking-tight">
              {match.overall_score.toFixed(1)}%
            </div>
            <div className="text-sm text-slate-300 font-medium">
              Overall Qualifications Fit
            </div>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed max-w-xl">
            {match.structured_explanation.summary}
          </p>

          <div className="pt-2 flex items-center gap-2 text-[11px] text-slate-400">
            <Info className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
            <span>
              Skill match scores are advisory indicators designed to guide skill growth, not a hiring guarantee.
            </span>
          </div>
        </div>

        {/* Mini Radar Chart */}
        <div className="h-[200px] w-full flex items-center justify-center">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis dataKey="metric" stroke="#94a3b8" fontSize={10} />
              <PolarRadiusAxis domain={[0, 100]} stroke="#475569" fontSize={8} />
              <Radar name="Alignment" dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.4} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Component Breakdown Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Core Requirements */}
        <div className="glass-card p-5 rounded-xl">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-400 mb-2">
            <span>Primary Weight</span>
            <span className="text-emerald-400 font-bold">{match.weighted_coverage_score}%</span>
          </div>
          <h4 className="text-sm font-bold text-white">Core Requirements Fit</h4>
          <p className="text-xs text-slate-400 mt-1">
            Evaluates required must-have skills versus preferred qualifications, recognizing related expertise.
          </p>
        </div>

        {/* Skill Overlap */}
        <div className="glass-card p-5 rounded-xl">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-400 mb-2">
            <span>Skill Match</span>
            <span className="text-violet-400 font-bold">{match.coverage_score}%</span>
          </div>
          <h4 className="text-sm font-bold text-white">Skill Overlap</h4>
          <p className="text-xs text-slate-400 mt-1">
            Direct overlap between technical skills identified on your resume and skills requested in the job description.
          </p>
        </div>

        {/* Contextual Fit */}
        <div className="glass-card p-5 rounded-xl">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-400 mb-2">
            <span>Context Fit</span>
            <span className="text-indigo-400 font-bold">{match.semantic_score}%</span>
          </div>
          <h4 className="text-sm font-bold text-white">Contextual Background Fit</h4>
          <p className="text-xs text-slate-400 mt-1">
            Measures how well your experience descriptions and project context align with the responsibilities in the role.
          </p>
        </div>
      </div>

      {/* Categorized Skills Breakdown */}
      <div className="space-y-6">
        {/* Matched Skills */}
        <div className="glass-panel p-6 rounded-xl space-y-4">
          <h3 className="text-base font-semibold text-emerald-400 flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5" />
            <span>Evidenced Skills ({match.matched_skills.length})</span>
          </h3>

          {match.matched_skills.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No direct matching skills evidenced.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {match.matched_skills.map((item) => (
                <div key={item.id} className="p-3.5 rounded-lg bg-emerald-950/20 border border-emerald-500/20">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white">{item.skill_name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-semibold">
                      Match: 1.0x
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 mt-2 font-mono bg-slate-950/50 p-2 rounded">
                    {item.supporting_evidence}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Related Skills */}
        <div className="glass-panel p-6 rounded-xl space-y-4">
          <h3 className="text-base font-semibold text-violet-400 flex items-center gap-2">
            <Layers className="h-5 w-5" />
            <span>Related & Adjacent Skills ({match.related_skills.length})</span>
          </h3>

          {match.related_skills.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No adjacent skills identified.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {match.related_skills.map((item) => (
                <div key={item.id} className="p-3.5 rounded-lg bg-violet-950/20 border border-violet-500/20">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white">{item.skill_name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-violet-500/10 text-violet-400 font-semibold">
                      Partial Credit: {item.match_value}x
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 mt-2 font-mono bg-slate-950/50 p-2 rounded">
                    {item.supporting_evidence}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Missing Skills */}
        <div className="glass-panel p-6 rounded-xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-rose-400 flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              <span>Skill Gaps ({match.missing_skills.length})</span>
            </h3>
            <span className="text-xs text-slate-400 italic">
              Means no supporting evidence was found in the analyzed document text
            </span>
          </div>

          {match.missing_skills.length === 0 ? (
            <p className="text-xs text-slate-500 italic">Zero skill gaps! Full requirement alignment.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {match.missing_skills.map((item) => (
                <div key={item.id} className="p-3.5 rounded-lg bg-rose-950/20 border border-rose-500/20">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white">{item.skill_name}</span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                        item.is_mandatory
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      }`}
                    >
                      {item.is_mandatory ? 'Mandatory Requirement' : 'Preferred'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-2">
                    {item.supporting_evidence}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
