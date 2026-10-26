import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText, Briefcase, GitCompare, Compass,
  ArrowUpRight, Plus, Sparkles, AlertCircle, CheckCircle2, ChevronRight
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, RadarChart, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import { api } from '../../services/api';
import type { ResumeListItem, JobListItem, MatchListItem, RoadmapListItem } from '../../types';

export const DashboardPage: React.FC = () => {
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [matches, setMatches] = useState<MatchListItem[]>([]);
  const [roadmaps, setRoadmaps] = useState<RoadmapListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [resumesData, jobsData, matchesData, roadmapsData] = await Promise.all([
          api.getResumes(),
          api.getJobs(),
          api.getMatches(),
          api.getRoadmaps(),
        ]);
        setResumes(resumesData);
        setJobs(jobsData);
        setMatches(matchesData);
        setRoadmaps(roadmapsData);
      } catch (err: any) {
        setError(err.message || 'Failed to load dashboard metrics.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 border-3 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
          <p className="text-sm text-slate-400">Loading your profile intelligence...</p>
        </div>
      </div>
    );
  }

  // Prepare chart data from recent matches
  const matchChartData = matches.slice(0, 5).map((m) => ({
    name: m.job_title.length > 15 ? `${m.job_title.substring(0, 15)}...` : m.job_title,
    overall: m.overall_score,
    weighted: m.weighted_coverage_score,
    coverage: m.coverage_score,
    semantic: m.semantic_score,
  }));

  const stats = [
    { label: 'Active Resumes', count: resumes.length, link: '/resumes', icon: FileText, color: 'text-indigo-400' },
    { label: 'Saved Jobs', count: jobs.length, link: '/jobs', icon: Briefcase, color: 'text-violet-400' },
    { label: 'Match Evaluations', count: matches.length, link: '/matches', icon: GitCompare, color: 'text-emerald-400' },
    { label: 'Active Roadmaps', count: roadmaps.length, link: '/roadmap/latest', icon: Compass, color: 'text-amber-400' },
  ];

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="p-6 md:p-8 rounded-2xl bg-gradient-to-r from-indigo-950/60 via-slate-900 to-slate-900 border border-indigo-500/20 relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-xs font-semibold mb-3">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Hybrid Match Engine v1.0 Ready</span>
          </div>
          <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
            Resume Intelligence Workspace
          </h2>
          <p className="text-slate-300 text-sm mt-2 leading-relaxed">
            Upload candidate resumes, evaluate against job descriptions using explainable multi-component NLP,
            and view prioritized skill roadmaps with verified learning resources.
          </p>
          <div className="flex flex-wrap gap-3 mt-5">
            <Link
              to="/resumes"
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/25 transition-all"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Upload Resume</span>
            </Link>
            <Link
              to="/jobs"
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all"
            >
              <Briefcase className="h-3.5 w-3.5" />
              <span>Add Job Description</span>
            </Link>
            <Link
              to="/matches"
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all"
            >
              <GitCompare className="h-3.5 w-3.5" />
              <span>Run Match</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Link
              key={stat.label}
              to={stat.link}
              className="glass-card p-5 rounded-xl block group"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">{stat.label}</span>
                <Icon className={`h-4 w-4 ${stat.color}`} />
              </div>
              <div className="text-2xl font-bold text-white mt-2 flex items-baseline justify-between">
                <span>{stat.count}</span>
                <ArrowUpRight className="h-4 w-4 text-slate-600 group-hover:text-indigo-400 transition-colors" />
              </div>
            </Link>
          );
        })}
      </div>

      {/* Main Grid: Match Analytics Chart & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Real Match Analytics */}
        <div className="lg:col-span-2 glass-panel rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-semibold text-white">Recent Match Scores Overview</h3>
              <p className="text-xs text-slate-400">Comparing hybrid scores across evaluated positions</p>
            </div>
            {matches.length > 0 && (
              <span className="text-xs px-2.5 py-1 rounded bg-slate-800 text-indigo-400 font-mono">
                Latest: {matches[0].overall_score}%
              </span>
            )}
          </div>

          {matches.length === 0 ? (
            <div className="min-h-[240px] flex flex-col items-center justify-center text-center p-6 border border-dashed border-slate-800 rounded-lg">
              <GitCompare className="h-8 w-8 text-slate-600 mb-2" />
              <p className="text-sm font-medium text-slate-300">No match evaluations yet</p>
              <p className="text-xs text-slate-500 max-w-sm mt-1">
                Upload your resume and paste a job description to see explainable scores and component breakdowns here.
              </p>
              <Link
                to="/matches"
                className="mt-4 px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-xs font-medium"
              >
                Create First Match
              </Link>
            </div>
          ) : (
            <div className="h-[260px] w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={matchChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    labelStyle={{ color: '#fff', fontWeight: 600 }}
                  />
                  <Bar dataKey="overall" name="Overall Hybrid" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="weighted" name="Requirement Weighted" fill="#10b981" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="coverage" name="Skill Overlap" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Right Col: Recent Matches List */}
        <div className="glass-panel rounded-xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold text-white">Recent Analyses</h3>
              <Link to="/matches" className="text-xs text-indigo-400 hover:text-indigo-300 font-medium">
                View All
              </Link>
            </div>

            {matches.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-8 text-center">No evaluations performed yet.</p>
            ) : (
              <div className="space-y-3">
                {matches.slice(0, 4).map((m) => (
                  <Link
                    key={m.id}
                    to={`/matches/${m.id}`}
                    className="p-3 rounded-lg bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800/80 flex items-center justify-between transition-colors block"
                  >
                    <div className="overflow-hidden pr-2">
                      <p className="text-xs font-semibold text-white truncate">{m.job_title}</p>
                      <p className="text-[11px] text-slate-400 truncate">{m.resume_title}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="inline-block text-xs font-bold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400">
                        {m.overall_score}%
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800/80">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Database Persistence</span>
              <span className="text-emerald-400 font-medium flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" /> Online
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
