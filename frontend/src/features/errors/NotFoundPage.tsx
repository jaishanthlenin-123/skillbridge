import React from 'react';
import { Link } from 'react-router-dom';
import { Compass, Home, Briefcase, HelpCircle, Bot } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  const handleOpenAssistant = () => {
    // Dispatches a custom event or triggers chat button
    const launcher = document.querySelector('button[aria-label="Open AI Assistant"]') as HTMLButtonElement | null;
    if (launcher) {
      launcher.click();
    }
  };

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center px-4 py-12">
      <div className="h-20 w-20 rounded-3xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-6 shadow-xl shadow-indigo-500/10">
        <Compass className="h-10 w-10 animate-spin-slow" />
      </div>

      <div className="text-xs uppercase font-bold tracking-widest text-indigo-400 mb-2">
        Error 404 — Page Not Found
      </div>
      <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-3">
        Lost in the Talent Matrix?
      </h1>
      <p className="text-slate-400 text-sm max-w-md mx-auto mb-8">
        The page or resource you are looking for does not exist, has been removed, or was relocated.
      </p>

      {/* Recovery Actions */}
      <div className="flex flex-wrap items-center justify-center gap-3">
        <Link
          to="/dashboard"
          className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
        >
          <Home className="h-4 w-4" />
          <span>Return to Dashboard</span>
        </Link>

        <Link
          to="/jobs"
          className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer"
        >
          <Briefcase className="h-4 w-4" />
          <span>Explore Job Library</span>
        </Link>

        <Link
          to="/faq"
          className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer"
        >
          <HelpCircle className="h-4 w-4" />
          <span>Browse FAQs</span>
        </Link>

        <button
          onClick={handleOpenAssistant}
          className="px-4 py-2.5 rounded-xl bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/30 text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer"
        >
          <Bot className="h-4 w-4" />
          <span>Ask the Assistant</span>
        </button>
      </div>
    </div>
  );
};
