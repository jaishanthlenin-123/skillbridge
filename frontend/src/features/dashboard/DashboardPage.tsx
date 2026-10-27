import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText, Briefcase, GitCompare, Compass,
  ArrowUpRight, Plus, Sparkles, CheckCircle2, ChevronRight,
  Target, BookOpen, Bot, ShieldCheck, ArrowRight
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer
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
  const token = localStorage.getItem('skillbridge_token');

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        if (token) {
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
        } else {
          // Guest Exploration: fetch available jobs list from database
          const jobsData = await api.getJobs();
          setJobs(jobsData);
          setResumes([]);
          setMatches([]);
          setRoadmaps([]);
        }
      } catch (err: any) {
        setError(err.message || 'Unable to load career data.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [token]);

  const handleOpenAssistant = () => {
    window.dispatchEvent(new CustomEvent('skillbridge:open-chat'));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 border-3 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
          <p className="text-sm text-slate-400">Loading your career dashboard...</p>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // GUEST PUBLIC LANDING PAGE
  // ---------------------------------------------------------------------------
  if (!token) {
    return (
      <div className="space-y-12 pb-8">
        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between">
            <span>{error}</span>
          </div>
        )}
        {/* Hero Section */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-indigo-950/40 via-slate-900/60 to-slate-950 border border-slate-800 p-8 sm:p-12 text-center lg:text-left flex flex-col lg:flex-row items-center justify-between gap-8">
          <div className="max-w-2xl space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold">
              <Sparkles className="h-3.5 w-3.5" />
              <span>SkillBridge Career Platform</span>
            </div>
            
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white tracking-tight leading-tight">
              Find Your Next <span className="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">Career Opportunity</span>
            </h1>
            
            <p className="text-base sm:text-lg text-slate-300 leading-relaxed max-w-xl">
              Explore jobs, understand your skill gaps, and build a personalized learning plan to move closer to your career goals.
            </p>

            <div className="pt-2 flex flex-wrap items-center justify-center lg:justify-start gap-3">
              <Link
                to="/resumes"
                className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2"
              >
                <FileText className="h-4 w-4" />
                <span>Upload Resume</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                to="/jobs"
                className="px-5 py-3 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700/80 font-semibold text-sm transition-all flex items-center gap-2"
              >
                <Briefcase className="h-4 w-4 text-indigo-400" />
                <span>Explore Jobs</span>
              </Link>
              <button
                onClick={handleOpenAssistant}
                className="px-5 py-3 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700/80 font-semibold text-sm transition-all flex items-center gap-2 cursor-pointer"
              >
                <Bot className="h-4 w-4 text-violet-400" />
                <span>Try Career Assistant</span>
              </button>
            </div>
          </div>

          {/* Quick Platform Metrics card */}
          <div className="w-full lg:w-80 glass-panel p-6 rounded-2xl border border-slate-800 space-y-4 shrink-0 text-left">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Platform Overview</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
                <span className="text-xs text-slate-300">Available Jobs in Library</span>
                <span className="text-sm font-bold text-white">{jobs.length}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
                <span className="text-xs text-slate-300">Supported Resume Formats</span>
                <span className="text-xs font-semibold text-indigo-400">PDF, DOCX</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
                <span className="text-xs text-slate-300">Instant Guest Exploration</span>
                <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1">
                  <ShieldCheck className="h-3.5 w-3.5" /> No Account Required
                </span>
              </div>
            </div>
            <div className="pt-2 text-center">
              <Link to="/login" className="text-xs text-indigo-400 hover:text-indigo-300 font-medium">
                Already have an account? Sign in &rarr;
              </Link>
            </div>
          </div>
        </div>

        {/* 4 Core Value Cards */}
        <div className="space-y-4">
          <div className="text-center max-w-xl mx-auto">
            <h2 className="text-xl font-bold text-white">Everything You Need to Advance Your Career</h2>
            <p className="text-xs text-slate-400 mt-1">Guided tools to evaluate qualifications and acquire in-demand skills.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* 1. Discover Jobs */}
            <div className="glass-card p-6 rounded-2xl flex flex-col justify-between hover:border-indigo-500/40 transition-all">
              <div className="space-y-3">
                <div className="h-10 w-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
                  <Briefcase className="h-5 w-5" />
                </div>
                <h3 className="text-base font-semibold text-white">Discover Jobs</h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Browse open positions or paste custom job descriptions to review required qualifications and tech stacks.
                </p>
              </div>
              <Link to="/jobs" className="mt-5 inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-400 hover:text-indigo-300">
                Explore positions <ArrowRight className="h-3 w-3" />
              </Link>
            </div>

            {/* 2. Analyze Your Skills */}
            <div className="glass-card p-6 rounded-2xl flex flex-col justify-between hover:border-violet-500/40 transition-all">
              <div className="space-y-3">
                <div className="h-10 w-10 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400 flex items-center justify-center">
                  <Target className="h-5 w-5" />
                </div>
                <h3 className="text-base font-semibold text-white">Analyze Your Skills</h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Compare your resume against any role to see matching strengths, related qualifications, and skill gaps.
                </p>
              </div>
              <Link to="/matches" className="mt-5 inline-flex items-center gap-1.5 text-xs font-semibold text-violet-400 hover:text-violet-300">
                Analyze your resume <ArrowRight className="h-3 w-3" />
              </Link>
            </div>

            {/* 3. Build a Learning Roadmap */}
            <div className="glass-card p-6 rounded-2xl flex flex-col justify-between hover:border-emerald-500/40 transition-all">
              <div className="space-y-3">
                <div className="h-10 w-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
                  <BookOpen className="h-5 w-5" />
                </div>
                <h3 className="text-base font-semibold text-white">Build a Learning Roadmap</h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Turn missing skills into an organized, step-by-step learning roadmap with curated courses, documentation, and practice guides.
                </p>
              </div>
              <Link to="/matches" className="mt-5 inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-400 hover:text-emerald-300">
                Explore roadmaps <ArrowRight className="h-3 w-3" />
              </Link>
            </div>

            {/* 4. Get Career Guidance */}
            <div className="glass-card p-6 rounded-2xl flex flex-col justify-between hover:border-amber-500/40 transition-all">
              <div className="space-y-3">
                <div className="h-10 w-10 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center">
                  <Bot className="h-5 w-5" />
                </div>
                <h3 className="text-base font-semibold text-white">Get Career Guidance</h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Chat with the integrated Career Assistant for instant answers on role requirements, resume improvements, and career planning.
                </p>
              </div>
              <button
                onClick={handleOpenAssistant}
                className="mt-5 inline-flex items-center gap-1.5 text-xs font-semibold text-amber-400 hover:text-amber-300 text-left cursor-pointer"
              >
                Ask assistant <ArrowRight className="h-3 w-3" />
              </button>
            </div>
          </div>
        </div>

        {/* Featured Sample Positions from Database */}
        {jobs.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-white">Featured Career Paths</h2>
                <p className="text-xs text-slate-400">Available positions you can explore and analyze right now.</p>
              </div>
              <Link to="/jobs" className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1">
                View all jobs <ChevronRight className="h-3 w-3" />
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {jobs.slice(0, 3).map((job) => (
                <div key={job.id} className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3 flex flex-col justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-white">{job.title}</h3>
                    <p className="text-xs text-slate-400 mt-0.5">{job.company_name || job.company || 'Technology Organization'}</p>
                    <p className="text-xs text-slate-300 line-clamp-2 mt-2 leading-relaxed">
                      {job.description || 'Full-time technical role with comprehensive skill requirements and growth milestones.'}
                    </p>
                  </div>
                  <div className="pt-2 flex items-center justify-between border-t border-slate-800/80">
                    <span className="text-[11px] text-slate-400">{job.location || 'Remote / Hybrid'}</span>
                    <Link
                      to="/jobs"
                      className="text-xs font-semibold text-indigo-400 hover:text-indigo-300"
                    >
                      View Details &rarr;
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // AUTHENTICATED USER DASHBOARD
  // ---------------------------------------------------------------------------
  const userStats = [
    { label: 'Available Jobs', count: jobs.length, link: '/jobs', icon: Briefcase, color: 'text-violet-400' },
    { label: 'Your Resumes', count: resumes.length, link: '/resumes', icon: FileText, color: 'text-indigo-400' },
    { label: 'Skill Match Results', count: matches.length, link: '/matches', icon: GitCompare, color: 'text-emerald-400' },
    { label: 'Learning Roadmaps', count: roadmaps.length, link: '/roadmap/latest', icon: Compass, color: 'text-amber-400' },
  ];

  // User-facing chart data
  const matchChartData = matches.slice(0, 5).map((m) => ({
    name: m.job_title.length > 14 ? `${m.job_title.substring(0, 14)}...` : m.job_title,
    overall: m.overall_score,
    qualifications: m.weighted_coverage_score,
    skills: m.coverage_score,
  }));

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="p-6 md:p-8 rounded-2xl bg-gradient-to-r from-indigo-950/50 via-slate-900 to-slate-900 border border-slate-800 relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold mb-3">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Career Development Workspace</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
            Welcome back to SkillBridge
          </h1>
          <p className="text-slate-300 text-sm mt-2 leading-relaxed">
            Manage your resumes, evaluate qualification fit against target jobs, and follow your prioritized learning roadmap.
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
              to="/matches"
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all"
            >
              <GitCompare className="h-3.5 w-3.5 text-indigo-400" />
              <span>New Skill Match</span>
            </Link>
            <Link
              to="/jobs"
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all"
            >
              <Briefcase className="h-3.5 w-3.5 text-slate-400" />
              <span>Explore Jobs</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Meaningful User Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {userStats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Link
              key={stat.label}
              to={stat.link}
              className="glass-card p-5 rounded-xl block group hover:border-indigo-500/40 transition-all"
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

      {/* Main Grid: Match Score Analytics & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Match Strength Overview */}
        <div className="lg:col-span-2 glass-panel rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-white">Skill Match Overview</h2>
              <p className="text-xs text-slate-400">Comparing your resume alignment across evaluated positions</p>
            </div>
            {matches.length > 0 && (
              <span className="text-xs px-2.5 py-1 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-semibold">
                Latest Match: {matches[0].overall_score}%
              </span>
            )}
          </div>

          {matches.length === 0 ? (
            <div className="min-h-[240px] flex flex-col items-center justify-center text-center p-6 border border-dashed border-slate-800 rounded-xl">
              <GitCompare className="h-8 w-8 text-slate-600 mb-2" />
              <p className="text-sm font-medium text-slate-300">No skill matches yet</p>
              <p className="text-xs text-slate-500 max-w-sm mt-1">
                Upload your resume and select a job description to see your qualification match and skill gap breakdown.
              </p>
              <Link
                to="/matches"
                className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold"
              >
                Analyze First Job Match
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
                  <Bar dataKey="overall" name="Overall Match %" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="qualifications" name="Core Qualifications %" fill="#10b981" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="skills" name="Skill Overlap %" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Right Col: Recent Analyses List */}
        <div className="glass-panel rounded-xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-white">Recent Analyses</h2>
              <Link to="/matches" className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold">
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
              <span>Career Profile</span>
              <span className="text-emerald-400 font-medium flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" /> Active
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
