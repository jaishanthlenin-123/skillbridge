import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Compass, ArrowLeft, CheckCircle2, Circle, ExternalLink,
  BookOpen, Code2, Clock, AlertCircle, Sparkles
} from 'lucide-react';
import { api } from '../../services/api';
import type { RoadmapDetail, RoadmapItem } from '../../types';

export const RoadmapDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [roadmap, setRoadmap] = useState<RoadmapDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchRoadmap() {
      try {
        setLoading(true);
        let targetId = id;
        
        // If route is /roadmap/latest, find the user's most recent roadmap
        if (id === 'latest') {
          const list = await api.getRoadmaps();
          if (list.length > 0) {
            targetId = list[0].id;
          } else {
            setLoading(false);
            return;
          }
        }

        if (targetId) {
          const data = await api.getRoadmap(targetId);
          setRoadmap(data);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load roadmap.');
      } finally {
        setLoading(false);
      }
    }
    fetchRoadmap();
  }, [id]);

  const handleToggle = async (itemId: string, currentStatus: boolean) => {
    if (!roadmap) return;
    try {
      const updatedItem = await api.toggleRoadmapItem(roadmap.id, itemId, !currentStatus);
      setRoadmap((prev) => {
        if (!prev) return null;
        const newItems = prev.items.map((it) => (it.id === itemId ? updatedItem : it));
        const completedCount = newItems.filter((i) => i.is_completed).length;
        return {
          ...prev,
          items: newItems,
          completed_items_count: completedCount,
        };
      });
    } catch (err: any) {
      alert(`Toggle failed: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="h-8 w-8 border-3 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !roadmap) {
    return (
      <div className="p-8 text-center glass-panel rounded-xl">
        <Compass className="h-10 w-10 text-slate-600 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-white">No active learning roadmap</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
          Roadmaps are generated from match analyses to guide you in closing critical skill gaps with verified resources.
        </p>
        <Link
          to="/matches"
          className="inline-block mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold"
        >
          Go to Matches
        </Link>
      </div>
    );
  }

  const completionPercent = Math.round((roadmap.completed_items_count / Math.max(1, roadmap.total_items_count)) * 100);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/matches"
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">{roadmap.title}</h2>
            <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5">
              <span>Target Role: {roadmap.target_role}</span>
              <span>•</span>
              <span className="text-indigo-400 font-medium">Match Baseline: {roadmap.match_score}%</span>
              <span>•</span>
              <span>Updated {new Date(roadmap.updated_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        <Link
          to={`/matches/${roadmap.match}`}
          className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-2"
        >
          <span>View Source Match</span>
        </Link>
      </div>

      {api.isGuest() && (
        <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Sparkles className="h-5 w-5 text-indigo-400 shrink-0" />
            <p className="text-xs text-indigo-200">
              <strong>Guest Session:</strong> This learning roadmap is active in your current session. Register to sync your roadmap progress across all your devices.
            </p>
          </div>
          <Link
            to="/register"
            className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shrink-0 transition-all"
          >
            Save Progress
          </Link>
        </div>
      )}

      {/* Progress Hero */}
      <div className="glass-panel p-6 rounded-2xl border border-indigo-500/20 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">
              Curriculum Progress
            </span>
            <h3 className="text-lg font-bold text-white mt-0.5">
              {roadmap.completed_items_count} of {roadmap.total_items_count} Skill Gaps Evidenced
            </h3>
          </div>
          <div className="text-2xl font-black text-indigo-400 font-mono">
            {completionPercent}%
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
          <div
            className="bg-indigo-600 h-2.5 rounded-full transition-all duration-500"
            style={{ width: `${completionPercent}%` }}
          />
        </div>
      </div>

      {/* Roadmap Items List */}
      <div className="space-y-4">
        {roadmap.items.map((item, index) => (
          <div
            key={item.id}
            className={`glass-panel p-6 rounded-2xl transition-all border ${
              item.is_completed ? 'border-emerald-500/30 bg-emerald-950/10' : 'border-slate-800'
            }`}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3.5">
                <button
                  onClick={() => handleToggle(item.id, item.is_completed)}
                  className={`mt-0.5 transition-colors ${
                    item.is_completed ? 'text-emerald-400' : 'text-slate-500 hover:text-slate-300'
                  }`}
                  title={item.is_completed ? 'Mark as Incomplete' : 'Mark as Completed'}
                >
                  {item.is_completed ? (
                    <CheckCircle2 className="h-6 w-6" />
                  ) : (
                    <Circle className="h-6 w-6" />
                  )}
                </button>

                <div>
                  <div className="flex items-center gap-3">
                    <h4
                      className={`text-base font-bold ${
                        item.is_completed ? 'line-through text-slate-400' : 'text-white'
                      }`}
                    >
                      {item.skill_name}
                    </h4>

                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                        item.priority === 'HIGH'
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          : item.priority === 'MEDIUM'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : 'bg-slate-700 text-slate-300'
                      }`}
                    >
                      {item.priority_display}
                    </span>

                    <span className="text-xs text-slate-500 flex items-center gap-1">
                      <Clock className="h-3 w-3" /> ~{item.estimated_weeks} weeks
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                    {item.rationale}
                  </p>
                </div>
              </div>
            </div>

            {/* Suggested Project & Resources */}
            <div className="mt-5 pt-4 border-t border-slate-800/80 grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Practical Project */}
              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5 mb-1.5">
                  <Code2 className="h-3.5 w-3.5" />
                  <span>Suggested Practical Portfolio Project</span>
                </span>
                <p className="text-xs text-slate-300 leading-relaxed font-mono">
                  {item.suggested_project}
                </p>
              </div>

              {/* Curated Verified Links */}
              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-[11px] font-bold uppercase tracking-wider text-violet-400 flex items-center gap-1.5 mb-1.5">
                  <BookOpen className="h-3.5 w-3.5" />
                  <span>Verified Learning Resources</span>
                </span>
                <div className="space-y-1.5">
                  {item.resources.map((res, i) => (
                    <a
                      key={i}
                      href={res.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1.5 truncate"
                    >
                      <ExternalLink className="h-3 w-3 shrink-0" />
                      <span className="truncate">{res.title} ({res.type})</span>
                    </a>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
