import React from 'react';
import { useLocation } from 'react-router-dom';
import { ShieldCheck, Sparkles, Cpu } from 'lucide-react';

export const Navbar: React.FC = () => {
  const location = useLocation();

  const getPageTitle = (path: string) => {
    if (path.startsWith('/dashboard')) return 'Platform Overview';
    if (path.startsWith('/resumes')) return 'Resume Workspace & Skill Extraction';
    if (path.startsWith('/jobs')) return 'Job Description Library';
    if (path.startsWith('/matches')) return 'Explainable Resume-to-Job Matching';
    if (path.startsWith('/roadmap')) return 'Personalized Learning Roadmap';
    if (path.startsWith('/history')) return 'Audit Trail & Privacy History';
    if (path.startsWith('/settings')) return 'Account & Data Retention Settings';
    return 'SkillBridge';
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-30">
      <div>
        <h1 className="text-base font-semibold text-white tracking-tight">
          {getPageTitle(location.pathname)}
        </h1>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>Private Document Sandbox</span>
        </div>

        <div className="hidden md:flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-medium">
          <Cpu className="h-3.5 w-3.5" />
          <span>MiniLM-L6 Hybrid Inference</span>
        </div>
      </div>
    </header>
  );
};
