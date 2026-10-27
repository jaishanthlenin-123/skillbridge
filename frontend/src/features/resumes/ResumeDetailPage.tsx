import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, FileText, CheckCircle2, AlertTriangle,
  Plus, X, Save, Sparkles, BookOpen, Clock, Tag
} from 'lucide-react';
import { api } from '../../services/api';
import type { ResumeDetail } from '../../types';

export const ResumeDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [resume, setResume] = useState<ResumeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Skill editing state
  const [skillsList, setSkillsList] = useState<string[]>([]);
  const [newSkillInput, setNewSkillInput] = useState('');
  const [savingSkills, setSavingSkills] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    async function fetchDetail() {
      if (!id) return;
      try {
        setLoading(true);
        const data = await api.getResume(id);
        setResume(data);
        setSkillsList((data.skills || []).map((s) => s.skill_name));
      } catch (err: any) {
        setError(err.message || 'Failed to load resume details.');
      } finally {
        setLoading(false);
      }
    }
    fetchDetail();
  }, [id]);

  const handleAddSkill = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = newSkillInput.trim();
    if (clean && !skillsList.some((s) => s.toLowerCase() === clean.toLowerCase())) {
      setSkillsList([...skillsList, clean]);
      setNewSkillInput('');
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    setSkillsList(skillsList.filter((s) => s !== skillToRemove));
  };

  const handleSaveSkills = async () => {
    if (!id) return;
    setSavingSkills(true);
    setSaveSuccess(false);
    try {
      const updated = await api.updateResumeSkills(id, skillsList);
      setResume(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert(`Failed to save skills: ${err.message}`);
    } finally {
      setSavingSkills(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="h-8 w-8 border-3 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !resume) {
    return (
      <div className="p-8 text-center glass-panel rounded-xl">
        <AlertTriangle className="h-8 w-8 text-rose-400 mx-auto mb-2" />
        <p className="text-white font-semibold">Unable to load resume</p>
        <p className="text-xs text-slate-400 mt-1">{error}</p>
        <Link to="/resumes" className="inline-block mt-4 text-xs text-indigo-400 hover:text-indigo-300 font-medium">
          ← Back to Resumes
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            to="/resumes"
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">{resume.title}</h2>
            <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5">
              <span>{resume.original_filename}</span>
              <span>•</span>
              <span className="text-emerald-400 font-medium">{resume.parsing_status_display}</span>
              <span>•</span>
              <span>Uploaded {new Date(resume.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        <Link
          to={`/matches?resume_id=${resume.id}`}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/20"
        >
          <Sparkles className="h-3.5 w-3.5" />
          <span>Match with a Job</span>
        </Link>
      </div>

      {/* Scanned PDF warning alert */}
      {resume.parsing_status === 'FAILED' && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-sm flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5 text-amber-400" />
          <div>
            <p className="font-semibold">Text Extraction Warning</p>
            <p className="text-xs text-amber-200/80 mt-0.5">{resume.error_details}</p>
          </div>
        </div>
      )}

      {/* Skills Review & Editing Card */}
      <div className="glass-panel p-6 rounded-xl space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Tag className="h-4 w-4 text-indigo-400" />
              <span>Extracted Technical Skills & Candidate Review</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Review skills extracted by our NLP engine. You can add missing skills or remove false positives.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {saveSuccess && (
              <span className="text-xs text-emerald-400 flex items-center gap-1 font-medium">
                <CheckCircle2 className="h-3.5 w-3.5" /> Changes Saved
              </span>
            )}
            <button
              onClick={handleSaveSkills}
              disabled={savingSkills}
              className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-indigo-600/20 cursor-pointer"
            >
              <Save className="h-3.5 w-3.5" />
              <span>{savingSkills ? 'Saving...' : 'Save Skills'}</span>
            </button>
          </div>
        </div>

        {/* Add Skill Form */}
        <form onSubmit={handleAddSkill} className="flex gap-2 max-w-md">
          <input
            type="text"
            value={newSkillInput}
            onChange={(e) => setNewSkillInput(e.target.value)}
            placeholder="Add a skill (e.g. PyTorch, Docker, Kubernetes)..."
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-medium flex items-center gap-1"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Add</span>
          </button>
        </form>

        {/* Skill Tags */}
        <div className="flex flex-wrap gap-2 pt-2">
          {skillsList.map((skillName) => {
            const occurrence = (resume.skills || []).find((s) => s.skill_name === skillName);
            return (
              <div
                key={skillName}
                title={occurrence?.evidence_text ? `Evidence: ${occurrence.evidence_text}` : undefined}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-medium group hover:border-indigo-500"
              >
                <span>{skillName}</span>
                <button
                  onClick={() => handleRemoveSkill(skillName)}
                  className="text-slate-500 hover:text-rose-400 p-0.5 rounded transition-colors"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Extracted Sections Preview */}
      <div className="glass-panel p-6 rounded-xl space-y-5">
        <h3 className="text-base font-semibold text-white flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-violet-400" />
          <span>Parsed Document Sections ({(resume.sections || []).length})</span>
        </h3>

        {(resume.sections || []).length === 0 ? (
          <p className="text-xs text-slate-500 italic py-4">No sections segmented.</p>
        ) : (
          <div className="space-y-4">
            {resume.sections.map((section) => (
              <div key={section.id} className="p-4 rounded-lg bg-slate-900/60 border border-slate-800/80">
                <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-400 block mb-2">
                  {section.section_type_display}
                </span>
                <p className="text-xs text-slate-300 whitespace-pre-line leading-relaxed font-mono">
                  {section.content}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
